"""FPT Gemma4 AI client using OpenAI-compatible SDK. Production-ready implementation."""
import os
from typing import AsyncGenerator, Optional

from openai import AsyncOpenAI

FPT_BASE_URL = "https://mkp-api.fptcloud.com"
FPT_MODEL = "gemma-4-31B-it"


def _normalize_base_url(raw_url: str) -> str:
    """Normalize API URL into an OpenAI-compatible base URL."""
    url = raw_url.strip().rstrip("/")
    if not url:
        return FPT_BASE_URL

    # Accept endpoint-style URL and convert to base URL for AsyncOpenAI.
    if url.endswith("/chat/completions"):
        return url[: -len("/chat/completions")]
    return url


class FPTAIClient:
    """Async client for FPT's Gemma4 model via OpenAI-compatible API."""

    def __init__(self):
        """Initialize the FPT AI client."""
        # Backward-compatible env lookup: support both FPT_API and FPT_API_KEY.
        api_key = (os.getenv("FPT_API", "") or os.getenv("FPT_API_KEY", "")).strip()

        raw_base_url = (
            os.getenv("FPT_BASE_URL", "")
            or os.getenv("FPT_API_URL", "")
            or FPT_BASE_URL
        )
        base_url = _normalize_base_url(raw_base_url)
        model = os.getenv("FPT_MODEL", FPT_MODEL).strip()

        if not api_key:
            raise ValueError("FPT_API or FPT_API_KEY environment variable is not set")

        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        """Send chat request and return the assistant's text response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens in response

        Returns:
            Assistant's text response
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )

            if response.choices and response.choices[0].message:
                return response.choices[0].message.content or ""

            return ""

        except Exception as e:
            print(f"[FPTAIClient.chat] Error: {e}")
            raise

    async def chat_stream(
        self,
        messages: list[dict],
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Send chat request and stream text chunks.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Yields:
            Text chunks from the response
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            print(f"[FPTAIClient.chat_stream] Error: {e}")
            raise

    async def close(self) -> None:
        """Close the async client."""
        await self.client.close()


# Global singleton instance
_client: Optional[FPTAIClient] = None


def get_ai_client() -> FPTAIClient:
    """Get or create the global FPT AI client instance."""
    global _client
    if _client is None:
        _client = FPTAIClient()
    return _client


async def close_ai_client() -> None:
    """Close the global AI client."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
