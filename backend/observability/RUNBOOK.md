# Visoora Incident Runbook — Top 5 Expected Incidents

> **Audience**: On-call SRE  
> **SLA**: All P1 incidents must be acknowledged within 5 minutes, resolved or mitigated within 30 minutes.

---

## 1. High LLM Latency (P95 > 1200ms)

**Alert**: `HighLLMLatency` | **Severity**: Warning → Critical if sustained > 10min  
**Impact**: Agent responses delay beyond 1.2s, causing awkward silences and prospect hangups.

### Triage (< 60 seconds)
1. Open Grafana → **Visoora Ops Dashboard** → "LLM Latency Distribution" panel
2. Check which `provider` / `model` label is spiking:
   ```promql
   histogram_quantile(0.95, sum(rate(visoora_llm_latency_histogram_bucket{provider="anthropic"}[5m])) by (le))
   ```
3. Open Tempo → search by `visoora.llm_latency_ms > 1200` → inspect the full call trace

### Root Causes & Remediation
| Cause | Action |
|-------|--------|
| Provider throttling | Check Anthropic/OpenAI status page. Switch to fallback provider via `LLM_PRIMARY_PROVIDER` env var restart |
| Token queue congestion | Scale `call-orchestrator` replicas: `kubectl scale deploy call-orchestrator --replicas=6` |
| Network latency to provider | Check egress pod → provider RTT in Tempo spans. Consider regional endpoint |
| Prompt too long | Check `visoora.tts_text_length` span attribute. Reduce system prompt or RAG context window |

### Escalation
- If P95 > 2000ms for > 5min → page AI Platform team lead
- If all providers degraded → activate fallback phrase pool (LLMGuard safe responses)

---

## 2. Call Connection Failures (SLO breach: < 99.5%)

**Alert**: `CallConnectionSLOBreach` | **Severity**: Critical  
**Impact**: Prospects aren't reached, pipeline stalls, revenue impact.

