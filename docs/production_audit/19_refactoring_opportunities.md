# Refactoring Opportunities

To address the Technical Debt, we must execute the following refactoring efforts.

## 1. Provider Abstraction Pattern
Refactor `ai_platform/providers` to use a strategy pattern.
```python
class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, schema: BaseModel) -> BaseModel: pass

class OpenAIProvider(BaseLLMProvider): ...
class ClaudeProvider(BaseLLMProvider): ...
```
This allows the `MissionEngine` to inject any provider and handle failovers automatically.

## 2. Notification Service Abstraction
Refactor `backend/notifications` similarly.
```python
class NotificationProvider(ABC):
    @abstractmethod
    async def notify(self, user_id: str, message: str, template: str): pass

class ResendProvider(NotificationProvider): ...
class InAppProvider(NotificationProvider): ...
```
This allows us to emit a single `DraftApprovedEvent` and have it route to both email and the in-app bell.

## 3. Edge-First Middleware
Rewrite `frontend/middleware.ts` to use `@supabase/ssr` `createServerClient`. It must actively refresh the token and validate the signature on the Edge before rendering the dashboard.

## 4. Pydantic Strict Mode
Remove all custom JSON parsing logic. Rely entirely on OpenAI Structured Outputs with strict Pydantic schemas. If the LLM fails the schema, retry once, then fail the task gracefully.
