import os
import json
import datetime
from typing import List, Dict, Any, Optional
from html import escape
from urllib.parse import urlencode, urlparse
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Response, Depends, Form
import structlog
from server.storage_manager import supabase_client
from security.config import settings
from security.twilio_auth import verify_twilio_signature
from services.calendar import calendar_service
from services.sms import sms_service

logger = structlog.get_logger("visoora_inbound")

inbound_router = APIRouter(tags=["Inbound"])

LOCAL_TENANTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "recordings", 
    "local_tenants.json"
)

LOCAL_AGENTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "recordings", 
    "local_agent_availability.json"
)

LOCAL_CALLBACKS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "recordings", 
    "local_callback_tasks.json"
)

# ----------------------------------------------------
# DATABASE SEEDERS & LOCAL FILES INITIALIZATION
# ----------------------------------------------------
def _init_local_files():
    os.makedirs(os.path.dirname(LOCAL_TENANTS_FILE), exist_ok=True)
    
    # 1. Local Tenants Registry
    if not os.path.exists(LOCAL_TENANTS_FILE):
        with open(LOCAL_TENANTS_FILE, "w") as f:
            json.dump([
                {
                    "id": "acme_tenant",
                    "name": "Acme Corp",
                    "twilio_phone": "+15017122661",
                    "greeting": "Thank you for calling Acme Corp! How can I help you today?",
                    "agent_persona": "You are Alex, an automated sales representative for Acme Corp.",
                    "fsm_mode": "standard"
                }
            ], f, indent=2)
            
    # 2. Local Agent Availability Registry
    if not os.path.exists(LOCAL_AGENTS_FILE):
        with open(LOCAL_AGENTS_FILE, "w") as f:
            json.dump([
                {
                    "tenant_id": "acme_tenant",
                    "agent_user_id": "agent_olivia",
                    "agent_name": "Olivia",
                    "is_available": True,
                    "last_seen": datetime.datetime.utcnow().isoformat()
                }
            ], f, indent=2)
            
    # 3. Local Callback Tasks Registry
    if not os.path.exists(LOCAL_CALLBACKS_FILE):
        with open(LOCAL_CALLBACKS_FILE, "w") as f:
            json.dump([], f)

_init_local_files()


# ----------------------------------------------------
# 1. TWILIO INBOUND VOICE WEBHOOK (POST /inbound-call)
# ----------------------------------------------------
@inbound_router.post("/inbound-call")
async def handle_inbound_call_webhook(
    request: Request,
    To: str = Form(...),
    From: str = Form(...),
    CallSid: str = Form(...)
):
    """
    Inbound voice webhook triggered by Twilio when a call is dialed to our tenant number.
    Looks up tenant configuration and connects the call to a secure inbound media stream.
    """
    logger.info("twilio_inbound_call_received", recipient=To, sender=From, call_sid=CallSid)
    
    # Defaults
    tenant_id = "acme_tenant"
    greeting = "Thank you for calling Visoora! How can I help you today?"
    company_name = "Visoora"
    
    # 1. Look up tenant by inbound phone number (To parameter)
    if supabase_client:
        try:
            res = supabase_client.table("tenants").select("*").eq("twilio_phone", To).execute()
            if res.data:
                tenant = res.data[0]
                tenant_id = tenant["id"]
                company_name = tenant["name"]
                greeting = tenant.get("greeting") or f"Thank you for calling {company_name}!"
        except Exception as e:
            logger.error("db_tenant_lookup_failed", error=str(e))
            
    # Local fallback
    if tenant_id == "acme_tenant":
        try:
            with open(LOCAL_TENANTS_FILE, "r") as f:
                tenants = json.load(f)
            for t in tenants:
                if t["twilio_phone"] == To:
                    tenant_id = t["id"]
                    company_name = t["name"]
                    greeting = t.get("greeting") or f"Thank you for calling {company_name}!"
                    break
        except Exception as e:
            logger.error("local_tenant_lookup_failed", error=str(e))
            
    # 2. Build secure Websocket URL
    configured = settings.server_public_domain.strip().rstrip("/")
    if configured:
        parsed = urlparse(configured if "://" in configured else f"https://{configured}")
        base_host = parsed.netloc or parsed.path
        protocol = "wss" if (parsed.scheme or "https") == "https" else "ws"
    else:
        base_host = request.headers.get("x-forwarded-host") or request.headers.get("host", "localhost:8000")
        if "localhost" not in base_host and "127.0.0.1" not in base_host:
            protocol = "wss"
        else:
            protocol = "wss" if request.headers.get("x-forwarded-proto") == "https" else "ws"

    query = urlencode({"caller_phone": From, "company": company_name})
    ws_url = f"{protocol}://{base_host}/media-stream/inbound/{tenant_id}?{query}"
    ws_url_xml = escape(ws_url, quote=True)
    greeting_xml = escape(greeting)
    
    # Pause buffer ensures that Twilio doesn't tear down the call before WebSocket opens
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Olivia">{greeting_xml}</Say>
    <Connect>
        <Stream url="{ws_url_xml}" />
    </Connect>
    <Pause length="28800" />
