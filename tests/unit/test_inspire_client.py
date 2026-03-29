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


def test_inspire_client_fetches_seed_abstract() -> None:
    """Extract abstract text from a seed record metadata payload."""

    class FakeInspireClient(InspireClient):
        """Return deterministic JSON metadata for seed lookup."""

        def _fetch_json(self, url: str) -> dict[str, object] | None:
            """Return a seed payload for arXiv lookup URLs."""
            if "/arxiv/1706.03762" in url:
                return {
                    "id": "12345",
                    "metadata": {
                        "abstracts": [{"value": "Transformer abstract text."}],
                    },
                }
            return None

    client = FakeInspireClient()
    record = PaperRecord(source_link="https://arxiv.org/abs/1706.03762", arxiv_id="1706.03762")
    assert client.fetch_abstract(record) == "Transformer abstract text."


def test_inspire_client_fetches_related_citing_and_references() -> None:
    """Collect both citing and referenced papers from INSPIRE payloads."""

    class FakeInspireClient(InspireClient):
        """Provide deterministic INSPIRE JSON responses for relation traversal."""

        def _fetch_json(self, url: str) -> dict[str, object] | None:
            """Return record and search payloads for related-paper fetching."""
            if "/arxiv/1706.03762" in url:
                return {
                    "id": "12345",
                    "metadata": {
                        "references": [
                            {"record": {"$ref": "https://inspirehep.net/api/literature/9001"}}
                        ]
                    },
                }
            if "/literature?" in url and "refersto+recid%3A12345" in url:
                return {
                    "hits": {
                        "hits": [
                            {
                                "id": "8001",
                                "metadata": {
                                    "titles": [{"title": "Citing transformer paper"}],
                                    "abstracts": [{"value": "Attention and transformer variants."}],
                                    "arxiv_eprints": [{"value": "2101.00001"}],
                                    "authors": [{"full_name": "A. Author"}],
                                    "earliest_date": "2021-01-15",
                                },
                            }
                        ]
                    }
                }
            if "/literature/9001" in url:
                return {
                    "id": "9001",
                    "metadata": {
                        "titles": [{"title": "Referenced optimization paper"}],
                        "abstracts": [{"value": "Optimization and training dynamics."}],
                        "dois": [{"value": "10.1000/xyz"}],
                        "authors": [{"full_name": "B. Author"}],
                        "earliest_date": "2020-06-01",
                    },
                }
            return None

    client = FakeInspireClient()
    seed = PaperRecord(source_link="https://arxiv.org/abs/1706.03762", arxiv_id="1706.03762")
    related = client.fetch_related_papers(seed, max_citing=5, max_references=5)

    assert len(related) == 2
    assert any(record.arxiv_id == "2101.00001" for record in related)
    assert any(record.doi == "10.1000/xyz" for record in related)
