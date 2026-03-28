from arxiv_bot.models import PaperRecord
from arxiv_bot.skills.inspire_client import InspireClient


def test_inspire_client_builds_identifier_urls() -> None:
    """Build INSPIRE lookup URLs with format=bibtex query parameter."""
    client = InspireClient(base_url="https://inspirehep.net/api")
    assert client._arxiv_url("1706.03762") == "https://inspirehep.net/api/arxiv/1706.03762?format=bibtex"
    assert (
        client._doi_url("10.1038/nature14539")
        == "https://inspirehep.net/api/doi/10.1038%2Fnature14539?format=bibtex"
    )


def test_inspire_client_prefers_arxiv_before_doi() -> None:
    """Query arXiv first and return early when arXiv BibTeX is found."""

    class FakeInspireClient(InspireClient):
        """Override transport to return deterministic payloads per URL."""

        def _fetch_text(self, url: str) -> str | None:
            """Return BibTeX only for arXiv URL requests."""
            if "/arxiv/" in url:
                return "@article{fromArxiv,\n  title={X}\n}"
            return "@article{fromDoi,\n  title={Y}\n}"

    client = FakeInspireClient()
    record = PaperRecord(
        source_link="https://arxiv.org/abs/1706.03762",
        arxiv_id="1706.03762",
        doi="10.1038/nature14539",
    )
    result = client.fetch_bibtex(record)
    assert result is not None
    assert "fromArxiv" in result


def test_inspire_client_returns_none_when_not_found() -> None:
    """Return None when neither arXiv nor DOI lookup yields BibTeX."""

    class FakeInspireClient(InspireClient):
        """Override transport to simulate not-found lookups."""

        def _fetch_text(self, url: str) -> str | None:
            """Return None for all lookup URLs."""
            _ = url
            return None

    client = FakeInspireClient()
    record = PaperRecord(source_link="https://example.org/paper", doi="10.1/abc")
    assert client.fetch_bibtex(record) is None
