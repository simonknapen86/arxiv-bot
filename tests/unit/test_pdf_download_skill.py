from pathlib import Path

from arxiv_bot.models import PaperRecord
from arxiv_bot.skills.pdf_download import pdf_download_skill


def _fake_pdf_fetcher(_: str) -> bytes:
    """Return deterministic PDF bytes for successful download tests."""
    return b"%PDF-1.4\n% fake\n%%EOF\n"


def _fake_non_pdf_fetcher(_: str) -> bytes:
    """Return non-PDF bytes for negative validation tests."""
    return b"<html>not-a-pdf</html>"


def test_pdf_download_saves_verified_arxiv_record(tmp_path: Path) -> None:
    """Download a verified arXiv record and persist it under deterministic filename."""
    records = [
        PaperRecord(
            source_link="https://arxiv.org/abs/1706.03762",
            arxiv_id="1706.03762",
            verified=True,
            status="verified",
        )
    ]

    downloaded = pdf_download_skill(records, output_dir=tmp_path, fetch_pdf=_fake_pdf_fetcher)
    assert len(downloaded) == 1
    assert downloaded[0].status == "downloaded"
    assert downloaded[0].local_pdf_path is not None
    assert downloaded[0].local_pdf_path.endswith("1706_03762.pdf")
    assert Path(downloaded[0].local_pdf_path).exists()


def test_pdf_download_skips_unverified_records(tmp_path: Path) -> None:
    """Skip records that are not verified before download."""
    records = [
        PaperRecord(
            source_link="https://arxiv.org/abs/1706.03762",
            arxiv_id="1706.03762",
            verified=False,
            status="discovered",
        )
    ]

    downloaded = pdf_download_skill(records, output_dir=tmp_path, fetch_pdf=_fake_pdf_fetcher)
    assert downloaded == []


def test_pdf_download_rejects_non_pdf_payload(tmp_path: Path) -> None:
    """Reject download payloads that do not match the PDF signature."""
    records = [
        PaperRecord(
            source_link="https://arxiv.org/abs/1706.03762",
            arxiv_id="1706.03762",
            verified=True,
            status="verified",
        )
    ]

    downloaded = pdf_download_skill(records, output_dir=tmp_path, fetch_pdf=_fake_non_pdf_fetcher)
    assert downloaded == []


def test_pdf_download_uses_explicit_pdf_url_when_available(tmp_path: Path) -> None:
    """Prefer an explicit pdf_url field over derived source URLs."""
    seen_urls: list[str] = []

    def recorder(url: str) -> bytes:
        """Capture requested URL while returning deterministic PDF bytes."""
        seen_urls.append(url)
        return b"%PDF-1.4\n%%EOF\n"

    records = [
        PaperRecord(
            source_link="https://doi.org/10.1038/nature14539",
            doi="10.1038/nature14539",
            pdf_url="https://example.org/paper.pdf",
            verified=True,
            status="verified",
        )
    ]

    downloaded = pdf_download_skill(records, output_dir=tmp_path, fetch_pdf=recorder)
    assert len(downloaded) == 1
    assert seen_urls == ["https://example.org/paper.pdf"]


def test_pdf_download_uses_doi_source_link_as_fallback(tmp_path: Path) -> None:
    """Use DOI source links as fallback PDF targets when no pdf_url is provided."""
    seen_urls: list[str] = []

    def recorder(url: str) -> bytes:
        """Capture requested URL while returning deterministic PDF bytes."""
        seen_urls.append(url)
        return b"%PDF-1.4\n%%EOF\n"

    records = [
        PaperRecord(
            source_link="https://doi.org/10.1038/nature14539",
            doi="10.1038/nature14539",
            verified=True,
            status="verified",
        )
    ]

    downloaded = pdf_download_skill(records, output_dir=tmp_path, fetch_pdf=recorder)
    assert len(downloaded) == 1
    assert seen_urls == ["https://doi.org/10.1038/nature14539"]
