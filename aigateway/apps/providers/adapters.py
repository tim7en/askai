"""
Provider adapters: each adapter implements a common interface for AI generation.
"""

import abc
import logging

import httpx

logger = logging.getLogger(__name__)


class BaseProviderAdapter(abc.ABC):
    """Interface for provider adapters."""

    @abc.abstractmethod
    def generate(
        self,
        api_key: str,
        model: str,
        prompt: str,
        system: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> dict:
        """
        Generate a response from the provider.

        Returns dict with keys:
        - output_text: str
        - units_in: int (input tokens/units)
        - units_out: int (output tokens/units)
        """
        ...


class OpenAIAdapter(BaseProviderAdapter):
    """Real adapter for OpenAI API."""

    BASE_URL = "https://api.openai.com/v1/chat/completions"

    def generate(self, api_key, model, prompt, system="", max_tokens=2048, temperature=0.7):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = httpx.post(
            self.BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

        choice = data.get("choices", [{}])[0]
        usage = data.get("usage", {})

        return {
            "output_text": choice.get("message", {}).get("content", ""),
            "units_in": usage.get("prompt_tokens", 0),
            "units_out": usage.get("completion_tokens", 0),
        }


class StubAdapter(BaseProviderAdapter):
    """Stub adapter for providers not yet integrated (Anthropic, Google, OSS)."""

    def generate(self, api_key, model, prompt, system="", max_tokens=2048, temperature=0.7):
        # TODO: Replace with real API integration when provider keys/docs are available
        return {
            "output_text": f"[STUB] Response from {model}. Prompt: {prompt[:100]}...",
            "units_in": len(prompt.split()),
            "units_out": 20,
        }


# Registry of adapters
_ADAPTERS = {
    "openai": OpenAIAdapter(),
    "anthropic": StubAdapter(),
    "google": StubAdapter(),
    "oss": StubAdapter(),
}


def get_adapter(provider_slug: str) -> BaseProviderAdapter:
    adapter = _ADAPTERS.get(provider_slug)
    if not adapter:
        logger.warning(f"No adapter for provider '{provider_slug}', using stub")
        return StubAdapter()
    return adapter
