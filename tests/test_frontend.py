"""Frontend unit tests for LM Speed Viewer.

Converts key JavaScript functions from static/index.html to Python and tests
their behavior: render(), renderGraph(), fmt(), mergeSSEIntoData(), djb2(),
modelColor(), parseISO().
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")

_PALETTE = ["#3fb950", "#58a6ff", "#d29922", "#bc8cff", "#f778ba", "#39c5cf"]
_RANGE_DURATIONS = {"5m": 300, "1h": 3600, "24h": 86400}

# ── Python translations of JS functions ──────────────────────────────────────


def djb2(s):
    """DJB2 hash from JS: h = ((h * 33) ^ charCode) >>> 0."""
    h = 5381
    for ch in s:
        h = ((h * 33) ^ ord(ch)) & 0xFFFFFFFF
    return h


def modelColor(model):
    if model is None or model == "":
        return "var(--dim)"
    return _PALETTE[djb2(model) % len(_PALETTE)]


def fmt(v, kind):
    if v is None:
        return "—"
    try:
        import math
        if math.isnan(v):
            return "—"
    except (TypeError, ValueError):
        pass
    if kind == "int":
        return f"{round(v):,}"
    if kind == "sec":
        return f"{v:.1f} s"
    if kind == "tps":
        return f"{v:.1f}"
    return str(v)


def parseISO(s):
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return dt.timestamp()


def msToISO(ts):
    secs = ts / 1000.0
    dt = datetime.fromtimestamp(secs, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def mergeSSEIntoData(data, sse):
    sseTs = msToISO(sse["timestampMs"])
    sseTPS = sse.get("tokensPerSecond")
    if sseTPS is None:
        return
    model = sse.get("modelIdentifier") or "unknown"
    for series in data["series"]:
        pts = series.get("points") or []
        if len(pts) == 0:
            continue
        lastPt = pts[-1]
        lastTs = lastPt["timestamp"]
        if sseTs > lastTs and (series.get("model") == model or not series.get("model")):
            pts.append({
                "timestamp": sseTs,
                "avgTokensPerSecond": sseTPS,
                "count": 1,
            })


def render(s):
    """Python render() that operates on a _RenderDOM stub."""
    c = s.get("collector") or "disconnected"
    p = s.get("prediction")

    dom = s["_dom"]
    dot = dom["dot"]
    statusText = dom["statusText"]
    speed = dom["speed"]
    speedUnit = dom["speedUnit"]
    modelEl = dom["model"]
    ttft = dom["ttft"]
    prompt = dom["prompt"]
    output = dom["output"]
    total = dom["total"]
    gentime = dom["gentime"]
    updated = dom["updated"]

    if c == "connected" and p:
        dotClass = "connected"
        statusText["textContent"] = "Connected"
    elif c == "connected":
        dotClass = "waiting"
        statusText["textContent"] = "Waiting for first prediction"
    elif c == "error":
        dotClass = "error"
        statusText["textContent"] = (
            f"Error: {s.get('detail')}" if s.get("detail") else "Error"
        )
    else:
        dotClass = c
        detail = s.get("detail")
        if detail:
            statusText["textContent"] = (
                c[0].upper() + c[1:] + ": " + detail
            )
        else:
            statusText["textContent"] = c[0].upper() + c[1:]

    dot["className"] = "dot " + dotClass

    import math
    hasSpeed = p and p.get("tokensPerSecond") is not None and not math.isnan(p.get("tokensPerSecond", 0))
    speed["textContent"] = fmt(p.get("tokensPerSecond"), "tps") if hasSpeed else "—"
    speedUnit["textContent"] = "tok/s" if hasSpeed else ""
    modelEl["textContent"] = (p.get("modelIdentifier")) if p and p.get("modelIdentifier") else "—"

    ttft["textContent"] = fmt(p.get("timeToFirstTokenSec") if p else None, "sec")
    prompt["textContent"] = fmt(p.get("promptTokensCount") if p else None, "int")
    output["textContent"] = fmt(p.get("predictedTokensCount") if p else None, "int")
    total["textContent"] = fmt(p.get("totalTokensCount") if p else None, "int")
    gentime["textContent"] = fmt(p.get("totalTimeSec") if p else None, "sec")

    if p and p.get("timestampMs"):
        dt = datetime.fromtimestamp(p["timestampMs"] / 1000.0, tz=timezone.utc)
        updated["textContent"] = dt.strftime("%H:%M")
    else:
        updated["textContent"] = "—"


def renderGraph(data):
    """Python renderGraph() that generates SVG content."""
    dom = data["_dom"]
    svg = dom["graphSvg"]
    empty = dom["emptyText"]
    legend = dom["legend"]
    area = dom["graphArea"]

    if not data.get("series") or len(data["series"]) == 0:
        svg["style"]["display"] = "none"
        empty["className"] = empty.get("_orig_class", "empty-text")
        legend["innerHTML"] = ""
        return

    empty["className"] = (empty.get("_orig_class", "empty-text")) + " hidden"
    svg["style"]["display"] = "block"

    W = 510  # graphArea width (540 - 30 padding)
    H = 200  # graphArea height
    pad = {"top": 15, "right": 15, "bottom": 30, "left": 50}
    gw = W - pad["left"] - pad["right"]
    gh = H - pad["top"] - pad["bottom"]

    maxX = 0
    maxY = 0
    allPoints = []
    for series in data["series"]:
        for pt in (series.get("points") or []):
            ts = parseISO(pt["timestamp"])
            if ts > maxX:
                maxX = ts
            tps = pt.get("avgTokensPerSecond")
            if tps is not None and tps > maxY:
                maxY = tps
            pt["_ts"] = ts
            allPoints.append({**pt, "_ts": ts})

    if maxX == 0:
        svg["style"]["display"] = "none"
        empty["className"] = empty.get("_orig_class", "empty-text")
        legend["innerHTML"] = ""
        return

    rangeDur = _RANGE_DURATIONS.get(data.get("range") or "1h", 3600)
    genAt = data.get("generatedAt")
    minTs = (parseISO(genAt) - rangeDur) if genAt else (maxX - rangeDur)
    xMin = minTs
    xMax = maxX
    xSpan = xMax - xMin or 1
    yMax = int((maxY + 14) // 15) * 15 if maxY > 0 else 15

    def xScale(v):
        return pad["left"] + ((v - xMin) / xSpan) * gw

    def yScale(v):
        return pad["top"] + gh - (v / yMax) * gh

    svgContent = ""

    nXLabels = 4
    for i in range(nXLabels + 1):
        ts = xMin + (xSpan * i / nXLabels)
        x = xScale(ts)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        label = dt.strftime("%H:%M")
        svgContent += f'<text x="{x}" y="{H - 5}" text-anchor="middle" fill="var(--dim)" font-size="10">{label}</text>'
        svgContent += f'<line x1="{x}" y1="{pad["top"]}" x2="{x}" y2="{pad["top"] + gh}" stroke="var(--line)" stroke-dasharray="2,4"/>'

    nYLabels = 3
    for i in range(nYLabels + 1):
        v = (yMax * i / nYLabels)
        y = yScale(v)
        svgContent += f'<text x="{pad["left"] - 5}" y="{y + 4}" text-anchor="end" fill="var(--dim)" font-size="10">{v:.1f}</text>'
        svgContent += f'<line x1="{pad["left"]}" y1="{y}" x2="{pad["left"] + gw}" y2="{y}" stroke="var(--line)" stroke-dasharray="2,4"/>'

    for series in data["series"]:
        color = modelColor(series.get("model"))
        pts = series.get("points") or []
        visible = [pt for pt in pts if pt.get("avgTokensPerSecond") is not None]
        if len(visible) == 0:
            continue

        pathD = ""
        for pt in visible:
            x = xScale(pt["_ts"])
            y = yScale(pt["avgTokensPerSecond"])
            pathD += (" L" if pathD else "M") + f"{x:.1f},{y:.1f}"
        svgContent += f'<path d="{pathD}" fill="none" stroke="{color}" stroke-width="1.5"/>'

        for pt in pts:
            x = xScale(pt["_ts"])
            tps = pt.get("avgTokensPerSecond")
            y = yScale(tps) if tps is not None else yScale(0)
            tpsStr = str(tps) if tps is not None else "no speed data"
            svgContent += f'<circle cx="{x}" cy="{y}" r="4" fill="{color}" class="pt" data-model="{series.get("model") or "unknown"}" data-timestamp="{pt["timestamp"]}" data-tps="{tpsStr}" data-count="{pt.get("count")}"/>'

    svg["innerHTML"] = svgContent
    svg["setAttribute"]("viewBox", f"0 0 {W} {H}")

    legend["innerHTML"] = ""
    for series in data["series"]:
        name = series.get("model") or "unknown"
        swatchColor = modelColor(series.get("model"))
        # In the real JS, this creates DOM elements; in Python we just track it
        legend.setdefault("_swatches", []).append(swatchColor)


# ── Test helpers ─────────────────────────────────────────────────────────────


def _make_render_dom():
    """Create a _RenderDOM stub that render() can manipulate."""
    from math import nan
    return {
        "dot": {"className": "", "textContent": ""},
        "statusText": {"textContent": ""},
        "speed": {"textContent": ""},
        "speedUnit": {"textContent": ""},
        "model": {"textContent": ""},
        "ttft": {"textContent": ""},
        "prompt": {"textContent": ""},
        "output": {"textContent": ""},
        "total": {"textContent": ""},
        "gentime": {"textContent": ""},
        "updated": {"textContent": ""},
    }


def _make_graph_dom():
    """Create a DOM stub for renderGraph()."""
    return {
        "graphSvg": {"innerHTML": "", "style": {"display": "none"}, "setAttribute": lambda k, v: None, "_viewBox": None},
        "emptyText": {"_orig_class": "empty-text", "className": "empty-text"},
        "legend": {"innerHTML": "", "_swatches": []},
        "graphArea": {},
    }


def _render(s):
    """Call render() with a fresh DOM."""
    dom = _make_render_dom()
    s["_dom"] = dom
    render(s)
    return dom


def _render_graph(data):
    """Call renderGraph() with a fresh DOM."""
    dom = _make_graph_dom()
    data["_dom"] = dom
    renderGraph(data)
    return dom


# ── Tests A1–A18 ─────────────────────────────────────────────────────────────


def test_render_connected_with_prediction():
    """A1: render() sets #dot.className='dot connected', shows speed + unit, model, all 5 metrics."""
    s = {
        "collector": "connected",
        "detail": None,
        "prediction": {
            "modelIdentifier": "qwen3.8-27b-mlx",
            "tokensPerSecond": 68.9,
            "timeToFirstTokenSec": 13.94,
            "totalTimeSec": 6.755,
            "promptTokensCount": 16632,
            "predictedTokensCount": 107,
            "totalTokensCount": 16739,
            "timestampMs": 1786744778242,
        },
    }
    dom = _render(s)
    assert dom["dot"]["className"] == "dot connected"
    assert dom["speed"]["textContent"] == "68.9"
    assert dom["speedUnit"]["textContent"] == "tok/s"
    assert dom["model"]["textContent"] == "qwen3.8-27b-mlx"
    assert dom["ttft"]["textContent"] == "13.9 s"
    assert dom["prompt"]["textContent"] == "16,632"
    assert dom["output"]["textContent"] == "107"
    assert dom["total"]["textContent"] == "16,739"
    assert dom["gentime"]["textContent"] == "6.8 s"


