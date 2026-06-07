import os
import datetime
import json
import uuid
import httpx
from zoneinfo import ZoneInfo
from typing import Dict, Optional, Tuple, List, Any
import phonenumbers
from phonenumbers import timezone
from fastapi import APIRouter, Depends, Request, Response
from security.errors import SecurityException
from security.rbac import get_current_user, RoleChecker, UserPrincipal
from security.logging import logger
from server.storage_manager import supabase_client

# Define compliance router
compliance_router = APIRouter(prefix="/compliance", tags=["Compliance"])

# ----------------------------------------------------
# COMPLIANCE EXCEPTIONS DEFINITIONS
# ----------------------------------------------------
class ComplianceException(SecurityException):
    """Base exception for all TCPA/GDPR compliance gate violations."""
    def __init__(self, status_code: int, detail: str, reason: str, extra: Optional[dict] = None):
        super().__init__(
            status_code=status_code,
            detail=detail,
            title="Compliance Violation",
            error_type=f"https://visoora.com/errors/compliance/{reason.lower()}"
        )
        self.invalid_params = [{"reason": reason, "detail": detail, **(extra or {})}]

class DNCBlockedException(ComplianceException):
    """Raised when the target number is in the Do Not Call registry (TCPA/GDPR violation)."""
    def __init__(self, phone_number: str):
        super().__init__(
            status_code=403,
            detail=f"E.164 phone number '{phone_number}' is registered on the tenant's Do Not Call (DNC) list.",
            reason="DNC_BLOCKED"
        )

class OutsideCallingHoursException(ComplianceException):
    """Raised when target dialing local time falls outside 8:00 AM - 9:00 PM (TCPA violation)."""
    def __init__(self, phone_number: str, tz_name: str, current_time: str, next_window: str):
        super().__init__(
            status_code=403,
            detail=f"Call blocked. Target recipient timezone '{tz_name}' is outside standard calling hours (8 AM - 9 PM).",
            reason="OUTSIDE_CALLING_HOURS",
            extra={"timezone": tz_name, "current_local_time": current_time, "next_available_window": next_window}
        )

