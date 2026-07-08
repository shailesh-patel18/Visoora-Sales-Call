# Code Quality Score

**Score: 60 / 100**

## Strengths
- Separation of concerns between `frontend` and `backend`.
- Use of strong typing in FastAPI (Pydantic models).

## Weaknesses

### 1. Tight LLM Coupling
AI Providers are directly instantiated in services. 
```python
# Bad
client = OpenAI(api_key=...)
response = client.chat.completions.create(...)
```
This makes unit testing nearly impossible without heavy mocking and makes swapping to Anthropic difficult. We need a Repository/Provider pattern.

### 2. Magic Strings and Mock Data
The frontend contains hardcoded mission names, mocked pipeline values (`$68,000`), and hardcoded percentages. These must be replaced with strict API contracts.

### 3. Incomplete Error Handling
Errors are often caught and `console.error`'d on the frontend without notifying the user via a Toast or alerting the engineering team via Sentry.

## Refactoring Targets
- Refactor `ai_platform` to use `BaseLLMProvider`.
- Remove all `setTimeout` mock animations in Next.js.
- Implement strict Pydantic parsing for all LLM outputs (removing fallback JSON parsing hacks).