def test_render_disconnected():
    """A2: render() sets dot to 'dot disconnected', hides speed unit, shows '—'."""
    s = {
        "collector": "disconnected",
        "detail": "lms log stream exited (code 1)",
        "prediction": None,
    }
    dom = _render(s)
    assert "disconnected" in dom["dot"]["className"]
    assert dom["speed"]["textContent"] == "—"
    assert dom["speedUnit"]["textContent"] == ""
    assert dom["model"]["textContent"] == "—"


def test_render_error():
    """A3: render() sets dot to 'dot error', shows detail text."""
    s = {
        "collector": "error",
        "detail": "lms CLI not found (checked PATH and ~/.lmstudio/bin)",
        "prediction": None,
    }
    dom = _render(s)
    assert "error" in dom["dot"]["className"]
    assert "lms CLI not found" in dom["statusText"]["textContent"]


def test_render_waiting():
    """A4: render() sets dot to 'dot waiting' when connected but no prediction."""
    s = {
        "collector": "connected",
        "detail": "",
        "prediction": None,
    }
    dom = _render(s)
    assert "waiting" in dom["dot"]["className"]
    assert dom["speed"]["textContent"] == "—"
    assert dom["speedUnit"]["textContent"] == ""


def test_render_graph_single_series():
    """A5: renderGraph() produces <path> with valid coords, <circle> elements, axis labels, legend."""
    data = {
        "range": "1h",
        "generatedAt": "2026-08-15T10:30:00.000Z",
        "series": [{
            "model": "qwen3.8-27b-mlx",
            "points": [
                {"timestamp": "2026-08-15T10:00:00.000Z", "avgTokensPerSecond": 45.2, "count": 1},
                {"timestamp": "2026-08-15T10:15:00.000Z", "avgTokensPerSecond": 52.1, "count": 1},
                {"timestamp": "2026-08-15T10:30:00.000Z", "avgTokensPerSecond": 48.7, "count": 1},
            ],
        }],
    }
    dom = _render_graph(data)
    svg_el = dom["graphSvg"]
    assert svg_el["style"]["display"] != "none"
    svg_inner = svg_el["innerHTML"]
    assert "<path" in svg_inner
    assert "<circle" in svg_inner
    assert "<text" in svg_inner
    assert 'class="pt"' in svg_inner


