import asyncio
from typing import Awaitable, Callable, Optional, TypeVar

T = TypeVar("T")


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    attempts: int = 3,
    base_delay_seconds: float = 0.25,
    retry_if: Optional[Callable[[T], bool]] = None,
) -> T:
    """
    Retry a small async operation with exponential backoff.
    `retry_if` returns True when a successful response should still be retried.
    """
    last_error: Optional[BaseException] = None

    for attempt in range(1, attempts + 1):
        try:
            result = await operation()
            if retry_if and retry_if(result) and attempt < attempts:
                await asyncio.sleep(base_delay_seconds * (2 ** (attempt - 1)))
                continue
            return result
        except Exception as exc:
            last_error = exc
            if attempt >= attempts:
                raise
            await asyncio.sleep(base_delay_seconds * (2 ** (attempt - 1)))

    if last_error:
        raise last_error
    raise RuntimeError("retry_async exited without a result")
