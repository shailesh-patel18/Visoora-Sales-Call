import os
import pytest
from sales_employee.mailbox_manager import (
    connect_mailbox,
    list_mailboxes,
    get_mailbox,
    get_default_mailbox,
    set_default_mailbox,
    disconnect_mailbox,
)
from sales_employee.services import store
from security.encryption import decrypt_value

def test_mailbox_connection_and_encryption():
    tenant_id = "test_tenant_mailbox"
    email = "sender@acme.com"
    provider = "smtp"
    config = {"host": "smtp.acme.com", "password": "super_secret_password"}
    
    # 1. Connect Mailbox
    mailbox = connect_mailbox(tenant_id, email, provider, config)
    assert mailbox["email"] == email
    assert mailbox["provider"] == provider
    assert mailbox["is_default"] is True # First one is default
    
    # Ensure config is encrypted
    assert mailbox["connection_config"] != '{"host": "smtp.acme.com", "password": "super_secret_password"}'
    decrypted = decrypt_value(mailbox["connection_config"])
    assert "super_secret_password" in decrypted
    
    # 2. List Mailboxes
    m_list = list_mailboxes(tenant_id)
    assert len(m_list) == 1
    assert m_list[0]["id"] == mailbox["id"]
    
    # 3. Connect a second Mailbox
    email2 = "marketing@acme.com"
    mailbox2 = connect_mailbox(tenant_id, email2, provider, config, is_default=False)
    assert mailbox2["is_default"] is False
    
    # 4. Set new mailbox as default
    set_default_mailbox(tenant_id, mailbox2["id"])
    
    # Verify default switched
    default_m = get_default_mailbox(tenant_id)
    assert default_m["id"] == mailbox2["id"]
    assert default_m["is_default"] is True
    
    # Old default should be False
    old_default = get_mailbox(tenant_id, mailbox["id"])
    assert old_default["is_default"] is False
    
    # 5. Disconnect mailbox
    success = disconnect_mailbox(tenant_id, mailbox2["id"])
    assert success is True
    
    # Remaining mailbox should become default automatically
    remaining_default = get_default_mailbox(tenant_id)
    assert remaining_default["id"] == mailbox["id"]
    assert remaining_default["is_default"] is True


@pytest.mark.asyncio
async def test_oauth_token_refresh():
    import time
    from sales_employee.mailbox_manager import refresh_oauth_token_if_needed
    
    tenant_id = "test_tenant_refresh"
    email = "oauth@gmail.com"
    provider = "gmail"
    config = {
        "access_token": "expired_token",
        "refresh_token": "mock_refresh",
        "expiry": int(time.time()) - 100 # Expired
    }
    
    mailbox = connect_mailbox(tenant_id, email, provider, config)
    assert mailbox["provider"] == "gmail"
    
    # Trigger refresh
    updated = await refresh_oauth_token_if_needed(tenant_id, mailbox["id"])
    assert updated is not None
    
    # Verify token updated
    decrypted = decrypt_value(updated["connection_config"])
    import json
    new_config = json.loads(decrypted)
    assert "refreshed_mock_access_token_" in new_config["access_token"]
    assert new_config["expiry"] > time.time() + 3000


@pytest.mark.asyncio
async def test_rate_limits():
    import time
    from sales_employee.mailbox_manager import enforce_mailbox_rate_limits, connect_mailbox
    
    tenant_id = "test_tenant_rate"
    email = "rate@acme.com"
    mailbox = connect_mailbox(tenant_id, email, "smtp", {"host": "mock_smtp"})
    
    start_time = time.time()
    await enforce_mailbox_rate_limits(tenant_id, mailbox["id"])
    
    # Enforce second call instantly, should sleep to enforce 5s gap
    await enforce_mailbox_rate_limits(tenant_id, mailbox["id"])
    elapsed = time.time() - start_time
    assert elapsed >= 4.9 # At least 5-second gap enforced


def test_webhook_replay_and_signatures():
    import time
    from sales_employee.delivery_tracker import verify_sendgrid_signature, check_replay_and_deduplicate
    
    # Sandbox/Test mode bypass verification should return True
    assert verify_sendgrid_signature("signature", "timestamp", b"payload") is True
    
    # Replay protection check
    event_id = "unique_event_123"
    assert check_replay_and_deduplicate(event_id, time.time()) is True
    # Duplicate ID should return False
    assert check_replay_and_deduplicate(event_id, time.time()) is False
    
    # Stale timestamp (>300s age) should return False
    assert check_replay_and_deduplicate("new_id", time.time() - 350) is False