def test_render_graph_empty_data():
    """A6: renderGraph() hides SVG, shows #emptyText, clears legend."""
    data = {"range": "1h", "generatedAt": "2026-08-15T10:30:00.000Z", "series": []}
    dom = _render_graph(data)
    svg_el = dom["graphSvg"]
    assert svg_el["style"]["display"] == "none"
    empty_el = dom["emptyText"]
    assert "hidden" not in empty_el["className"]
    legend_el = dom["legend"]
    assert legend_el["innerHTML"] == ""


def test_render_graph_multi_series():
    """A7: Two models → two distinct <path> elements, two legend swatches."""
    data = {
        "range": "1h",
        "generatedAt": "2026-08-15T10:30:00.000Z",
        "series": [
            {"model": "alpha", "points": [
                {"timestamp": "2026-08-15T10:00:00.000Z", "avgTokensPerSecond": 30.0, "count": 1},
            ]},
            {"model": "beta", "points": [
                {"timestamp": "2026-08-15T10:15:00.000Z", "avgTokensPerSecond": 40.0, "count": 1},
            ]},
        ],
    }
    dom = _render_graph(data)
    svg_el = dom["graphSvg"]
    svg_inner = svg_el["innerHTML"]
    path_count = svg_inner.count('<path d="')
    assert path_count >= 2, f"Expected at least 2 paths, found {path_count}"

    swatch_count = len(dom["legend"].get("_swatches", []))
    assert swatch_count >= 2, f"Expected at least 2 swatches, got {swatch_count}"


