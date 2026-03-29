from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class LLMClient:
    """Provide a minimal interface for text-generation calls used by skills."""

    model: str = "gpt-4.1-mini"
    provider: str = "openai"

    def generate(self, prompt: str, max_tokens: int = 400) -> str:
        """Generate text from a prompt using the configured provider."""
        if self.provider == "openai":
            return self._generate_openai(prompt, max_tokens=max_tokens)
        return ""

    def _generate_openai(self, prompt: str, max_tokens: int = 400) -> str:
        """Generate text via the OpenAI Responses API when credentials exist."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return ""

        try:
            from openai import OpenAI  # type: ignore
        except Exception:
            return ""

        try:
            client = OpenAI(api_key=api_key)
            configured_model = os.getenv("ARXIV_BOT_LLM_MODEL", self.model)
            model_candidates = [configured_model, "gpt-4.1-mini", "gpt-4o-mini"]

            seen: set[str] = set()
            for candidate in model_candidates:
                if candidate in seen:
                    continue
                seen.add(candidate)

                response = client.responses.create(
                    model=candidate,
                    input=prompt,
                    max_output_tokens=max_tokens,
                )
                output_text = getattr(response, "output_text", None)
                if isinstance(output_text, str) and output_text.strip():
                    return output_text.strip()
        except Exception:
            return ""

        return ""
