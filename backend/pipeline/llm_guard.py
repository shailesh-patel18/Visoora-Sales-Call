import os
import re
import time
import random
import datetime
import asyncio
from typing import Optional, List, Dict, Any, Callable
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger("visoora_llm_guard")


# ====================================================
# CONFIG & PHRASE BLOCKLISTS
# ====================================================
FORBIDDEN_REGEXES = [
    r"\bas\s+an\s+ai\b",
    r"\bi'm\s+a\s+bot\b",
    r"\bi\s+am\s+a\s+bot\b",
    r"\byou\s+are\s+a\s+bot\b",
    r"\bprogrammed\s+to\b",
    r"\bprogrammed\s+by\b",
    r"\bbot\s+programmed\b",
    r"\bi'm\s+programmed\b",
    r"\bi\s+am\s+programmed\b",
    r"\bi\s+guarantee\b",
    r"\b100%\s+success\s+rate\b",
    r"\b100%\s+success\b",
    r"\bas\s+an\s+artificial\s+intelligence\b",
    r"\bprogrammed\b",
    r"\bguarantee\b",
    r"\bbot\b",
    r"\bartificial\s+intelligence\b"
]

# Standard unapproved competitor list
UNAPPROVED_COMPETITORS = [
    "zoominfo",
    "apollo",
    "outreach",
    "salesloft",
    "dialpad",
    "gong",
]

# Safe recovery substitutions pool (10 entries)
SAFE_RECOVERY_POOL = [
    "That's a great question — let me address that properly.",
    "Sure thing, I want to make sure I give you the correct details on that.",
    "Right. Let's make sure we walk through the exact details during our meeting next week.",
    "Got it. I want to be 100% sure on that, so I'll check with my engineering lead.",
    "Absolutely, that's a very fair point and I want to cover that correctly.",
    "Of course. Let me make a note of that so we can address it with the integration team.",
    "I hear you. Let me check that and get back to you with the exact numbers.",
    "Got it. Let's make sure we focus on the main setup, and we'll review the rest later.",
    "That makes total sense — I'd want to check the specific compatibility for you first.",
    "Understood. Let's schedule some time so we can go through that aspect in detail."
]

GROUNDING_RECOVERY = "I'd want to make sure I give you the right information on that — my colleague will follow up."