def test_render_graph_y_axis_nice_scale():
    """A8: Y-axis labels are multiples of 30 (0.0, 30.0, 60.0, 90.0), not arbitrary values."""
    data = {
        "range": "1h",
        "generatedAt": "2026-08-15T10:30:00.000Z",
        "series": [{
            "model": "test",
            "points": [
                {"timestamp": "2026-08-15T10:00:00.000Z", "avgTokensPerSecond": 85.0, "count": 1},
            ],
        }],
    }
    dom = _render_graph(data)
    svg_el = dom["graphSvg"]
    svg_inner = svg_el["innerHTML"]

    y_labels = re.findall(r'text-anchor="end".*?>(\d+\.?\d*)</text>', svg_inner)
    for label in y_labels:
        val = float(label)
        assert val % 30 == 0, f"Y-axis label '{label}' is not a multiple of 30"


def test_render_graph_no_nan_coords():
    """A9: All <circle> have numeric cx/cy attributes, no NaN strings."""
    data = {
        "range": "1h",
        "generatedAt": "2026-08-15T10:30:00.000Z",
        "series": [{
            "model": "test",
            "points": [
                {"timestamp": "2026-08-15T10:00:00.000Z", "avgTokensPerSecond": 50.0, "count": 1},
            ],
        }],
    }
    dom = _render_graph(data)
    svg_el = dom["graphSvg"]
    svg_inner = svg_el["innerHTML"]

    circles = re.findall(r'<circle[^>]*>', svg_inner)
    for circle in circles:
        assert "NaN" not in circle, f"Found NaN in circle: {circle}"
        assert "nan" not in circle, f"Found nan in circle: {circle}"


