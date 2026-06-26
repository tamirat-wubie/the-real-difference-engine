"""Validate public static site deployment health from known generated endpoints."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "https://tamirat-wubie.github.io/the-real-difference-engine/"
DEFAULT_TIMEOUT_SECONDS = 20


@dataclass(frozen=True)
class HealthResult:
    url: str
    ok: bool
    detail: str


class JsonLdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_json_ld = False
        self.payloads: list[str] = []
        self._current: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "script":
            return
        attributes = dict(attrs)
        if attributes.get("type") == "application/ld+json":
            self.in_json_ld = True
            self._current = []

    def handle_data(self, data: str) -> None:
        if self.in_json_ld:
            self._current.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.in_json_ld:
            self.payloads.append("".join(self._current))
            self.in_json_ld = False
            self._current = []


def join_url(base_url: str, path: str = "") -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def planned_urls(base_url: str, comparison_ids: list[str]) -> list[str]:
    urls = [
        join_url(base_url),
        join_url(base_url, "library.json"),
        join_url(base_url, "feed.xml"),
        join_url(base_url, "sitemap.xml"),
        join_url(base_url, "robots.txt"),
    ]
    for comparison_id in comparison_ids[:3]:
        urls.append(join_url(base_url, f"comparisons/{comparison_id}.html"))
        urls.append(join_url(base_url, f"exports/{comparison_id}.md"))
    return urls


def fetch_text(url: str, timeout_seconds: int) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "the-real-difference-engine-health-check"},
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        status = getattr(response, "status", 200)
        if status < 200 or status >= 300:
            raise urllib.error.HTTPError(url, status, f"HTTP {status}", response.headers, None)
        return response.read().decode("utf-8")


def validate_home_html(url: str, html: str) -> HealthResult:
    parser = JsonLdParser()
    parser.feed(html)
    if not parser.payloads:
        return HealthResult(url, False, "missing JSON-LD payload")
    payload = json.loads(parser.payloads[0])
    if payload.get("@type") != "CollectionPage":
        return HealthResult(url, False, "home JSON-LD is not CollectionPage")
    required_fragments = [
        'rel="canonical"',
        'property="og:title"',
        'type="application/rss+xml"',
    ]
    missing = [fragment for fragment in required_fragments if fragment not in html]
    if missing:
        return HealthResult(url, False, f"missing metadata: {', '.join(missing)}")
    return HealthResult(url, True, "home metadata ok")


def validate_library_json(url: str, text: str) -> tuple[HealthResult, list[str]]:
    payload = json.loads(text)
    if payload.get("schema") != "the-real-difference-engine.library.v1":
        return HealthResult(url, False, "unexpected library schema"), []
    comparisons = payload.get("comparisons")
    if not isinstance(comparisons, list) or not comparisons:
        return HealthResult(url, False, "library has no comparisons"), []
    comparison_ids = [str(record["comparison_id"]) for record in comparisons[:3]]
    return HealthResult(url, True, f"library has {payload.get('comparison_count')} comparisons"), comparison_ids


def validate_feed(url: str, text: str) -> HealthResult:
    if '<rss version="2.0">' not in text or "<item>" not in text:
        return HealthResult(url, False, "feed is missing RSS items")
    return HealthResult(url, True, "feed ok")


def validate_sitemap(url: str, text: str) -> HealthResult:
    required_fragments = ["<urlset", "library.json", "feed.xml"]
    missing = [fragment for fragment in required_fragments if fragment not in text]
    if missing:
        return HealthResult(url, False, f"sitemap missing: {', '.join(missing)}")
    return HealthResult(url, True, "sitemap ok")


def validate_robots(url: str, text: str) -> HealthResult:
    if "User-agent: *" not in text or "Sitemap:" not in text:
        return HealthResult(url, False, "robots missing user-agent or sitemap")
    return HealthResult(url, True, "robots ok")


def validate_comparison_html(url: str, html: str) -> HealthResult:
    parser = JsonLdParser()
    parser.feed(html)
    if not parser.payloads:
        return HealthResult(url, False, "missing JSON-LD payload")
    payload = json.loads(parser.payloads[0])
    if payload.get("@type") != "CreativeWork":
        return HealthResult(url, False, "comparison JSON-LD is not CreativeWork")
    if "Download markdown" not in html:
        return HealthResult(url, False, "missing markdown export link")
    return HealthResult(url, True, "comparison page ok")


def validate_markdown_export(url: str, text: str) -> HealthResult:
    if not text.startswith("# ") or "## Final Line" not in text:
        return HealthResult(url, False, "markdown export missing expected headings")
    return HealthResult(url, True, "markdown export ok")


def validate_url(url: str, text: str) -> HealthResult:
    if url.endswith("/library.json"):
        result, _ = validate_library_json(url, text)
        return result
    if url.endswith("/feed.xml"):
        return validate_feed(url, text)
    if url.endswith("/sitemap.xml"):
        return validate_sitemap(url, text)
    if url.endswith("/robots.txt"):
        return validate_robots(url, text)
    if "/comparisons/" in url:
        return validate_comparison_html(url, text)
    if "/exports/" in url:
        return validate_markdown_export(url, text)
    return validate_home_html(url, text)


def run_health_check(base_url: str, timeout_seconds: int) -> list[HealthResult]:
    library_url = join_url(base_url, "library.json")
    try:
        library_text = fetch_text(library_url, timeout_seconds)
        library_result, comparison_ids = validate_library_json(library_url, library_text)
    except Exception as exc:  # noqa: BLE001
        return [HealthResult(library_url, False, f"{type(exc).__name__}: {exc}")]

    results = [library_result]
    urls = [url for url in planned_urls(base_url, comparison_ids) if url != library_url]
    for url in urls:
        try:
            text = fetch_text(url, timeout_seconds)
            results.append(validate_url(url, text))
        except Exception as exc:  # noqa: BLE001
            results.append(HealthResult(url, False, f"{type(exc).__name__}: {exc}"))
    return results


def render_results(results: list[HealthResult]) -> str:
    lines = ["# Site Health Check", ""]
    for result in results:
        status = "OK" if result.ok else "BROKEN"
        lines.append(f"- {status} {result.url} - {result.detail}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate deployed public site health.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args()

    results = run_health_check(args.base_url, args.timeout)
    print(render_results(results))
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
