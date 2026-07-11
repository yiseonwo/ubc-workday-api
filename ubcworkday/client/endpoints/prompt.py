"""Prompts — fetching a form field's selectable options."""

from __future__ import annotations

from dataclasses import dataclass

from ubcworkday.client.endpoints.base import Post
from ubcworkday.client.response import Tokens


@dataclass(frozen=True)
class Options(Post):
    """Fetches the selectable options (a prompt) for a form field."""

    template: str = "/ubc/prompt/{context_id}/{field_id}.htmld"

    @staticmethod
    def body(
        field_id: str,
        tokens: Tokens,
        prompt_id: str | None = None,
        filters: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """Build the prompt request body; ``prompt_id``/``filters`` drill a hierarchical picker."""
        body = {
            "_flowExecutionKey": tokens.flow_key,
            "_eventId_prompt": field_id,
            "sessionSecureToken": tokens.secure_token,
        }
        if prompt_id is not None:
            body["prompt"] = prompt_id
        for property_name, instance_id in (filters or {}).items():
            body[f"nlp_{property_name}"] = instance_id
        return body


OPTIONS = Options()
