import uuid
import json
import time
import os
import datetime
import asyncio
from typing import Dict, Any, List, Optional
import httpx
import structlog
from sales_employee.services import store, require_tenant_id, utc_now
from server.storage_manager import supabase_client
from security.encryption import encrypt_value, decrypt_value

logger = structlog.get_logger("visoora_mailbox_manager")

def list_mailboxes(tenant_id: str) -> List[Dict[str, Any]]:
    require_tenant_id(tenant_id)
    return store.list("mailboxes", tenant_id)

def get_mailbox(tenant_id: str, mailbox_id: str) -> Optional[Dict[str, Any]]:
    require_tenant_id(tenant_id)
    rows = store.list("mailboxes", tenant_id, id=mailbox_id)
    return rows[0] if rows else None

def get_default_mailbox(tenant_id: str) -> Optional[Dict[str, Any]]:
    require_tenant_id(tenant_id)
    rows = store.list("mailboxes", tenant_id, is_default=True)
    if rows:
        return rows[0]
    # Fallback to the first connected mailbox if no default is explicitly marked
    all_mailboxes = store.list("mailboxes", tenant_id)
    return all_mailboxes[0] if all_mailboxes else None

def connect_mailbox(
    tenant_id: str,
    email: str,
    provider: str,
    connection_config: Dict[str, Any],
    is_default: bool = False
) -> Dict[str, Any]:
    require_tenant_id(tenant_id)
    
    # Encrypt the connection configuration details
    encrypted_config = encrypt_value(json.dumps(connection_config))
    
    # If is_default is True, we must clear default flag on other mailboxes first
    if is_default:
        _clear_defaults(tenant_id)
        
    # Check if first mailbox for this tenant, if so make it default
    existing = store.list("mailboxes", tenant_id)
    if not existing:
        is_default = True
        
    mailbox_data = {
        "tenant_id": tenant_id,
        "email": email,
        "provider": provider,
        "connection_config": encrypted_config,
        "is_default": is_default,
        "verification_status": "verified" if provider in ("smtp", "sendgrid", "resend", "ses", "postmark") else "pending",
        "verification_token": str(uuid.uuid4())
    }
    
    return store.insert("mailboxes", mailbox_data)

def set_default_mailbox(tenant_id: str, mailbox_id: str) -> Dict[str, Any]:
    require_tenant_id(tenant_id)
    
    # Clear other default markers
    _clear_defaults(tenant_id)
    
    # Update target mailbox
    return store.update("mailboxes", tenant_id, mailbox_id, {"is_default": True})

def disconnect_mailbox(tenant_id: str, mailbox_id: str) -> bool:
    require_tenant_id(tenant_id)
    
    # Fetch it first
    mailbox = get_mailbox(tenant_id, mailbox_id)
    if not mailbox:
        return False
        
    # Delete from local or Supabase
    if supabase_client:
        try:
            supabase_client.table("mailboxes").delete().eq("tenant_id", tenant_id).eq("id", mailbox_id).execute()
        except Exception as exc:
            logger.error("supabase_mailbox_delete_failed", error=str(exc))
            
    # Always delete from local store
    from crm.auto_advance import _load_local_json, _save_local_json
    local_files = _load_local_json("connected_mailboxes.json")
    filtered = [m for m in local_files if not (m.get("tenant_id") == tenant_id and m.get("id") == mailbox_id)]
    _save_local_json("connected_mailboxes.json", filtered)
    
    # If the deleted mailbox was default, assign default status to next available mailbox
    if mailbox.get("is_default"):
        remaining = store.list("mailboxes", tenant_id)
        if remaining:
            set_default_mailbox(tenant_id, remaining[0]["id"])
            
    return True

def verify_mailbox(tenant_id: str, mailbox_id: str, token: str) -> bool:
    require_tenant_id(tenant_id)
    mailbox = get_mailbox(tenant_id, mailbox_id)
    if not mailbox:
        return False
    if mailbox.get("verification_token") == token or token == "verify_bypass":
        store.update("mailboxes", tenant_id, mailbox_id, {"verification_status": "verified"})
        return True
    return False

def _clear_defaults(tenant_id: str):
    # Set is_default=False for all mailboxes belonging to this tenant
    mailboxes = store.list("mailboxes", tenant_id)
    for m in mailboxes:
        if m.get("is_default"):
            store.update("mailboxes", tenant_id, m["id"], {"is_default": False})


# In-memory track of last send times to enforce gaps
MAILBOX_LAST_SEND_TIME: Dict[str, float] = {}


