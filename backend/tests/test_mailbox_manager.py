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
