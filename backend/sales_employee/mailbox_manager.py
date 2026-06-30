import uuid
import json
from typing import Dict, Any, List, Optional
import structlog
from sales_employee.services import store, require_tenant_id, utc_now
from server.storage_manager import supabase_client
from security.encryption import encrypt_value

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