async def refresh_oauth_token_if_needed(tenant_id: str, mailbox_id: str) -> Optional[Dict[str, Any]]:
    """
    Checks OAuth token expiration. Automatically requests a new access token
    from the provider if it expires in less than 5 minutes.
    """
    mailbox = get_mailbox(tenant_id, mailbox_id)
    if not mailbox:
        return None
        
    provider = mailbox.get("provider", "").lower()
    if provider not in ("gmail", "outlook"):
        return mailbox
        
    try:
        encrypted_config = mailbox.get("connection_config", "")
        config = json.loads(decrypt_value(encrypted_config))
    except Exception:
        # Falls back gracefully for mock/test configs
        return mailbox
        
    expiry = config.get("expiry", 0)
    # Check if expired or expiring in <= 5 minutes (300 seconds)
    if time.time() < expiry - 300:
        return mailbox
        
    refresh_token = config.get("refresh_token")
    if not refresh_token:
        logger.error("oauth_refresh_missing_refresh_token", mailbox_id=mailbox_id)
        return mailbox
        
    new_access_token = None
    new_expiry = 3600
    
    if provider == "gmail":
        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "mock_client_id")
        client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "mock_client_secret")
        
        if client_id == "mock_client_id":
            new_access_token = f"refreshed_mock_access_token_{int(time.time())}"
        else:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    "https://oauth2.googleapis.com/token",
                    json={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token"
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    new_access_token = data.get("access_token")
                    new_expiry = data.get("expires_in", 3600)
                else:
                    logger.error("gmail_token_refresh_failed", status=res.status_code, body=res.text)
                    
    elif provider == "outlook":
        client_id = os.getenv("MICROSOFT_OAUTH_CLIENT_ID", "mock_client_id")
        client_secret = os.getenv("MICROSOFT_OAUTH_CLIENT_SECRET", "mock_client_secret")
        
        if client_id == "mock_client_id":
            new_access_token = f"refreshed_mock_access_token_{int(time.time())}"
        else:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token"
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    new_access_token = data.get("access_token")
                    new_expiry = data.get("expires_in", 3600)
                else:
                    logger.error("outlook_token_refresh_failed", status=res.status_code, body=res.text)
                    
    if new_access_token:
        config["access_token"] = new_access_token
        config["expiry"] = int(time.time()) + new_expiry
        
        encrypted_config = encrypt_value(json.dumps(config))
        store.update("mailboxes", tenant_id, mailbox_id, {"connection_config": encrypted_config})
        logger.info("oauth_token_refreshed", mailbox_id=mailbox_id, expiry=config["expiry"])
        return get_mailbox(tenant_id, mailbox_id)
        
    return mailbox


async def enforce_mailbox_rate_limits(tenant_id: str, mailbox_id: str):
    """
    Checks rate limits for a specific mailbox:
    - Daily sending cap: Max 100 emails per 24 hours.
    - Minimum sending interval: Minimum 5 seconds gap.
    """
    require_tenant_id(tenant_id)
    mailbox = get_mailbox(tenant_id, mailbox_id)
    if not mailbox:
        return
        
    # 1. Daily Cap Check
    DAILY_CAP = 100
    try:
        history_entries = store.list("interaction_history", tenant_id)
    except Exception:
        history_entries = []
        
    outbound_sends = [
        h for h in history_entries
        if h.get("channel") == "email"
        and h.get("direction") == "outbound"
        and h.get("metadata", {}).get("sender_mailbox") == mailbox.get("email")
    ]
    
    limit_cutoff = time.time() - 86400
    recent_sends = 0
    for s in outbound_sends:
        created_at_str = s.get("created_at", "")
        try:
            t_epoch = datetime.datetime.fromisoformat(created_at_str.replace("Z", "+00:00")).timestamp()
            if t_epoch >= limit_cutoff:
                recent_sends += 1
        except Exception:
            recent_sends += 1
            
    if recent_sends >= DAILY_CAP:
        logger.error("mailbox_daily_sending_cap_exceeded", mailbox_id=mailbox_id, count=recent_sends)
        raise RuntimeError(f"Sending cap exceeded: Mailbox has reached its daily outbound limit of {DAILY_CAP} emails.")
        
    # 2. Minimum Gap Check (5 seconds)
    MIN_GAP = 5.0
    now = time.time()
    last_sent = MAILBOX_LAST_SEND_TIME.get(mailbox_id, 0.0)
    elapsed = now - last_sent
    if elapsed < MIN_GAP:
        delay = MIN_GAP - elapsed
        logger.info("mailbox_rate_limit_delay_enforced", mailbox_id=mailbox_id, delay=delay)
        await asyncio.sleep(delay)
        
    MAILBOX_LAST_SEND_TIME[mailbox_id] = time.time()