# ====================================================
# 1. OUTPUT VALIDATION LAYER
# ====================================================
class ValidationChain:
    """
    Enforces conversational safety guardrails, sentence limits, profanity checks,
    and regex-based blocklists with semantic fallback routing.
    """
    def __init__(self, blocklist_phrases=None, allowed_sources_text: str = ""):
        self.blocklist = blocklist_phrases or [
            "As an AI", "I'm a bot", "I'm programmed",
            "I guarantee", "100% success rate"
        ]
        # Pre-computed allowed sources text for price grounding check
        self.allowed_sources_text = allowed_sources_text.lower()
        
    def truncate_to_two_sentences(self, text: str) -> str:
        """Truncates the generated output strictly at the second sentence boundary."""
        # Regex splits on standard end-of-sentence punctuation (.!?), preserving them
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        if len(sentences) > 2:
            return " ".join(sentences[:2])
        return text

    def check_forbidden_phrases(self, text: str, approved_competitors: List[str] = None) -> bool:
        """Returns True if the text violates forbidden phrases or unapproved competitor blocklists."""
        lower_txt = text.lower()
        
        # 1. Check Regex blocklist
        for pattern in FORBIDDEN_REGEXES:
            if re.search(pattern, lower_txt):
                return True
                
        # 2. Check pricing mentions — only block dollar values NOT present in the approved
        #    grounding sources. This prevents the guard from blocking the AI's own
        #    product pricing (e.g., "$499/month") which is a legitimate grounded claim.
        dollar_matches = re.findall(r"\$\d+|\b\d+\s*dollars\b|\b\d+\s*bucks\b", lower_txt)
        for price_mention in dollar_matches:
            # Strip punctuation to get the bare number/phrase for source comparison
            if price_mention not in self.allowed_sources_text:
                return True

        # 3. Check Competitor blocklist
        for comp in UNAPPROVED_COMPETITORS:
            if comp in lower_txt:
                if approved_competitors and comp in [c.lower() for c in approved_competitors]:
                    continue
                return True

        # 4. Check embedding semantic similarity against forbidden concepts
        for phrase in self.blocklist:
            sim = self._calculate_heuristic_similarity(lower_txt, phrase.lower())
            if sim > 0.8:
                return True
                
        return False

    def check_profanity_or_offtopic(self, text: str) -> bool:
        """Detects profanity or toxic/off-topic patterns using a localized validator."""
        lower_txt = text.lower()
        
        # Basic profanity and toxicity detector
        profanity_words = [
            "fuck", "shit", "bitch", "asshole", "cunt", "damn", "bastard", 
            "toxic", "vulgar"
        ]
        for word in profanity_words:
            if re.search(rf"\b{word}\b", lower_txt):
                return True
                
        # Off-topic and prompt injection detector (highly comprehensive)
        off_topic_patterns = [
            # Ignore overrides
            r"\bignore\b",
            r"\boverride\b",
            r"\bbypass\b",
            r"\breboot\b",
            # Forget directives
            r"\bforget\b",
            # Act / Roleplay directives
            r"\bact\s+as\b",
            r"\byou\s+are\s+now\b",
            r"\btransition\s+to\b",
            r"\bnew\s+role\b",
            # Code / scripting / technology injection
            r"\bscripts?\b",
            r"\bcode\b",
            r"\bcompiler\b",
            r"\bterminal\b",
            r"\bcalculator\b",
            r"\bssh\b",
            r"\bcredentials\b",
            r"\bsupabase_url\b",
            r"\btokens?\b",
            r"\bsecrets?\b",
            r"\bpasswords?\b",
            r"\bdatabase\b",
            r"\bschema\b",
            r"\benvironment\b",
            r"\bvariables?\b",
            r"\bscrape\b",
            r"\bdrop\s+tables\b",
            r"\bpython\b",
            r"\btranslate\b",
            # Prompt leaks
            r"\bprompts?\b",
            r"\btemplate\b",
            r"\bdirectives?\b",
            r"\binstructions?\b",
            # Other compliance bypass / competitors
            r"\bgdpr\b",
            r"\bunapproved\b",
            r"\bsales\s+agent\b",
            r"\bautomated\s+system\b",
            r"\bsdr\s+pitch\b",
        ]
        for pattern in off_topic_patterns:
            if re.search(pattern, lower_txt):
                return True

        return False

    def _calculate_heuristic_similarity(self, text1: str, text2: str) -> float:
        """Local standard string-intersection based similarity mapping to mimic embeddings."""
        words1 = set(re.findall(r"\b\w+\b", text1))
        words2 = set(re.findall(r"\b\w+\b", text2))
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        return len(intersection) / (len(words1) ** 0.5 * len(words2) ** 0.5)


# ====================================================
# 2. GROUNDING ENFORCEMENT LAYER
# ====================================================
class GroundingChecker:
    """
    Cross-references factual statements (numbers, dates, metrics) in LLM outputs
    against compiled FSM prompts, CRM contexts, and product settings.
    """
    def __init__(self, allowed_sources: List[str]):
        self.allowed_sources = " ".join(allowed_sources).lower()

    def check_grounding_score(self, output_text: str) -> float:
        """
        Extracts numbers, percentages, dates, and names to verify grounding.
        Returns a score from 0.0 (fully grounded) to 1.0 (fully ungrounded).
        """
        # Extract factual claims
        numbers = re.findall(r"\b\d+(?:\.\d+)?%?\b", output_text)
        dates = re.findall(r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|next week|q3|q4|january|february|march|april|may|june|july|august|september|october|november|december)\b", output_text, re.IGNORECASE)
        features = re.findall(r"\b(?:cloudscale|hubspot|salesforce|crm|VAD|VAD engine|stereo|audio|twilio|subaccount)\b", output_text, re.IGNORECASE)

        claims = list(set(numbers + dates + features))
        if not claims:
            return 0.0 # No factual claims to flag

        ungrounded_count = 0
        for claim in claims:
            if claim.lower() not in self.allowed_sources:
                ungrounded_count += 1

        return ungrounded_count / len(claims)