### Triage
1. Grafana → check `visoora_call_connection_total{status="failure"}` rate
2. Loki → filter `{event="ws_accept_failed"}` or `{event="twilio_status_callback"}` with `call_status=failed`
3. Check Twilio Console → [Status Page](https://status.twilio.com)

### Root Causes & Remediation
| Cause | Action |
|-------|--------|
| Twilio API outage | Confirm via status page. Nothing to do — wait for recovery. Update status page |
| Webhook URL unreachable | Verify `SERVER_PUBLIC_DOMAIN` resolves. Check nginx ingress health. `curl -I https://{domain}/incoming-call` |
| WebSocket accept crash | Check Loki for `ws_accept_failed` CRITICAL logs with stack traces. Fix and deploy |
| Rate limiter over-aggressive | Check Redis `rate_limiter` keys. Temporarily raise `MAX_CONCURRENT_CALLS` |
| TLS cert expiry | Check cert dates: `echo | openssl s_client -connect {domain}:443 2>/dev/null | openssl x509 -noout -dates` |

### Escalation
- If Twilio outage → notify customers via status page
- If self-inflicted → rollback last deployment

---

## 3. Compliance Block Spike (> 10/min)

**Alert**: `ComplianceBlockSpike` | **Severity**: Critical  
**Impact**: Legal risk if blocks indicate a misconfigured campaign; revenue risk if false positives.

### Triage
1. Grafana → "Compliance Events Timeline" → identify which `reason` label dominates:
   - `DNC_BLOCKED` → mass campaign hitting DNC numbers
   - `OUTSIDE_CALLING_HOURS` → timezone misconfiguration
   - `CONSENT_MISSING` → consent tokens not being passed
2. Loki → `{level="critical", event=~"compliance.*"}` → examine blocked phone numbers and tenant

### Root Causes & Remediation
| Cause | Action |
|-------|--------|
| Campaign CSV has DNC numbers | Pause campaign. Clean CSV against DNC list. Re-upload |
| Timezone inference wrong | Check `phonenumbers` library version. Verify area code → timezone mapping |
| Consent token flow broken | Frontend → Backend: verify `consent_token` is passed in `/make-call` request body |
| Clock skew on pod | Check `date` on affected pod vs NTP. Fix with `chronyd` or pod restart |
| DNC list stale / over-broad | Audit DNC list for false entries. Provide self-service removal endpoint |

### Escalation
- Always notify Legal/Compliance team within 15 minutes
- If TCPA violation suspected → halt all outbound dialing immediately

---

## 4. Recording Upload Failures (> 5% rate)

**Alert**: `RecordingUploadFailures` | **Severity**: Warning  
**Impact**: Missing call recordings = compliance audit failure, lost training data.

### Triage
1. Grafana → "Audio Decode Errors Rate" + check `visoora_recording_upload_total{status="failure"}`
2. Loki → `{event="recording_upload_failed"}` → check error message
3. Supabase Dashboard → Storage → check bucket quota and permissions

### Root Causes & Remediation
| Cause | Action |
|-------|--------|
| Supabase Storage quota exceeded | Increase storage plan or archive old recordings. Check `recordings/` local fallback |
| Supabase API rate limit | Implement exponential backoff in `recording-worker`. Spread uploads across workers |
| Recording file corrupt | Check audio decode error rate. If codec issue → fix `encode_pcm_chunk` |
| Network timeout to Supabase | Check recording-worker pod egress. Increase upload timeout from 30s → 60s |
| Bucket permissions revoked | Re-apply RLS policies. Check `SUPABASE_SERVICE_ROLE_KEY` is valid |

### Escalation
- If > 20% failure rate → page Storage team
- Recordings are buffered locally in `recordings/` dir — they are NOT lost. Re-upload after fix.

---

## 5. Pod Capacity Exhaustion (active_calls > 80%)

**Alert**: `HighCallCapacity` | **Severity**: Warning  
**Impact**: New calls may be rejected or queued, increasing connection latency.

### Triage
1. Grafana → "Active Calls by Tenant" → identify which tenant is consuming capacity
2. Kubernetes → `kubectl top pods -l app=visoora` → check CPU/memory
3. HPA → `kubectl get hpa` → verify autoscaler is responding

### Root Causes & Remediation
| Cause | Action |
|-------|--------|
| Organic traffic spike | HPA should auto-scale. If not, manually: `kubectl scale deploy call-orchestrator --replicas=N` |
| Stuck WebSocket sessions | Loki → `{event="ws_connect_success"}` without matching `ws_disconnect`. Kill zombie sessions |
| HPA misconfigured | Check KEDA scaler config. Verify WebSocket connection count metric is being scraped |
| Single tenant abuse | Apply per-tenant rate limit. Contact tenant if on starter plan |
| Memory leak | Check pod restart count. If OOMKilled → increase memory limit or fix leak |

### Escalation
- If at 100% and new calls dropping → page Infrastructure team
- Pre-scale before known campaign launches

---

## Quick Reference

| Grafana URL | `http://grafana:3000/d/visoora-ops-dashboard` |
|-------------|-----------------------------------------------|
| Prometheus  | `http://prometheus:9090` |
| Tempo       | `http://tempo:3200` |
| Loki        | `http://loki:3100` |
| AlertManager | `http://alertmanager:9093` |

### Useful PromQL Queries
```promql
# Current active calls
sum(visoora_active_calls_gauge)

# P95 LLM latency (5m window)
histogram_quantile(0.95, sum(rate(visoora_llm_latency_histogram_bucket[5m])) by (le))

# Compliance blocks per minute
sum(rate(visoora_compliance_blocks_counter[1m])) * 60

# Recording failure rate
sum(rate(visoora_recording_upload_total{status="failure"}[5m])) / sum(rate(visoora_recording_upload_total[5m]))

# Call connection success rate
1 - (sum(rate(visoora_call_connection_total{status="failure"}[5m])) / sum(rate(visoora_call_connection_total[5m])))
```

### Useful Loki Queries
```logql
# All CRITICAL logs
{job="visoora-telephony"} |= "CRITICAL"

# FSM transitions for a specific call
{job="visoora-telephony", event="fsm_transition"} | json | stream_sid="<SID>"

# Compliance blocks in last hour
{job="visoora-telephony", event=~"compliance.*"} | json | line_format "{{.tenant_id}} {{.event}} {{.event_message}}"
```
