import json
import os
import re
from datetime import datetime
from typing import Any


class MemoryEngine:
    """A reusable memory engine for EchoDesk.

    MemoryEngine stores, retrieves, updates, deletes, and searches user facts
    in the shared memory.json file. It is designed to be resilient when the
    memory file is missing or corrupted and to preserve conversation history
    alongside stored facts.
    """

    DEFAULT_FILE = "memory.json"

    def __init__(self, file_path: str | None = None):
        """Create a memory engine instance.

        Args:
            file_path: Optional custom path to the JSON file used for memory
                persistence. If omitted, memory.json in the current working
                directory is used.
        """
        self.file_path = file_path or self.DEFAULT_FILE
        self._payload = self._load_payload()

    def remember_fact(self, subject: str, value: str) -> str | None:
        """Store or update a memory fact about the user.

        Args:
            subject: The fact key or subject.
            value: The fact value.

        Returns:
            A human-readable confirmation message, or None when the inputs are
            invalid.
        """
        normalized_subject = self._normalize_subject(subject)
        normalized_value = self._normalize_value(value)

        if not normalized_subject or not normalized_value:
            return None

        existing_index = self._find_fact_index(normalized_subject)
        if existing_index is not None:
            existing = self._payload["facts"][existing_index]
            if existing["value"].strip().lower() == normalized_value.strip().lower():
                return f"I already remember that your {normalized_subject} is {existing['value']}."

            self._payload["facts"][existing_index]["value"] = normalized_value.strip()
            self._payload["facts"][existing_index]["updated_at"] = self._timestamp()
            self._write_payload()
            return f"I updated your {normalized_subject} to {normalized_value}."

        fact = {
            "subject": normalized_subject,
            "value": normalized_value.strip(),
            "created_at": self._timestamp(),
            "updated_at": self._timestamp(),
        }
        self._payload["facts"].append(fact)
        self._write_payload()
        return f"I will remember that your {normalized_subject} is {normalized_value}."

    def retrieve_fact(self, subject: str) -> str | None:
        """Retrieve a previously stored fact by subject.

        Args:
            subject: The fact's subject or key.

        Returns:
            A human-readable summary of the fact, or None if no matching fact is
            found.
        """
        normalized_subject = self._normalize_subject(subject)
        index = self._find_fact_index(normalized_subject)
        if index is None:
            return None

        value = self._payload["facts"][index]["value"]
        return f"Your {normalized_subject} is {value}."

    def update_fact(self, subject: str, value: str) -> str | None:
        """Update an existing memory fact.

        Args:
            subject: The existing fact subject.
            value: The updated fact value.

        Returns:
            A human-readable confirmation message, or None if no existing fact
            matches the subject.
        """
        normalized_subject = self._normalize_subject(subject)
        existing_index = self._find_fact_index(normalized_subject)
        if existing_index is None:
            return None

        self._payload["facts"][existing_index]["value"] = self._normalize_value(value)
        self._payload["facts"][existing_index]["updated_at"] = self._timestamp()
        self._write_payload()
        return f"I updated your {normalized_subject} to {value.strip()}."

    def delete_fact(self, subject: str) -> str | None:
        """Delete a stored memory fact.

        Args:
            subject: The subject of the fact to delete.

        Returns:
            A human-readable confirmation message, or None if the fact is not
            found.
        """
        normalized_subject = self._normalize_subject(subject)
        existing_index = self._find_fact_index(normalized_subject)
        if existing_index is None:
            return None

        removed = self._payload["facts"].pop(existing_index)
        self._write_payload()
        return f"I forgot that your {normalized_subject} is {removed['value']}."

    def search_facts(self, keyword: str) -> str | None:
        """Search stored facts by keyword.

        Args:
            keyword: The search keyword.

        Returns:
            A concise summary of matching memory facts, or None if no matches
            were found.
        """
        normalized_keyword = self._normalize_subject(keyword)
        if not normalized_keyword:
            return None

        matches = []
        for fact in self._payload["facts"]:
            if normalized_keyword in fact["subject"] or normalized_keyword in fact["value"].lower():
                matches.append(fact)

        if not matches:
            return None

        if len(matches) == 1:
            fact = matches[0]
            return f"I remember that your {fact['subject']} is {fact['value']}."

        joined = ". ".join(
            f"Your {fact['subject']} is {fact['value']}" for fact in matches[:3]
        )
        return f"I remember several things: {joined}."

    def is_memory_command(self, command: str) -> bool:
        """Detect whether a command should be handled by memory intelligence.

        Args:
            command: The user's raw command.

        Returns:
            True when the command is related to memory storage, retrieval,
            update, deletion, or search.
        """
        if not isinstance(command, str):
            return False

        normalized = command.lower().strip()
        if not normalized:
            return False

        patterns = [
            r"^(?:remember(?: that)?|please remember)\s+",
            r"^(?:update|change|set|modify)\s+",
            r"^(?:forget|forget about|forget that|delete|remove)\s+",
            r"^(?:search memory for|find in memory|find memory|memory search|memory lookup)\s+",
            r"^(?:what is my|what are my|tell me about my|do i have|what do i know about|what do you know about my)\s+",
        ]

        return any(re.match(pattern, normalized, flags=re.IGNORECASE) for pattern in patterns)

    def process_command(self, command: str) -> str | None:
        """Interpret a natural language command to manage user memory.

        Args:
            command: The user's raw command.

        Returns:
            A response string when the command is related to memory management,
            otherwise None.
        """
        if not isinstance(command, str):
            return None

        normalized = command.lower().strip()
        if not normalized:
            return None

        remember_match = self._match_pattern(
            normalized,
            r"^(?:remember(?: that)?|please remember)\s+(?P<subject>.+?)\s+(?:is|are|was|were|to be|=)\s+(?P<value>.+)$",
        )
        if remember_match:
            return self.remember_fact(remember_match.group("subject"), remember_match.group("value"))

        remember_as_match = self._match_pattern(
            normalized,
            r"^(?:remember(?: that)?|please remember)\s+(?P<subject>.+?)\s+as\s+(?P<value>.+)$",
        )
        if remember_as_match:
            return self.remember_fact(remember_as_match.group("subject"), remember_as_match.group("value"))

        update_match = self._match_pattern(
            normalized,
            r"^(?:update|change|set|modify)\s+(?P<subject>.+?)\s+(?:to|as|=)\s+(?P<value>.+)$",
        )
        if update_match:
            subject = update_match.group("subject")
            value = update_match.group("value")
            response = self.update_fact(subject, value)
            if response:
                return response
            return self.remember_fact(subject, value)

        delete_match = self._match_pattern(
            normalized,
            r"^(?:forget|forget about|forget that|delete|remove)\s+(?:about\s+)?(?P<subject>.+)$",
        )
        if delete_match:
            return self.delete_fact(delete_match.group("subject"))

        search_memory_match = self._match_pattern(
            normalized,
            r"^(?:search memory for|find in memory|find memory|memory search|memory lookup)\s+(?P<keyword>.+)$",
        )
        if search_memory_match:
            return self.search_facts(search_memory_match.group("keyword"))

        retrieve_match = self._match_pattern(
            normalized,
            r"^(?:what is my|what are my|tell me about my|do i have|what do i know about|what do you know about my)\s+(?P<subject>.+)$",
        )
        if retrieve_match:
            response = self.retrieve_fact(retrieve_match.group("subject"))
            if response:
                return response
            return self.search_facts(retrieve_match.group("subject"))

        return None

    def _load_payload(self) -> dict[str, Any]:
        if not os.path.exists(self.file_path):
            return self._default_payload()

        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                payload = json.load(file)
        except (json.JSONDecodeError, ValueError, OSError):
            payload = self._default_payload()
            self._write_payload(payload)
            return payload

        if not isinstance(payload, dict):
            payload = self._default_payload()

        if "history" not in payload or not isinstance(payload["history"], list):
            payload["history"] = []

        if "facts" not in payload or not isinstance(payload["facts"], list):
            payload["facts"] = []

        return payload

    def _write_payload(self, payload: dict[str, Any] | None = None) -> None:
        payload = payload if payload is not None else self._payload
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=4)
        self._payload = payload

    def _default_payload(self) -> dict[str, Any]:
        return {"history": [], "facts": []}

    def _normalize_subject(self, subject: str) -> str:
        normalized = subject.strip().lower()
        normalized = re.sub(r"^my\s+", "", normalized)
        normalized = re.sub(r"\s{2,}", " ", normalized)
        return normalized

    def _normalize_value(self, value: str) -> str:
        return value.strip()

    def _find_fact_index(self, subject: str) -> int | None:
        subject = self._normalize_subject(subject)
        for index, fact in enumerate(self._payload["facts"]):
            if self._normalize_subject(fact.get("subject", "")) == subject:
                return index
        return None

    def _match_pattern(self, text: str, pattern: str) -> re.Match[str] | None:
        return re.match(pattern, text, flags=re.IGNORECASE)

    def _timestamp(self) -> str:
        return datetime.now().isoformat()