</Response>
"""
    return Response(content=twiml, media_type="application/xml")


# ----------------------------------------------------
# 2. INBOUND DIALOG FSM CONTROLLER & WEB_SOCKET ROUTE
# ----------------------------------------------------
class InboundFSMController:
    """
    Governs state transitions, Lead Qualifications, Bookings, and warm human hot-transfers.
    """
    def __init__(self, tenant_id: str, caller_phone: str, company: str):
        self.tenant_id = tenant_id
        self.caller_phone = caller_phone
        self.company = company
        self.state = "GREETING"
        self.utterance_count = 0
        
        # Lead Qualification fields
        self.lead_name = None
        self.lead_company = None
        
        # Calendar Slots
        self.available_slots = []
        
    def process_utterance(self, text: str) -> Dict[str, Any]:
        """
        Processes a prospect spoken turn and updates the dialog FSM state.
        Returns a dict containing:
          - "response": The spoken message to play back to the user
          - "transfer_action": Optional twiml configuration if warm-transferring
          - "hangup": Boolean if session completes
        """
        self.utterance_count += 1
        clean_txt = text.strip().lower()
        
        # ====================================================
        # STATE GREETING
        # ====================================================
        if self.state == "GREETING":
            # Greeting welcome was played by TwiML first. Transition immediately.
            self.state = "INTENT_DETECTION"
            
        # ====================================================
        # STATE INTENT_DETECTION (utterance 1 and 2)
        # ====================================================
        if self.state == "INTENT_DETECTION":
            # Classify caller intent based on keywords
            if any(w in clean_txt for w in ["schedule", "book", "appointment", "demo", "calendar"]):
                self.state = "BOOKING"
                return self._activate_booking()
            elif any(w in clean_txt for w in ["new", "lead", "buy", "pricing", "sales", "prospect"]):
                self.state = "QUALIFY_LEAD"
                return {
                    "response": "Wonderful! We would love to share how we can help. May I start by getting your name?"
                }
            elif any(w in clean_txt for w in ["support", "issue", "customer", "agent", "human", "representative", "olivia"]):
                self.state = "TRANSFER_TO_HUMAN"
                return self._activate_human_transfer()
            else:
                # If utterance count reaches 2 and still unclassified, route to human
                if self.utterance_count >= 2:
                    self.state = "TRANSFER_TO_HUMAN"
                    return self._activate_human_transfer()
                return {
                    "response": f"Got it. Are you calling to book a demo, ask about pricing, or speak with support?"
                }
                
        # ====================================================
        # STATE QUALIFY_LEAD
        # ====================================================
        elif self.state == "QUALIFY_LEAD":
            if not self.lead_name:
                self.lead_name = text.strip()
                return {
                    "response": f"Great to meet you, {self.lead_name}. And what is the name of your company?"
                }
            elif not self.lead_company:
                self.lead_company = text.strip()
                
                # Qualified! Let's persist contact to database/local file
                self._save_qualified_lead()
                
                # Automatically transition to Booking
                self.state = "BOOKING"
                return self._activate_booking(welcome_back=f"Perfect. I have qualified your lead at an 85 score. Let's get you booked. ")
                
        # ====================================================
        # STATE BOOKING
        # ====================================================
        elif self.state == "BOOKING":
            # Check user slot selection
            selected_idx = None
            if any(w in clean_txt for w in ["first", "one", "10", "10:00", "tuesday"]):
                selected_idx = 0
            elif any(w in clean_txt for w in ["second", "two", "2", "2:00", "wednesday"]):
                selected_idx = 1
                
            if selected_idx is not None and len(self.available_slots) > selected_idx:
                chosen_slot = self.available_slots[selected_idx]
                
                # Resolve contact id
                contact_id = "contact_fallback"
                if supabase_client:
                    try:
                        res = supabase_client.table("contacts").select("id").eq("phone_e164", self.caller_phone).eq("tenant_id", self.tenant_id).execute()
                        if res.data:
                            contact_id = res.data[0]["id"]
                    except Exception:
                        pass
                
                # Book slot
                try:
                    event_id = calendar_service.book_slot(
                        tenant_id=self.tenant_id,
                        contact_id=contact_id,
                        slot=chosen_slot,
                        title=f"Visoora Inbound Call: Demo with {self.lead_name or 'Prospect'}"
                    )
                    
                    # Outbound SMS Confirmation alert
                    sms_service.send_booking_sms(
                        tenant_id=self.tenant_id,
                        phone_e164=self.caller_phone,
                        name=self.lead_name or "Valued Customer",
                        company=self.company,
                        slot=chosen_slot
                    )
                    
                    self.state = "COMPLETE"
                    slot_str = chosen_slot.strftime("%A at %I:%M %p")
                    return {
                        "response": f"Excellent! Your booking is fully confirmed for {slot_str}. An SMS confirmation has been sent to your phone. Thank you so much!",
                        "hangup": True
                    }
                except Exception as e:
                    logger.error("fsm_booking_failed", error=str(e))
                    return {
                        "response": "Oh, it looks like that slot was just booked. Let me fetch other calendar opportunities."
                    }
            else:
                return {
                    "response": "I didn't quite catch that. Would you like the first slot or the second slot?"
                }
                
        # ====================================================
        # STATE TRANSFER_TO_HUMAN
        # ====================================================
        elif self.state == "TRANSFER_TO_HUMAN":
            return self._activate_human_transfer()
            
        # ====================================================
        # STATE COMPLETE
        # ====================================================
        elif self.state == "COMPLETE":
            return {
                "response": "Thank you for calling Acme Corp. Have a wonderful day!",
                "hangup": True
            }
            
        return {"response": "I'm here to help. Could you clarify your request?"}

    def _activate_booking(self, welcome_back: str = "") -> Dict[str, Any]:
        """Queries calendar slots and speaks them back to the caller."""
        slots = calendar_service.get_available_slots(self.tenant_id, num_slots=2)
        self.available_slots = slots
        
        if not slots:
            self.state = "TRANSFER_TO_HUMAN"
            return self._activate_human_transfer()
            
        slot1_str = slots[0].strftime("%A at %I:%M %p")
        slot2_str = slots[1].strftime("%A at %I:%M %p")
        
        return {
            "response": f"{welcome_back}I have two slots available: first is {slot1_str}, and second is {slot2_str}. Which of these works best for you?"
        }

    def _activate_human_transfer(self) -> Dict[str, Any]:
        """Checks agent availability, registers hot transfers or sets up callback logs."""
        agent = self._get_available_agent()
        
        if agent:
            agent_name = agent.get("agent_name", "Olivia")
            self.state = "COMPLETE"
            return {
                "response": f"I would be glad to connect you. Let me transfer you directly to {agent_name}. Please stand by.",
                "transfer_action": {
                    "action": "conference_transfer",
                    "conference_name": f"conf_{self.tenant_id}_{agent['agent_user_id']}",
                    "agent_name": agent_name
                }
            }
        else:
            # Local fallback: Log callback task
            self._save_callback_task()
            self.state = "COMPLETE"
            return {
                "response": "Our team is busy right now. Can I have you leave your number and we'll call you back within 2 hours?",
                "hangup": True
            }

    def _get_available_agent(self) -> Optional[Dict[str, Any]]:
        """Queries availability table to find active agent."""
        if supabase_client:
            try:
                res = supabase_client.table("agent_availability").select("*").eq("tenant_id", self.tenant_id).eq("is_available", True).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error("db_agent_query_failed", error=str(e))
                
        # Local fallback lookup
        try:
            with open(LOCAL_AGENTS_FILE, "r") as f:
                agents = json.load(f)
            for a in agents:
                if a["tenant_id"] == self.tenant_id and a["is_available"]:
                    return a
        except Exception:
            pass
        return None

    def _save_qualified_lead(self):
        """Creates contact and seeds default pipeline opportunity."""
        contact_id = f"c_{uuid_short()}"
        contact_payload = {
            "id": contact_id,
            "tenant_id": self.tenant_id,
            "phone_e164": self.caller_phone,
            "full_name": self.lead_name or "Valued Customer",
            "name": self.lead_name or "Valued Customer",
            "company_name": self.lead_company or "Acme Corp",
            "company": self.lead_company or "Acme Corp",
            "lead_score": 85,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat()
        }
        
        # Supabase Persist
        if supabase_client:
            try:
                supabase_client.table("contacts").insert(contact_payload).execute()
                logger.info("db_contact_created", id=contact_id)
            except Exception as e:
                logger.error("db_contact_persist_failed", error=str(e))
                
        # Local Fallback
        try:
            local_contacts_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                "recordings", 
                "local_crm_contacts.json"
            )
            os.makedirs(os.path.dirname(local_contacts_file), exist_ok=True)
            contacts = []
            if os.path.exists(local_contacts_file):
                with open(local_contacts_file, "r") as f:
                    contacts = json.load(f)
            contacts.append(contact_payload)
            with open(local_contacts_file, "w") as f:
                json.dump(contacts, f, indent=2)
            logger.info("local_contact_created", id=contact_id)
        except Exception as e:
            logger.error("local_contact_persist_failed", error=str(e))

    def _save_callback_task(self):
        """Saves offline callback request to database."""
        task_id = f"tsk_{uuid_short()}"
        task_payload = {
            "id": task_id,
            "tenant_id": self.tenant_id,
            "phone_number": self.caller_phone,
            "status": "pending",
            "callback_window": "2 hours",
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        
        if supabase_client:
            try:
                supabase_client.table("callback_tasks").insert(task_payload).execute()
                logger.info("db_callback_task_created", id=task_id)
            except Exception as e:
                logger.error("db_callback_task_failed", error=str(e))
                
        # Local Fallback
        try:
            with open(LOCAL_CALLBACKS_FILE, "r") as f:
                tasks = json.load(f)
            tasks.append(task_payload)
            with open(LOCAL_CALLBACKS_FILE, "w") as f:
                json.dump(tasks, f, indent=2)
            logger.info("local_callback_task_created", id=task_id)
        except Exception:
            pass


def uuid_short() -> str:
    import uuid
    return str(uuid.uuid4())[:8]


# ----------------------------------------------------
# 3. FASTAPI BI-DIRECTIONAL WEBSOCKET DIALOGUE HANDLER
# ----------------------------------------------------
@inbound_router.websocket("/media-stream/inbound/{tenant_id}")
async def handle_inbound_media_stream(websocket: WebSocket, tenant_id: str):
    """
    VoIP Media Stream dialogue orchestrator.
    Handles Twilio G.711 mu-law packages and processes caller speech turns via Inbound FSM.
    Also accepts simple utterance intercepts for integration testing.
    """
    await websocket.accept()
    logger.info("inbound_websocket_opened", tenant_id=tenant_id)
    
    caller_phone = websocket.query_params.get("caller_phone", "+15005550006")
    company = websocket.query_params.get("company", "Acme Corp")
    
    # Initialize the FSM
    fsm = InboundFSMController(tenant_id, caller_phone, company)
    
    try:
        while True:
            # Read messages from Twilio or unit tests client
            raw_msg = await websocket.receive_text()
            msg = json.loads(raw_msg)
            event = msg.get("event")
            
            # Unit Testing intercepts
            if event == "caller_speech":
                speech_text = msg.get("text", "")
                result = fsm.process_utterance(speech_text)
                
                # Dispatch response spoken audio (text fallback)
                await websocket.send_text(json.dumps({
                    "event": "agent_speech",
                    "text": result["response"],
                    "transfer_action": result.get("transfer_action"),
                    "hangup": result.get("hangup", False)
                }))
                
                if result.get("hangup"):
                    break
                    
            elif event == "media":
                # In production, transcode standard base64 mu-law audio frame,
                # feed to VAD engine, feed to Antigravity SDK, and stream output audio frames back.
                # Here, we keep a fast silent heartbeat handler to support live connections:
                pass
                
            elif event == "stop":
                logger.info("inbound_websocket_stop_received")
                break
                
    except WebSocketDisconnect:
        logger.info("inbound_websocket_disconnected")
    except Exception as e:
        logger.error("inbound_websocket_error", error=str(e))
    finally:
        logger.info("inbound_websocket_closed")