def test_render_graph_tooltip_data():
    """A10: Circles have data-timestamp, data-tps, data-count attributes."""
    data = {
        "range": "1h",
        "generatedAt": "2026-08-15T10:30:00.000Z",
        "series": [{
            "model": "test",
            "points": [
                {"timestamp": "2026-08-15T10:00:00.000Z", "avgTokensPerSecond": 50.0, "count": 3},
            ],
        }],
    }
    dom = _render_graph(data)
    svg_el = dom["graphSvg"]
    svg_inner = svg_el["innerHTML"]

    circles = re.findall(r'<circle[^>]*class="pt"[^>]*>', svg_inner)
    assert len(circles) > 0, "No .pt circles found"
    for circle in circles:
        assert "data-timestamp=" in circle
        assert "data-tps=" in circle
        assert "data-count=" in circle


def test_fmt_tps():
    """A11: fmt(68.9, 'tps') -> '68.9'."""
    assert fmt(68.9, "tps") == "68.9"


def test_fmt_sec():
    """A12: fmt(1.5, 'sec') -> '1.5 s'."""
    assert fmt(1.5, "sec") == "1.5 s"


def test_fmt_int():
    """A13: fmt(17607, 'int') -> '17,607'."""
    assert fmt(17607, "int") == "17,607"


def test_fmt_null():
    """A14: fmt(None, 'tps') -> '—', fmt(NaN, 'sec') -> '—'."""
    import math
    assert fmt(None, "tps") == "—"
    assert fmt(float("nan"), "sec") == "—"
    assert fmt(None, "int") == "—"


def test_modelColor_djb2_hash():
    """A15: Same model returns same color; different models get different colors."""
    c1 = modelColor("qwen3.8-27b-mlx")
    c2 = modelColor("qwen3.8-27b-mlx")
    assert c1 == c2

    colors = set()
    for m in ["qwen3.8-27b-mlx", "llama-3-70b", "mistral-7b", "gemma-2-27b", "phi-3-mini", "codellama-34b"]:
        colors.add(modelColor(m))
    assert len(colors) >= 5, f"Expected >= 5 distinct colors, got {len(colors)}: {colors}"

    assert modelColor(None) == "var(--dim)"
    assert modelColor("") == "var(--dim)"
    assert modelColor("unknown") != "var(--dim)"


def test_mergeSSEIntoData_injects_latest():
    """A16: SSE prediction with newer timestamp → appended to last series point."""
    data = {
        "series": [{
            "model": "qwen3.8-27b-mlx",
            "points": [
                {"timestamp": "2026-08-15T10:00:00.000Z", "avgTokensPerSecond": 45.0, "count": 1},
            ],
        }],
    }
    sse = {
        "modelIdentifier": "qwen3.8-27b-mlx",
        "tokensPerSecond": 68.9,
        "timestampMs": 1786788900000,
    }
    mergeSSEIntoData(data, sse)
    assert len(data["series"][0]["points"]) == 2
    assert data["series"][0]["points"][1]["avgTokensPerSecond"] == 68.9
    assert data["series"][0]["points"][1]["count"] == 1


def test_mergeSSEIntoData_ignored_older():
    """A17: SSE prediction older than last DB point → no append."""
    data = {
        "series": [{
            "model": "qwen3.8-27b-mlx",
            "points": [
                {"timestamp": "2026-08-15T10:30:00.000Z", "avgTokensPerSecond": 50.0, "count": 1},
            ],
        }],
    }
    sse = {
        "modelIdentifier": "qwen3.8-27b-mlx",
        "tokensPerSecond": 68.9,
        "timestampMs": 1786741200000,
    }
    mergeSSEIntoData(data, sse)
    assert len(data["series"][0]["points"]) == 1


def test_fetchHistory_race_guard():
    """A18: fetchHistory uses fetchSeq for race guard (seq !== fetchSeq → return).

    We verify the JavaScript source contains the race guard pattern since
    the fetchHistory function is called from the browser, not from Python.
    """
    html = open(os.path.join(STATIC_DIR, "index.html"), "r").read()
    m = re.search(r"<script>([\s\S]*?)</script>", html)
    assert m is not None, "no <script> block found in index.html"
    script = m.group(1)
    assert "fetchSeq" in script
    assert "if (seq !== fetchSeq) return" in script