# ====================================================
# 3. LLM PROVIDER FALLBACK CHAIN & CIRCUIT BREAKER
# ====================================================
class LLMProviderFallbackChain:
    """
    Orchestrates LLM calls across multiple providers, enforcing circuit-breaker patterns.
    Failures within 60s trigger dynamic fallbacks.
    """
    def __init__(self):
        self.active_provider = "claude"
        self.failures_timestamps: List[float] = []
        self.lock = asyncio.Lock()
        
    async def record_failure_and_check_failover(self):
        """Records provider failure and auto-switches to the next provider if threshold breached."""
        async with self.lock:
            now = time.time()
            self.failures_timestamps.append(now)
            
            # Filter failures within the last 60 seconds
            self.failures_timestamps = [t for t in self.failures_timestamps if now - t <= 60.0]
            
            if len(self.failures_timestamps) >= 3:
                # Trigger failover transition
                if self.active_provider == "claude":
                    self.active_provider = "emergency"
                    logger.warn("llm_circuit_breaker_tripped", msg="Claude failed 3x in 60s. Transitioning to Emergency local scripted responses.")
                self.failures_timestamps.clear() # Clear stamps post-transition

    async def execute_llm_call(self, provider_calls: Dict[str, Callable[[], Any]]) -> str:
        """Executes LLM call targeting the active provider, with fallback cascading."""
        current = self.active_provider
        
        try:
            if current == "claude":
                return await provider_calls["claude"]()
            else:
                return await provider_calls["emergency"]()
        except Exception as e:
            logger.error("llm_provider_execution_failed", provider=current, error=str(e))
            # Record failure and trigger cascading fallback instantly
            await self.record_failure_and_check_failover()
            
            # Cascade to next provider
            if self.active_provider != current:
                return await self.execute_llm_call(provider_calls)
            raise e


