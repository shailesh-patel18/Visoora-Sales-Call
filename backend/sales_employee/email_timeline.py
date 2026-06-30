from typing import Dict, Any, List, Optional
from sales_employee.services import store, require_tenant_id

def get_or_create_thread(tenant_id: str, lead_id: str, subject: str) -> Dict[str, Any]:
    """
    Retrieves an existing email thread matching the subject root, or creates a new one.
    """
    require_tenant_id(tenant_id)
    threads = store.list("email_threads", tenant_id, lead_id=lead_id)
    
    clean_subject = subject.lower().replace("re:", "").strip()
    if threads:
        for t in threads:
            t_subject = t.get("subject", "").lower().replace("re:", "").strip()
            if clean_subject == t_subject:
                return t
                
    # If no thread match, insert a new thread record
    thread_data = {
        "tenant_id": tenant_id,
        "lead_id": lead_id,
        "subject": subject,
        "message_ids": []
    }
    return store.insert("email_threads", thread_data)

def add_message_to_thread(tenant_id: str, thread_id: str, message_id: str) -> None:
    """
    Appends a message ID to the thread mapping.
    """
    require_tenant_id(tenant_id)
    rows = store.list("email_threads", tenant_id, id=thread_id)
    if rows:
        thread = rows[0]
        msg_ids = list(thread.get("message_ids", []))
        if message_id not in msg_ids:
            msg_ids.append(message_id)
            store.update("email_threads", tenant_id, thread_id, {"message_ids": msg_ids})
