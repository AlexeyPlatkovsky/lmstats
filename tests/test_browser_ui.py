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
    root = Path(__file__).resolve().parents[1]

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)

        def log_message(self, format, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/static/"
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
    assert page.locator("[data-range]").all_text_contents() == ["5m", "15m", "1h", "24h", "1mo"]
    assert page.locator(".recent-table col").first.get_attribute("style") == "width:17%"


def test_monthly_graph_and_interactive_vertical_legend(page, ui_url):
    """Monthly samples use an ordinal axis; legend controls filter and highlight lines."""
    page.add_init_script("window.EventSource = class { constructor() {} close() {} };")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    history = {
        "range": "1mo",
        "series": [{
            "model": model,
            "points": [{
                "timestamp": (now - timedelta(minutes=10 - index)).isoformat()
                .replace("+00:00", "Z"),
                "avgTokensPerSecond": speed,
                "count": 1,
            } for index, speed in enumerate(speeds)],
        } for model, speeds in (("alpha", [10, 20]), ("beta", [30, 40, 50]))],
    }
    page.route(
        "**/api/dashboard?**",
        lambda route: route.fulfill(content_type="application/json", body=json.dumps({
            "range": "1mo", "history": history, "recent": [], "summary": [],
        })),
    )
    page.goto(ui_url)
    page.get_by_role("button", name="1mo").click()
    page.get_by_role("button", name="alpha").wait_for()

    assert page.locator("#graphSvg text").all_text_contents()[-10:] == [
        str(value) for value in range(1, 11)
    ]
    legend = page.locator("#legend")
    assert legend.evaluate("element => getComputedStyle(element).flexDirection") == "column"

    alpha = page.get_by_role("button", name="alpha")
    alpha.hover()
    assert page.locator('#graphSvg path[data-model="alpha"]').get_attribute("stroke-width") == "3"
    alpha.hover(position={"x": 1, "y": 1})
    page.mouse.move(1200, 100)
    assert page.locator('#graphSvg path[data-model="alpha"]').get_attribute("stroke-width") == "1.5"

    alpha.click()
    assert alpha.get_attribute("aria-pressed") == "false"
    assert page.locator('#graphSvg path[data-model="alpha"]').count() == 0
    decoration = alpha.evaluate("element => getComputedStyle(element).textDecorationLine")
    assert decoration == "line-through"


def test_model_palette_cycles_after_six_accessible_colours(page, ui_url):
    """Model order determines the first six graph colours without unchecked shades."""
    page.add_init_script("window.EventSource = class { constructor() {} close() {} };")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    history = {
        "series": [{
            "model": f"model-{index}",
            "points": [{
                "timestamp": now.isoformat().replace("+00:00", "Z"),
                "avgTokensPerSecond": 10 + index,
                "count": 1,
            }],
        } for index in range(7)],
    }
    page.route(
        "**/api/dashboard?**",
        lambda route: route.fulfill(content_type="application/json", body=json.dumps({
            "history": history, "recent": [], "summary": [],
        })),
    )
    page.goto(ui_url)
    page.locator("#legend .swatch").last.wait_for()

    colours = page.locator("#legend .swatch").evaluate_all(
        "elements => elements.map(element => element.style.background)"
    )
    assert colours[:6] == [
        "rgb(56, 255, 20)", "rgb(229, 184, 0)", "rgb(57, 197, 207)",
        "rgb(188, 140, 255)", "rgb(247, 120, 186)", "rgb(88, 166, 255)",
    ]
    assert colours[6] == colours[0]


def test_penpot_desktop_layout_and_accessible_theme_switch(page, ui_url):
    """The shipped UI preserves the Penpot desktop composition and theme control."""
    page.set_viewport_size({"width": 1280, "height": 720})
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _open_with_legacy_api(page, ui_url, now)

    layout = page.evaluate("""() => {
        const box = selector => document.querySelector(selector).getBoundingClientRect().toJSON();
        return {app: box('.app'), live: box('.live'), recent: box('.recent'),
                chart: box('.chart'), summary: box('.summary')};
    }""")
    assert layout["app"]["width"] == 1280
    assert layout["live"]["width"] == 390
    assert layout["live"]["height"] == layout["recent"]["height"] == 260
    assert layout["summary"]["height"] == 100
    assert layout["chart"]["width"] == layout["summary"]["width"] == 1248
    assert page.get_by_role("heading", name="GENERATION SPEED").count() == 1

    toggle = page.get_by_role("button", name="Switch to light theme")
    toggle.focus()
    page.keyboard.press("Enter")
    assert page.locator("html").get_attribute("data-theme") == "light"
    assert page.get_by_role("button", name="Switch to dark theme").count() == 1
    assert page.evaluate("localStorage.getItem('theme')") == "light"


def test_theme_text_colours_meet_wcag_aa_contrast(page, ui_url):
    """Both theme palettes keep all text-bearing UI treatments at 4.5:1 or higher."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _open_with_legacy_api(page, ui_url, now)

    contrasts = page.evaluate("""() => {
        const luminance = color => {
            const rgb = color.match(/\\d+(?:\\.\\d+)?/g).slice(0, 3).map(Number).map(value => {
                value /= 255;
                return value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4;
            });
            return .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2];
        };
        const ratio = (foreground, background) => {
            const [light, dark] = [luminance(foreground), luminance(background)]
                .sort((a, b) => b - a);
            return (light + .05) / (dark + .05);
        };
        const pairs = [
            ['.title', 'body'], ['.status', 'body'], ['.range-btn', '.range-btn'],
            ['.selected', 'body'], ['.nav-btn', 'body'], ['.timestamp', '.live'],
            ['.metric', '.live'], ['.value', '.live'], ['.panel-title', '.recent'],
            ['.data-table th', '.recent'], ['.data-table td', '.recent'],
            ['.empty-text', '.graph'], ['.legend', 'body'], ['.tooltip', '.tooltip'],
        ];
        return pairs.map(([foreground, background]) => {
            const fg = getComputedStyle(document.querySelector(foreground)).color;
            const bg = getComputedStyle(document.querySelector(background)).backgroundColor;
            return {foreground, background, ratio: ratio(fg, bg)};
        });
    }""")
    assert all(item["ratio"] >= 4.5 for item in contrasts), contrasts

    page.get_by_role("button", name="Switch to light theme").click()
    light_contrasts = page.evaluate("""() => {
        const luminance = color => {
            const rgb = color.match(/\\d+(?:\\.\\d+)?/g).slice(0, 3).map(Number).map(value => {
                value /= 255;
                return value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4;
            });
            return .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2];
        };
        const ratio = (foreground, background) => {
            const [light, dark] = [luminance(foreground), luminance(background)]
                .sort((a, b) => b - a);
            return (light + .05) / (dark + .05);
        };
        return [['.title', 'body'], ['.status', 'body'], ['.range-btn', '.range-btn'],
                ['.selected', 'body'], ['.metric', '.live'], ['.value', '.live'],
                ['.data-table th', '.recent'], ['.data-table td', '.recent'],
                ['.empty-text', '.graph'], ['.legend', 'body'], ['.tooltip', '.tooltip']]
            .map(([foreground, background]) => ({foreground, background,
                ratio: ratio(getComputedStyle(document.querySelector(foreground)).color,
                             getComputedStyle(document.querySelector(background)).backgroundColor)}));
    }""")
    assert all(item["ratio"] >= 4.5 for item in light_contrasts), light_contrasts


def test_theme_colours_meet_wcag_aa_for_all_rendered_treatments(page, ui_url):
    """Text, boundaries, disabled states, and graph series stay readable in both themes."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _open_with_legacy_api(page, ui_url, now)

    page.evaluate("""() => {
        hiddenModels.clear();
        setTheme('dark');
        const points = graphState.data.series[0].points;
        renderGraph({series: Array.from({length: 6}, (_, index) => ({
            model: `model-${index}`, points,
        }))}, graphState.emptyMessage);
    }""")

    for theme in ("dark", "light"):
        if theme == "light":
            page.evaluate("hiddenModels.clear()")
            page.get_by_role("button", name="Switch to light theme").click()
        treatments = page.evaluate("""() => {
            const rgb = color => {
                const sample = document.createElement('span');
                sample.style.color = color;
                document.body.append(sample);
                const values = getComputedStyle(sample).color
                    .match(/\\d+(?:\\.\\d+)?/g).slice(0, 3).map(Number);
                sample.remove();
                return values;
            };
            const luminance = color => {
                const values = rgb(color).map(value => {
                    value /= 255;
                    return value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4;
                });
                return .2126 * values[0] + .7152 * values[1] + .0722 * values[2];
            };
            const composite = (foreground, background, alpha) => rgb(foreground)
                .map((value, index) => value * alpha + rgb(background)[index] * (1 - alpha));
            const ratio = (foreground, background, alpha = 1) => {
                const mixed = alpha === 1 ? rgb(foreground)
                    : composite(foreground, background, alpha);
                const [light, dark] = [luminance(`rgb(${mixed})`), luminance(background)]
                    .sort((a, b) => b - a);
                return (light + .05) / (dark + .05);
            };
            const style = selector => getComputedStyle(document.querySelector(selector));
            const background = selector => style(selector).backgroundColor;
            const grid = document.querySelector('#graphSvg line');
            return [
                ['panel border', style('.panel').borderColor, background('.panel')],
                ['range border', style('.range-btn').borderColor, background('.range-btn')],
                ['metric border', style('.metric').borderTopColor, background('.live')],
                ['table divider', style('.data-table td').borderBottomColor,
                    background('.recent')],
                ['summary header divider', style('.summary .data-table th').borderBottomColor,
                    background('.summary .data-table thead')],
                ['disabled next', style('#nextBtn').color, background('body'),
                    Number(style('#nextBtn').opacity)],
                ['graph grid', style('#graphSvg line').stroke, background('.graph'),
                    Number(grid.getAttribute('stroke-opacity') || 1)],
                ...[...document.querySelectorAll('#graphSvg circle')].map((point, index) => [
                    `graph point ${index}`, getComputedStyle(point).fill, background('.graph'),
                ]),
            ].map(([name, foreground, background, alpha]) => ({
                name, ratio: ratio(foreground, background, alpha),
            }));
        }""")
        page.get_by_role("button", name="model-0").click()
        treatments.extend(page.evaluate("""() => {
            const rgb = color => {
                const sample = document.createElement('span');
                sample.style.color = color;
                document.body.append(sample);
                const values = getComputedStyle(sample).color
                    .match(/\\d+(?:\\.\\d+)?/g).slice(0, 3).map(Number);
                sample.remove();
                return values;
            };
            const luminance = color => {
                const values = rgb(color).map(value => {
                    value /= 255;
                    return value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4;
                });
                return .2126 * values[0] + .7152 * values[1] + .0722 * values[2];
            };
            const composite = (foreground, background, alpha) => rgb(foreground)
                .map((value, index) => value * alpha + rgb(background)[index] * (1 - alpha));
            const ratio = (foreground, background, alpha) => {
                const mixed = composite(foreground, background, alpha);
                const [light, dark] = [luminance(`rgb(${mixed})`), luminance(background)]
                    .sort((a, b) => b - a);
                return (light + .05) / (dark + .05);
            };
            const style = selector => getComputedStyle(document.querySelector(selector));
            const hidden = style('.legend-item[aria-pressed="false"]');
            return [{name: 'hidden legend', ratio: ratio(hidden.color,
                getComputedStyle(document.body).backgroundColor, Number(hidden.opacity))}];
        }"""))
        assert all(item["ratio"] >= 4.5 for item in treatments), (theme, treatments)


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
    page.evaluate("active.end = new Date(Date.now() - 5_000)")
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
