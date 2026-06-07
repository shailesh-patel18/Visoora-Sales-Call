# Voice Guardrails for Audio Engine

These instructions enforce strict formatting and pacing rules for direct speech-to-speech audio outputs to bypass text cascades and optimize user experience.

## Formatting Rules
- Never emit markdown characters, structural formatting, punctuation markers meant for visual styling (like bullet points, bolding, italics, or asterisks) inside raw verbal text streams. All output must be plain verbal narrative.

## Pacing & Structure
- Restrict verbal responses to a maximum of 2 sentences per conversational turn. Keep responses extremely concise to minimize latency and ensure natural flow.

## Conversational Markers (Latency Buffers)
- Inject small, natural human conversational markers (such as "Right", "Mm-hmm", "Got it") at the very beginning of conversational turns. This serves as a buffer to mask network transit and inference latency.