class ConsentRequiredException(ComplianceException):
    """Raised when valid consent token is missing, expired, or mismatched."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=403,
            detail=detail,
            reason="CONSENT_REQUIRED"
        )

# ----------------------------------------------------
# FILE-BASED THREAD-SAFE LOCAL FALLBACK REGISTRIES
# ----------------------------------------------------
LOCAL_DNC_FILE = "recordings/local_dnc.json"
LOCAL_CONSENT_FILE = "recordings/local_consents.json"
LOCAL_COMPLIANCE_SETTINGS_FILE = "recordings/local_tenant_compliance.json"

for f_path in [LOCAL_DNC_FILE, LOCAL_CONSENT_FILE]:
    if not os.path.exists(f_path):
        with open(f_path, "w") as f:
            json.dump([], f)

if not os.path.exists(LOCAL_COMPLIANCE_SETTINGS_FILE):
    with open(LOCAL_COMPLIANCE_SETTINGS_FILE, "w") as f:
        # Prepopulate default tenant settings
        json.dump({
            "default_shared_tenant": {
                "recording_disclosure_enabled": True,
                "recording_disclosure_text": "This call may be recorded for quality and training purposes.",
                "ai_disclosure_enabled": True,
                "ai_disclosure_text": "You are speaking with an automated assistant."
            }
        }, f, indent=2)

# ----------------------------------------------------
# TIMEZONE & CALLING WINDOW ENFORCEMENT
# ----------------------------------------------------
def get_calling_hours_status(phone_number: str) -> Tuple[bool, str, str, str]:
    """
    Infers recipient timezone name from E.164 phone area code using the 'phonenumbers' library.
    Checks if current local time at the target falls inside the TCPA-compliant 8:00 AM - 9:00 PM window.
    Returns: (is_allowed, timezone_name, current_local_time_str, next_window_iso_str)
    """
    try:
        # Standardize and parse number format
        parsed = phonenumbers.parse(phone_number, None)
        tzs = timezone.time_zones_for_number(parsed)
        
        # Fallback to America/New_York (Eastern Time) if timezone cannot be determined
        tz_name = "America/New_York"
        if tzs and tzs[0] != "Etc/Unknown":
            tz_name = tzs[0]
            
        tz = ZoneInfo(tz_name)
        now_in_tz = datetime.datetime.now(tz)
        current_hour = now_in_tz.hour
        
        is_allowed = 8 <= current_hour < 21  # 8:00 AM to 8:59 PM is allowed. 9:00 PM is blocked.
        
        # Calculate Next Available Calling Window
        if current_hour >= 21:
            # Tomorrow at 8:00 AM
            next_dt = (now_in_tz + datetime.timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
        elif current_hour < 8:
            # Today at 8:00 AM
            next_dt = now_in_tz.replace(hour=8, minute=0, second=0, microsecond=0)
        else:
            next_dt = now_in_tz # Currently allowed
            
        return is_allowed, tz_name, now_in_tz.strftime("%I:%M %p"), next_dt.isoformat()
        
    except Exception as e:
        logger.error("timezone_inference_error", message="Failed to parse timezone from phone.", phone=phone_number, error=str(e))
        # Cascades to true safely to avoid complete blocker on invalid numbers, default Eastern Time
        return True, "UTC", datetime.datetime.utcnow().strftime("%I:%M %p"), datetime.datetime.utcnow().isoformat()

# ----------------------------------------------------
# ACTIVE COMPLIANCE GATE MIDDLEWARE
# ----------------------------------------------------
async def verify_compliance_gate(phone_number: str, tenant_id: str, consent_token: Optional[str] = None):
    """
    Executes TCPA/GDPR zero-trust verification pipeline *before*Twilio dials the outbound PSTN leg.
    1. Tenant DNC registry verify.
    2. Recipient local calling hours timezone verify.
    3. Expiry-aware Consent Token verify (90 days).
    """
    logger.info("compliance_gate_start", message="Running compliance gate filters.", phone=phone_number, tenant_id=tenant_id)
    
    # ----------------------------------------------------
    # 0. SAAS BILLING USAGE LIMIT ENFORCEMENT
    # ----------------------------------------------------
    from billing.meter import check_calling_limit
    is_billing_cleared = await check_calling_limit(tenant_id)
    if not is_billing_cleared:
        raise ComplianceException(
            status_code=402,
            detail="Outbound call blocked. Tenant calling minutes limit depleted or billing is suspended. Please review your settings billing page.",
            reason="BILLING_SUSPENDED_NO_MINUTES"
        )
    
    # ----------------------------------------------------
    # 1. DO NOT CALL (DNC) REGISTRY CHECK (TCPA 47 U.S.C. § 227)
    # ----------------------------------------------------
    is_dnc = False
    if supabase_client:
        try:
            res = supabase_client.table("dnc_numbers").select("*").eq("phone_number", phone_number).eq("tenant_id", tenant_id).execute()
            if res.data:
                is_dnc = True
        except Exception as e:
            logger.error("dnc_supabase_error", message="Supabase DNC query failed. Checking local registry.", error=str(e))
            
    if not is_dnc:
        # Check Local fallback registry
        try:
            with open(LOCAL_DNC_FILE, "r") as f:
                dnc_list = json.load(f)
                is_dnc = any(item.get("phone_number") == phone_number and item.get("tenant_id") == tenant_id for item in dnc_list)
        except Exception as e:
            logger.error("dnc_local_read_error", message="Local DNC registry read failed.", error=str(e))

    if is_dnc:
        raise DNCBlockedException(phone_number)
        
    # ----------------------------------------------------
    # 2. TIME-WINDOW ENFORCEMENT CHECK (FCC calling hours limits)
    # ----------------------------------------------------
    allowed, tz_name, local_time_str, next_window = get_calling_hours_status(phone_number)
    if not allowed:
        raise OutsideCallingHoursException(phone_number, tz_name, local_time_str, next_window)

    # ----------------------------------------------------
    # 3. CONSENT VERIFICATION CHECK (GDPR Article 7 & TCPA PEWC)
    # ----------------------------------------------------
    if not consent_token:
        raise ConsentRequiredException("outbound call blocked: consent_token is missing.")
        
    # Validate UUID format
    try:
        uuid.UUID(consent_token)
    except ValueError:
        raise ConsentRequiredException("Invalid token format: consent_token must be a valid UUID.")
        
    is_consent_valid = False
    consent_detail = "Consent token was not found or mismatched."
    
    if supabase_client:
        try:
            res = supabase_client.table("call_consents").select("*").eq("consent_token", consent_token).execute()
            if res.data:
                consent_record = res.data[0]
                is_consent_valid, consent_detail = _verify_consent_record(consent_record, phone_number, tenant_id)
        except Exception as e:
            logger.error("consent_supabase_error", message="Supabase consent query failed.", error=str(e))
            
    if not is_consent_valid:
        # Check Local fallback registry
        try:
            with open(LOCAL_CONSENT_FILE, "r") as f:
                consent_list = json.load(f)
                records = [r for r in consent_list if r.get("consent_token") == consent_token]
                if records:
                    is_consent_valid, consent_detail = _verify_consent_record(records[0], phone_number, tenant_id)
        except Exception as e:
            logger.error("consent_local_read_error", message="Local consent registry read failed.", error=str(e))

    if not is_consent_valid:
        raise ConsentRequiredException(f"Consent validation failed: {consent_detail}")

    logger.info("compliance_gate_passed", message="Compliance checks passed successfully. Gate cleared.", phone=phone_number)
    return True

def _verify_consent_record(record: dict, phone_number: str, tenant_id: str) -> Tuple[bool, str]:
    """Helper to check record values, phone matching, and expiration date."""
    if record.get("phone_number") != phone_number:
        return False, "Consent token is registered to a different phone number."
    if record.get("tenant_id") != tenant_id:
        return False, "Consent token tenant owner mismatch."
        
    expires_at_str = record.get("expires_at")
    if not expires_at_str:
        return False, "Consent expiration date is missing."
        
    try:
        # Standardize ISO timestamps conversion
        expires_at = datetime.datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        if datetime.datetime.now(datetime.timezone.utc) > expires_at:
            return False, "Consent token has expired (quarantine expired after 90 days)."
    except Exception as e:
        return False, f"Failed to parse consent expiration date: {e}"
        
    return True, "Valid consent token."

# ----------------------------------------------------
# DYNAMIC DISCLOSURES RETRIEVAL (FTC & Recording consent)
# ----------------------------------------------------
def get_tenant_compliance_settings(tenant_id: str) -> dict:
    """
    Fetches compliance settings for custom disclosures per tenant, returning standard fallbacks on missing.
    """
    default_settings = {
        "recording_disclosure_enabled": True,
        "recording_disclosure_text": "This call may be recorded for quality and training purposes.",
        "ai_disclosure_enabled": True,
        "ai_disclosure_text": "You are speaking with an automated assistant."
    }
    
    if supabase_client:
        try:
            res = supabase_client.table("tenant_compliance_settings").select("*").eq("tenant_id", tenant_id).execute()
            if res.data:
                return {**default_settings, **res.data[0]}
        except Exception as e:
            logger.error("compliance_settings_supabase_failed", message="Failed to fetch tenant settings.", error=str(e))
            
    # Check Local fallback registry
    try:
        with open(LOCAL_COMPLIANCE_SETTINGS_FILE, "r") as f:
            local_data = json.load(f)
            if tenant_id in local_data:
                return {**default_settings, **local_data[tenant_id]}
    except Exception as e:
        logger.error("compliance_settings_local_failed", message="Local settings read failed.", error=str(e))
        
    return default_settings

# ----------------------------------------------------
# COMPLIANCE REST ENDPOINTS FOR DNC MANAGEMENT
# ----------------------------------------------------
@compliance_router.post("/dnc/add")
async def add_to_dnc(phone_payload: dict, user: UserPrincipal = Depends(RoleChecker(["agent", "admin"]))):
    """
    Enrolls an E.164 phone number into the tenant-scoped DNC registry.
    """
    phone_number = phone_payload.get("phone_number")
    if not phone_number:
        return {"success": False, "error": "phone_number is required"}
        
    tenant_id = user.tenant_id
    success = False
    
    # 1. Supabase Postgres write
    if supabase_client:
        try:
            res = supabase_client.table("dnc_numbers").insert({
                "phone_number": phone_number,
                "tenant_id": tenant_id
            }).execute()
            success = True
            logger.info("dnc_enrolled_supabase", message="Phone enrolled in Supabase DNC.", phone=phone_number, tenant_id=tenant_id)
        except Exception as e:
            logger.error("dnc_enroll_supabase_failed", message="Supabase DNC enrollment failed. Falling back to local.", error=str(e))
            
    # 2. Local Fallback persistence
    try:
        with open(LOCAL_DNC_FILE, "r+") as f:
            dnc_list = json.load(f)
            # Avoid duplicates
            exists = any(r.get("phone_number") == phone_number and r.get("tenant_id") == tenant_id for r in dnc_list)
            if not exists:
                dnc_list.append({
                    "id": str(uuid.uuid4()),
                    "phone_number": phone_number,
                    "tenant_id": tenant_id,
                    "created_at": datetime.datetime.utcnow().isoformat()
                })
                f.seek(0)
                json.dump(dnc_list, f, indent=2)
                f.truncate()
            success = True
            logger.info("dnc_enrolled_local", message="Phone enrolled in Local DNC.", phone=phone_number, tenant_id=tenant_id)
    except Exception as e:
        logger.error("dnc_enroll_local_failed", message="Local DNC enrollment failed.", error=str(e))
        
    return {"success": success, "phone_number": phone_number, "tenant_id": tenant_id, "action": "added_to_dnc"}

@compliance_router.delete("/dnc/remove")
async def remove_from_dnc(phone_payload: dict, user: UserPrincipal = Depends(RoleChecker(["agent", "admin"]))):
    """
    Removes an E.164 phone number from the tenant-scoped DNC registry.
    """
    phone_number = phone_payload.get("phone_number")
    if not phone_number:
        return {"success": False, "error": "phone_number is required"}
        
    tenant_id = user.tenant_id
    success = False
    
    # 1. Supabase Postgres delete
    if supabase_client:
        try:
            res = supabase_client.table("dnc_numbers").delete().eq("phone_number", phone_number).eq("tenant_id", tenant_id).execute()
            success = True
            logger.info("dnc_removed_supabase", message="Phone removed from Supabase DNC.", phone=phone_number, tenant_id=tenant_id)
        except Exception as e:
            logger.error("dnc_remove_supabase_failed", message="Supabase DNC deletion failed.", error=str(e))
            
    # 2. Local Fallback deletion
    try:
        with open(LOCAL_DNC_FILE, "r+") as f:
            dnc_list = json.load(f)
            filtered = [r for r in dnc_list if not (r.get("phone_number") == phone_number and r.get("tenant_id") == tenant_id)]
            f.seek(0)
            json.dump(filtered, f, indent=2)
            f.truncate()
            success = True
            logger.info("dnc_removed_local", message="Phone removed from Local DNC.", phone=phone_number, tenant_id=tenant_id)
    except Exception as e:
        logger.error("dnc_remove_local_failed", message="Local DNC deletion failed.", error=str(e))
        
    return {"success": success, "phone_number": phone_number, "tenant_id": tenant_id, "action": "removed_from_dnc"}

@compliance_router.get("/dnc/list")
async def list_dnc(user: UserPrincipal = Depends(RoleChecker(["agent", "admin", "viewer"]))):
    """
    Returns the tenant-scoped DNC registry list.
    """
    tenant_id = user.tenant_id
    
    if supabase_client:
        try:
            res = supabase_client.table("dnc_numbers").select("*").eq("tenant_id", tenant_id).execute()
            return {"success": True, "dnc_list": res.data or []}
        except Exception as e:
            logger.error("dnc_list_supabase_failed", message="Supabase DNC list failed.", error=str(e))
            
    # Local Fallback
    try:
        with open(LOCAL_DNC_FILE, "r") as f:
            dnc_list = json.load(f)
            filtered = [r for r in dnc_list if r.get("tenant_id") == tenant_id]
            return {"success": True, "dnc_list": filtered}
    except Exception as e:
        logger.error("dnc_list_local_failed", message="Local DNC list failed.", error=str(e))
        return {"success": False, "error": "Failed to retrieve DNC list"}