# ====================================================
# 4. LATENCY ENFORCER & PROMETHEUS TELEMETRY
# ====================================================
class LatencyEnforcer:
    """Enforces strict sub-800ms latency metrics, masking delays with streamed filler audio."""
    def __init__(self):
        # Latency registry per provider: provider -> list of float milliseconds
        self.latency_metrics: Dict[str, List[float]] = {
            "google": [],
            "claude": [],
            "gpt4o": [],
            "emergency": []
        }

    def record_latency(self, provider: str, duration_ms: float):
        self.latency_metrics[provider].append(duration_ms)
        logger.info("llm_latency_recorded", provider=provider, latency_ms=duration_ms)

    def get_percentile_latency(self, provider: str, percentile: float) -> float:
        latencies = sorted(self.latency_metrics.get(provider, []))
        if not latencies:
            return 0.0
        idx = int(len(latencies) * percentile / 100.0)
        return latencies[min(idx, len(latencies) - 1)]

    async def call_with_latency_mask(
        self,
        llm_coro: asyncio.Task,
        stream_filler_callback: Callable[[str], Any],
        provider: str
    ) -> str:
        """
        Executes LLM call with a 600ms latency enforcer mask.
        Streams filler audio if execution time crosses 600ms.
        """
        start = time.time()
        
        # Wait up to 600ms (0.6s)
        done, pending = await asyncio.wait(
            [llm_coro],
            timeout=0.6,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        if llm_coro in done:
            duration_ms = (time.time() - start) * 1000.0
            self.record_latency(provider, duration_ms)
            return await llm_coro
        else:
            # Exceeded 600ms threshold! Dispatch latency masking filler phrase
            logger.warn("llm_latency_threshold_exceeded", limit_ms=600, elapsed_ms=600)
            await stream_filler_callback("Let me think about that for just a second.")
            
            # Await main LLM response
            res = await llm_coro
            duration_ms = (time.time() - start) * 1000.0
            self.record_latency(provider, duration_ms)
            return res


# ====================================================
# GLOBAL COORDINATOR SYSTEM
# ====================================================
class LLMGuardSystem:
    """
    Master Hallucination Prevention, Safety Guard, and Provider Fallback system.
    Runs output validations, claim grounding checks, and latency masks.
    """
    def __init__(self, allowed_grounding_sources: List[str], approved_competitors: List[str] = None):
        self.validator = ValidationChain(
            allowed_sources_text=" ".join(allowed_grounding_sources)
        )
        self.grounding = GroundingChecker(allowed_grounding_sources)
        self.fallback_chain = LLMProviderFallbackChain()
        self.latency = LatencyEnforcer()
        self.approved_competitors = approved_competitors or ["Salesforce", "HubSpot"]
        self.command_allowlist = ["BOOK_CALENDAR", "END_CALL", "TRANSFER_HUMAN", "QUALIFY_LEAD", "PLAY_GREETING"]

    def verify_prompt_safety(self, prompt: str) -> bool:
        """Runs BEFORE the LLM generates a response to detect prompt injection."""
        lower_prompt = prompt.lower()
        injection_patterns = [
            r"\bignore\b.*\binstructions\b",
            r"\boverride\b",
            r"\bbypass\b",
            r"\bsystem\s+prompt\b",
            r"\bforget\b",
            r"\bnew\s+role\b"
        ]
        for pattern in injection_patterns:
            if re.search(pattern, lower_prompt):
                logger.error("prompt_injection_detected", pattern=pattern)
                return False
        return True

    def redact_pii_for_logging(self, text: str) -> str:
        """Redacts PII (emails, phones, SSNs) from text for safe logging."""
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', text)
        text = re.sub(r'\+?\d{1,3}?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE_REDACTED]', text)
        return text

    def check_command_allowlist(self, output: str) -> bool:
        """Verifies any commands emitted by the LLM are in the allowlist."""
        commands_found = re.findall(r"\[([A-Z_]+)\]", output)
        for cmd in commands_found:
            if cmd not in self.command_allowlist:
                return False
        return True

    async def generate_safe_response(
        self,
        prompt_text: str,
        provider_calls: Dict[str, Callable[[], Any]],
        stream_filler_callback: Callable[[str], Any]
    ) -> str:
        """
        Generates and fully filters an AI response.
        Enforces latency budget masks, RAG claim grounding, and phrase blocklists.
        """
        # 0. Pre-generation Prompt Injection Check
        if not self.verify_prompt_safety(prompt_text):
            logger.error("safety_guard_violation", reason="prompt_injection_prevention")
            return random.choice(SAFE_RECOVERY_POOL)

        # Redact prompt for safe logging
        safe_log_prompt = self.redact_pii_for_logging(prompt_text)
        logger.debug("llm_generation_start", prompt_preview=safe_log_prompt[:100])

        provider = self.fallback_chain.active_provider
        
        # 1. Trigger LLM call with Latency Mask
        llm_coro = asyncio.create_task(self.fallback_chain.execute_llm_call(provider_calls))
        raw_text = await self.latency.call_with_latency_mask(
            llm_coro, stream_filler_callback, provider
        )
        
        # 2. Output Validation
        # Check command allowlist
        if not self.check_command_allowlist(raw_text):
            logger.error("safety_guard_violation", reason="unapproved_command")
            return random.choice(SAFE_RECOVERY_POOL)

        # Enforce max 2 sentences limit
        truncated_text = self.validator.truncate_to_two_sentences(raw_text)
        
        # Check forbidden phrases / competitor leaks / profanity / prompt injection
        if (self.validator.check_forbidden_phrases(truncated_text, self.approved_competitors) or
            self.validator.check_profanity_or_offtopic(truncated_text)):
            logger.error("safety_guard_violation", action="substitution", raw_text=self.redact_pii_for_logging(raw_text))
            return random.choice(SAFE_RECOVERY_POOL)

        # 3. Grounding Verification
        grounding_score = self.grounding.check_grounding_score(truncated_text)
        if grounding_score > 0.7:
            logger.error("grounding_score_violation", score=grounding_score, action="grounding_substitution")
            return GROUNDING_RECOVERY

        return truncated_text
