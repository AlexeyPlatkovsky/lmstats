"""Browser tests that execute the shipped dashboard JavaScript."""

import json
import threading
from datetime import datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest


pytestmark = pytest.mark.browser


@pytest.fixture()
def ui_url():
    root = Path(__file__).resolve().parents[1] / "static"

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)

        def log_message(self, format, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()


def _history(now):
    return {
        "range": "24h",
        "generatedAt": now.isoformat().replace("+00:00", "Z"),
        "series": [{
            "model": "alpha",
            "points": [
                {
                    "timestamp": (now - timedelta(minutes=90)).isoformat().replace("+00:00", "Z"),
                    "avgTokensPerSecond": 52.0,
                    "count": 1,
                },
                {
                    "timestamp": (now - timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
                    "avgTokensPerSecond": 72.0,
                    "count": 1,
                },
                {
                    "timestamp": now.isoformat().replace("+00:00", "Z"),
                    "avgTokensPerSecond": 62.0,
                    "count": 1,
                },
            ],
        }],
    }


def _open_with_legacy_api(page, ui_url, now):
    page.add_init_script("window.EventSource = class { constructor() {} close() {} };")
    history = _history(now)
    requests = []

    def dashboard(route):
        requests.append(route.request.url)
        route.fulfill(status=404, content_type="application/json", body='{"detail":"Not Found"}')

    page.route("**/api/dashboard?**", dashboard)
    page.route(
        "**/api/history?**",
        lambda route: route.fulfill(content_type="application/json", body=json.dumps(history)),
    )
    page.goto(ui_url)
    page.locator("#graphSvg circle").first.wait_for()
    return requests


def test_legacy_fallback_is_honest_and_handles_historical_navigation(page, ui_url):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    requests = _open_with_legacy_api(page, ui_url, now)

    assert page.locator("#graphSvg circle").count() == 2
    unavailable = "Detailed rows require the dashboard API. Restart LM Speed Viewer to enable them."
    assert unavailable == page.locator("#recentRows").inner_text()
    assert unavailable == page.locator("#summaryRows").inner_text()

    page.get_by_role("button", name="‹ PREV").click()
    assert len(requests) >= 2
    page.wait_for_function("document.querySelectorAll('#graphSvg circle').length === 1")
    assert page.locator("#graphSvg circle").count() == 1


def test_graph_ticks_tooltip_and_resize_execute_in_the_browser(page, ui_url):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _open_with_legacy_api(page, ui_url, now)

    labels = page.locator("#graphSvg text").all_text_contents()
    assert len(labels) >= 9  # four y-axis labels plus five x-axis time labels
    assert labels[:4] == ["0", "30", "60", "90"]

    page.locator("#graphSvg circle").last.hover()
    assert "Bucket:" in page.locator("#tooltip").inner_text()
    bounds = page.evaluate("""() => ({
        tooltip: document.querySelector('#tooltip').getBoundingClientRect().toJSON(),
        graph: document.querySelector('#graphArea').getBoundingClientRect().toJSON(),
        viewBox: document.querySelector('#graphSvg').getAttribute('viewBox'),
    })""")
    assert bounds["tooltip"]["right"] <= bounds["graph"]["right"]

    page.set_viewport_size({"width": 1100, "height": 720})
    page.wait_for_timeout(50)
    changed = page.locator("#graphSvg").get_attribute("viewBox")
    assert changed != bounds["viewBox"]


def test_mobile_recent_table_and_status_detail_use_the_shipped_ui(page, ui_url):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _open_with_legacy_api(page, ui_url, now)
    assert page.locator("#nextBtn").is_disabled()
    next_opacity = page.locator("#nextBtn").evaluate("element => getComputedStyle(element).opacity")
    assert float(next_opacity) < 1
    page.set_viewport_size({"width": 390, "height": 844})

    layout = page.evaluate("""() => {
        const panel = document.querySelector('.recent');
        return { overflow: getComputedStyle(panel).overflowX,
                 scrollWidth: panel.scrollWidth, clientWidth: panel.clientWidth };
    }""")
    assert layout["overflow"] in {"auto", "scroll"}
    assert layout["scrollWidth"] > layout["clientWidth"]

    page.evaluate("""() => render({
        collector: 'disconnected', detail: 'lms log stream exited (code 2)',
        prediction: { tokensPerSecond: 1, timeToFirstTokenSec: 1.5 },
    })""")
    assert page.locator("#statusText").inner_text() == "LM Studio: DISCONNECTED"
    assert page.locator("#ttft").inner_text() == "1.5 s"


def test_visible_ranges_and_recent_time_column(page, ui_url):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _open_with_legacy_api(page, ui_url, now)
    assert page.locator("[data-range]").all_text_contents() == ["5m", "15m", "1h", "24h"]
    assert page.locator(".recent-table col").first.get_attribute("style") == "width:17%"


def test_live_prediction_refreshes_the_current_dashboard_window(page, ui_url):
    """An SSE prediction must move the live window forward before refetching."""
    page.add_init_script("""
        window.EventSource = class {
            constructor() { window.latestEventSource = this; }
            close() {}
        };
    """)
    event_timestamp = 0
    dashboard_requests = []

    def dashboard(route):
        at = parse_qs(urlparse(route.request.url).query)["at"][0]
        dashboard_requests.append(at)
        request_timestamp = datetime.fromisoformat(
            at.replace("Z", "+00:00")
        ).timestamp() * 1000
        if event_timestamp and request_timestamp >= event_timestamp:
            payload = {
                "history": {"series": [{"model": "alpha", "points": [{
                    "timestamp": datetime.fromtimestamp(
                        event_timestamp / 1000, timezone.utc).isoformat().replace("+00:00", "Z"),
                    "avgTokensPerSecond": 8.42, "count": 1,
                }]}]},
                "recent": [{"modelIdentifier": "alpha", "timestampMs": event_timestamp,
                            "tokensPerSecond": 8.42}],
                "summary": [],
            }
        else:
            payload = {"history": {"series": []}, "recent": [], "summary": []}
        route.fulfill(content_type="application/json", body=json.dumps(payload))

    page.route("**/api/dashboard?**", dashboard)
    page.goto(ui_url)
    page.locator("#recentRows").get_by_text("No generations recorded yet.").wait_for()
    page.wait_for_timeout(20)
    event_timestamp = page.evaluate("""() => {
        const timestampMs = Date.now();
        window.latestEventSource.onmessage({data: JSON.stringify({
            collector: "connected",
            prediction: {modelIdentifier: "alpha", tokensPerSecond: 8.42, timestampMs},
        })});
        return timestampMs;
    }""")

    page.locator("#recentRows").get_by_text("8.4").wait_for()
    assert page.locator("#speed").inner_text() == "8.4"
    assert "Aug" in page.locator("#recentRows td").first.inner_text()
    assert page.locator("#graphSvg circle").count() == 1
    assert len(dashboard_requests) >= 2
    assert dashboard_requests[-1] > dashboard_requests[0]
