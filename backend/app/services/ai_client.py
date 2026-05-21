import aiohttp
from fastapi import HTTPException, status

from app.config import get_settings


class DeepSeekChatError(RuntimeError):
    """Raised when the DeepSeek chat API cannot return a usable response."""


async def call_deepseek_chat(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.35,
    max_tokens: int = 900,
) -> dict:
    settings = get_settings()
    if not settings.deepseek_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="暂时无法连接 AI，请稍后再试",
        )

    url = f"{settings.deepseek_base_url.rstrip('/')}/chat/completions"
    timeout = aiohttp.ClientTimeout(total=settings.deepseek_timeout_seconds)
    body = {
        "model": settings.deepseek_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                url,
                headers={
                    "Authorization": f"Bearer {settings.deepseek_api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            ) as response:
                data = await response.json(content_type=None)
                if response.status >= 400:
                    raise DeepSeekChatError("DeepSeek returned an error status")

                choices = data.get("choices") if isinstance(data, dict) else None
                content = choices[0].get("message", {}).get("content") if choices else ""
                if not content:
                    raise DeepSeekChatError("DeepSeek returned an empty response")

                return {
                    "reply": str(content).strip(),
                    "model": str(data.get("model") or settings.deepseek_model),
                }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="暂时无法连接 AI，请稍后再试",
        ) from exc
