"""The form-flow verbs — add / remove / validate / submit events on an open task."""

from __future__ import annotations

from dataclasses import dataclass

from ubcworkday.client.endpoints.base import Post
from ubcworkday.client.response import Choice, Tokens


@dataclass(frozen=True)
class Action(Post):
    """Drives a form flow via ``flowController`` events (add / remove / validate / submit)."""

    template: str = "/ubc/flowController.htmld"

    @staticmethod
    def add_body(
        field_id: str, choice: Choice, tokens: Tokens, pv: bool = False
    ) -> dict[str, str]:
        """Body to add ``choice`` to a field. ``pv=True`` tags it value/primary-value for
        single-select replacement fields (e.g. Evaluate's Program of Study)."""
        body = {
            "_flowExecutionKey": tokens.flow_key,
            "_eventId_add": field_id,
            field_id: choice.id,
            f"{choice.id}_DID": choice.text,
            f"{choice.id}_IID": choice.id,
            "sessionSecureToken": tokens.secure_token,
        }
        if pv:
            body[f"{choice.id}_V"] = "1"
            body[f"{choice.id}_PV"] = "1"
        return body

    @staticmethod
    def remove_body(field_id: str, instance_id: str, tokens: Tokens) -> dict[str, str]:
        """Body to remove an existing value (``instance_id``) from a field."""
        return {
            "_flowExecutionKey": tokens.flow_key,
            "_eventId_remove": field_id,
            field_id: instance_id,
            "sessionSecureToken": tokens.secure_token,
        }

    @staticmethod
    def check_body(field_id: str, tokens: Tokens, value: str = "1") -> dict[str, str]:
        """Body to set + validate a boolean/checkbox field (e.g. Evaluate's 'Is Primary')."""
        return {
            "_flowExecutionKey": tokens.flow_key,
            "_eventId_validate": field_id,
            field_id: value,
            "sessionSecureToken": tokens.secure_token,
        }

    @staticmethod
    def submit_body(event_id: str, tokens: Tokens) -> dict[str, str]:
        """Body to fire a submit event (finishes the flow)."""
        return {
            "_flowExecutionKey": tokens.flow_key,
            "_eventId_submit": event_id,
            "sessionSecureToken": tokens.secure_token,
        }


ACTION = Action()
