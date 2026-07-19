import json
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError


class InternetEngine:
    """A minimal internet search engine for EchoDesk.

    InternetEngine performs a concise web search using a public search
    endpoint and returns human-readable summaries. It is independent,
    reusable, and built to fail gracefully when the network or service is
    unavailable.
    """

    API_URL = "https://api.duckduckgo.com/"

    def __init__(self, timeout: float = 5.0):
        """Initialize the internet engine.

        Args:
            timeout: The maximum number of seconds to wait for a remote
                response.
        """
        self.timeout = float(timeout)

    def search(self, query: str) -> str | None:
        """Search the internet for a concise summary.

        Args:
            query: The query text to search.

        Returns:
            A human-readable summary string when a valid response is
            available, or None when the query is empty or no useful result
            could be obtained.
        """
        if not isinstance(query, str) or not query.strip():
            return None

        url = self._build_url(query)

        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "EchoDesk InternetEngine/1.0"},
            )
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                if response.status != 200:
                    return self._format_error(
                        "The search service returned an unexpected status code."
                    )

                payload = response.read()
                data = json.loads(payload.decode("utf-8", errors="ignore"))

        except HTTPError:
            return self._format_error(
                "The search service could not complete the request."
            )
        except URLError:
            return self._format_error(
                "I could not reach the internet. Please check your connection."
            )
        except json.JSONDecodeError:
            return self._format_error(
                "The search service returned an invalid response."
            )
        except ValueError:
            return self._format_error(
                "The search service responded with corrupt data."
            )

        return self._summarize_result(data)

    def _build_url(self, query: str) -> str:
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }
        return f"{self.API_URL}?{urllib.parse.urlencode(params)}"

    def _summarize_result(self, data: dict) -> str | None:
        if not isinstance(data, dict):
            return self._format_error(
                "The search service returned an unexpected format."
            )

        answer = self._extract_field(data, "Answer")
        if answer:
            return self._summarize_text(answer)

        abstract = self._extract_field(data, "AbstractText")
        if abstract:
            return self._summarize_text(abstract)

        related = self._extract_related_topics(data)
        if related:
            return self._summarize_text(related)

        if self._extract_field(data, "Redirect"):
            return "I found a related result but could not summarize it cleanly."

        return self._format_error("I could not find a useful answer from the web.")

    def _extract_field(self, data: dict, key: str) -> str | None:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value
        return None

    def _extract_related_topics(self, data: dict) -> str | None:
        topics = data.get("RelatedTopics")
        if not isinstance(topics, list):
            return None

        for item in topics:
            if isinstance(item, dict):
                text = item.get("Text")
                if isinstance(text, str) and text.strip():
                    return text.strip()

                topics_list = item.get("Topics")
                if isinstance(topics_list, list):
                    for child in topics_list:
                        child_text = child.get("Text")
                        if isinstance(child_text, str) and child_text.strip():
                            return child_text.strip()

        return None

    def _summarize_text(self, text: str) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= 400:
            return normalized

        sentences = normalized.split(". ")
        summary = []
        for sentence in sentences:
            if not sentence:
                continue
            candidate = ". ".join(summary + [sentence])
            if len(candidate) > 350:
                break
            summary.append(sentence)

        if summary:
            result = ". ".join(summary).strip()
            if not result.endswith("."):
                result = f"{result}."
            return result

        return f"{normalized[:347].rstrip()}..."

    def _format_error(self, message: str) -> str:
        return message.strip()
