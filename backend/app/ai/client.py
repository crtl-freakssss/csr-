import json
import os
import re
from typing import Any
import httpx


class LLMAPIError(Exception):
    """Raised when communication with the LLM API fails due to network, timeout, or provider status."""
    pass


class ModelOutputInvalidError(ValueError):
    """Raised when the LLM returns invalid JSON or content that fails Pydantic schema validation."""
    code: str = "MODEL_OUTPUT_INVALID"

    def __init__(self, message: str, raw_output: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.raw_output = raw_output


class LLMClient:
    """Configurable HTTP client for LLM completions supporting JSON extraction."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.base_url = (base_url or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        timeout_val = timeout_seconds if timeout_seconds is not None else float(os.getenv("LLM_TIMEOUT_SECONDS", "60.0"))
        self.timeout = timeout_val
        self.http_client = http_client

    def _strip_markdown_fences(self, text: str) -> str:
        """Strip markdown code fences (e.g. ```json ... ```)."""
        stripped = text.strip()
        match = re.search(r"^```(?:json)?\s*([\s\S]*?)\s*```$", stripped, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return stripped

    def generate_json(self, prompt: str, system_prompt: str | None = None) -> dict[str, Any]:
        """Send prompt to LLM and parse response into a Python dictionary."""
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
        }

        url = f"{self.base_url}/chat/completions"

        try:
            if self.http_client is not None:
                response = self.http_client.post(url, json=payload, headers=headers, timeout=self.timeout)
            else:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(url, json=payload, headers=headers)
        except httpx.RequestError as exc:
            raise LLMAPIError(f"Network error communicating with LLM API: {exc}") from exc

        if response.status_code != 200:
            raise LLMAPIError(
                f"LLM API returned status {response.status_code}: {response.text}"
            )

        try:
            data = response.json()
            raw_content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise LLMAPIError(f"Unexpected LLM response structure: {response.text}") from exc

        clean_content = self._strip_markdown_fences(raw_content)

        try:
            parsed = json.loads(clean_content)
        except json.JSONDecodeError as exc:
            raise ModelOutputInvalidError(
                f"MODEL_OUTPUT_INVALID: LLM output is not valid JSON ({exc})",
                raw_output=raw_content,
            ) from exc

        if not isinstance(parsed, dict):
            raise ModelOutputInvalidError(
                "MODEL_OUTPUT_INVALID: Root JSON structure must be an object (dict)",
                raw_output=raw_content,
            )

        return parsed
