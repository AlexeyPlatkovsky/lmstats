
const $ = id => document.getElementById(id);
const RANGES = {"5m": 300, "15m": 900, "1h": 3600, "24h": 86400, "1mo": 2592000};
const BUCKET_SECONDS = {"5m": 30, "15m": 60, "1h": 60, "24h": 900, "1mo": 86400};
const PALETTES = {
  dark: ["#38ff14", "#e5b800", "#39c5cf", "#bc8cff", "#f778ba", "#58a6ff"],
  light: ["#0969da", "#8250df", "#087d1c", "#b54708", "#a82568", "#006b73"],
};
const LOCAL_ZONE = Intl.DateTimeFormat().resolvedOptions().timeZone;
let active = {range: "1h", end: new Date(), start: null};
let followingLive = true;
let fetchSeq = 0;
let graphState = null;
const hiddenModels = new Set();
const modelColorIndexes = new Map();
let hoveredModel = null;

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  const isLight = theme === "light";
  $("themeToggle").setAttribute("aria-label", `Switch to ${isLight ? "dark" : "light"} theme`);
  $("themeToggle").title = `Switch to ${isLight ? "dark" : "light"} theme`;
  localStorage.setItem("theme", theme);
}

setTheme(localStorage.getItem("theme") === "light" ? "light" : "dark");
$("themeToggle").onclick = () => {
  setTheme(document.documentElement.dataset.theme === "light" ? "dark" : "light");
  if (graphState) renderGraph(graphState.data, graphState.emptyMessage);
};

function fmt(value, kind = "tps") {
  if (value == null || Number.isNaN(value)) return "—";
  if (kind === "int") return Math.round(value).toLocaleString("en-US");
  if (kind === "short") return value >= 1000 ? (value / 1000).toFixed(1) + "k" : Math.round(value);
  if (kind === "sec") return Number(value).toFixed(1) + " s";
  return Number(value).toFixed(1);
}

function esc(value) {
  const element = document.createElement("span");
  element.textContent = value || "—";
  return element.innerHTML;
}

function time(date) {
  return new Intl.DateTimeFormat("sv-SE", {
    dateStyle: "short", timeStyle: "medium", hour12: false, timeZone: LOCAL_ZONE,
  }).format(date);
}

function render(state) {
  const collectorState = state.collector || "disconnected";
  const prediction = state.prediction;
  const hasSpeed = prediction && prediction.tokensPerSecond != null;
  const liveStatus = collectorState === "connected" ? (prediction ? "CONNECTED" : "WAITING") : collectorState.toUpperCase();
  $("dot").className = "dot " + (collectorState === "connected" ? (prediction ? "connected" : "waiting") : collectorState);
  $("statusText").textContent = "LM Studio: " + liveStatus;
  $("speed").textContent = hasSpeed ? fmt(prediction.tokensPerSecond) : "—";
  $("speedUnit").textContent = hasSpeed ? "tok/s" : "";
  $("model").textContent = prediction?.modelIdentifier || "—";
  [["ttft", "timeToFirstTokenSec", "sec"], ["prompt", "promptTokensCount", "int"], ["output", "predictedTokensCount", "int"], ["total", "totalTokensCount", "int"], ["gentime", "totalTimeSec", "sec"]].forEach(([id, key, kind]) => $(id).textContent = fmt(prediction?.[key], kind));
  $("updated").textContent = prediction?.timestampMs ? time(new Date(prediction.timestampMs)) : "—";
}

function win() {
  return active.range === "custom" ? {start: active.start, end: active.end} : {start: new Date(active.end - RANGES[active.range] * 1000), end: active.end};
}

function controls() {
  const window = win();
  $("selectedRange").textContent = time(window.start) + " → " + time(window.end);
  document.querySelectorAll("[data-range]").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.range === active.range)));
  $("customBtn").setAttribute("aria-pressed", String(active.range === "custom"));
  $("nextBtn").disabled = followingLive;
}

function filterHistory(history) {
  const window = win();
  return {...history, generatedAt: window.end.toISOString(), series: history.series.map(series => ({...series, points: series.points.filter(point => {
    const timestamp = new Date(point.timestamp);
    return timestamp >= window.start && timestamp <= window.end;
  })})).filter(series => series.points.length)};
}

function legacyHistoryAvailable(history) {
  const window = win();
  const generatedAt = new Date(history.generatedAt);
  const earliest = new Date(generatedAt - RANGES["24h"] * 1000);
  return window.start >= new Date(earliest - 60_000);
}

function params() {
  const window = win();
  const query = new URLSearchParams();
  if (active.range === "custom") {
    query.set("start", window.start.toISOString());
    query.set("end", window.end.toISOString());
  } else {
    query.set("range", active.range);
    query.set("at", window.end.toISOString());
  }
  return query;
}

function cell(value, kind) { return `<td>${fmt(value, kind)}</td>`; }

function modelColorIndex(model) {
  if (!modelColorIndexes.has(model)) modelColorIndexes.set(model, modelColorIndexes.size);
  return modelColorIndexes.get(model);
}

function modelColor(model) { return color(modelColorIndex(model)); }

function modelLabel(model) {
  return `<span class="model-label" data-model-color-index="${modelColorIndex(model)}">${esc(model)}</span>`;
}

function setModelColors(data) {
  modelColorIndexes.clear();
  [
    ...(data.history?.series || []).map(series => series.model),
    ...(data.recent || []).map(row => row.modelIdentifier),
    ...(data.summary || []).map(row => row.model),
  ].forEach(modelColorIndex);
}

function refreshModelLabelColors() {
  document.querySelectorAll(".model-label").forEach(label => {
    label.style.color = color(Number(label.dataset.modelColorIndex));
  });
}

function recent(rows, unavailable = "") {
  $("recentRows").innerHTML = unavailable ? `<tr><td class="empty" colspan="8">${unavailable}</td></tr>` : rows.length ? rows.map(row => {
    const date = new Date(row.timestampMs);
    const displayTime = date.toLocaleString("en-GB", {day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", timeZone: LOCAL_ZONE});
    return `<tr><td>${displayTime}</td><td title="${esc(row.modelIdentifier)}">${modelLabel(row.modelIdentifier)}</td>${cell(row.promptTokensCount, "short")}${cell(row.predictedTokensCount, "short")}${cell(row.tokensPerSecond)}${cell(row.timeToFirstTokenSec, "sec")}${cell(row.totalTimeSec, "sec")}<td>${esc(row.stopReason)}</td></tr>`;
  }).join("") : '<tr><td class="empty" colspan="8">No generations recorded yet.</td></tr>';
}

function summary(rows, unavailable = "") {
  $("summaryRows").innerHTML = unavailable ? `<tr><td class="empty" colspan="9">${unavailable}</td></tr>` : rows.length ? rows.map(row => `<tr><td title="${esc(row.model)}">${modelLabel(row.model)}</td>${cell(row.requests, "int")}${cell(row.avgTokensPerSecond)}${cell(row.medianTokensPerSecond)}${cell(row.minTokensPerSecond)}${cell(row.maxTokensPerSecond)}${cell(row.avgTimeToFirstTokenSec, "sec")}${cell(row.promptTokens, "short")}${cell(row.outputTokens, "short")}</tr>`).join("") : '<tr><td class="empty" colspan="9">No model summary for this period.</td></tr>';
}

function color(index) {
  const theme = document.documentElement.dataset.theme === "light" ? "light" : "dark";
  const palette = PALETTES[theme];
  return palette[index % palette.length];
}

function niceStep(maximum) {
  const magnitude = 10 ** Math.floor(Math.log10(Math.max(maximum / 3, 1)));
  const normalized = maximum / 3 / magnitude;
  return (normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 3 ? 3 : normalized <= 5 ? 5 : 10) * magnitude;
}

function bucketSeconds(range) {
  if (range !== "custom") return BUCKET_SECONDS[range] || 60;
  const window = win();
  return Math.max(10, Math.floor((window.end - window.start) / 1000 / 120));
}

function bucketLabel(timestamp, range) {
  const start = new Date(timestamp);
  const end = new Date(start.getTime() + bucketSeconds(range) * 1000);
  const options = {hour: "2-digit", minute: "2-digit", timeZone: LOCAL_ZONE};
  return `Bucket: ${start.toLocaleTimeString("en-GB", options)}–${end.toLocaleTimeString("en-GB", options)}`;
}

function updateHighlight() {
  $("graphSvg").querySelectorAll(".graph-line").forEach(line => {
    line.setAttribute("stroke-width", line.dataset.modelKey === String(hoveredModel) ? "3" : "1.5");
  });
}

function renderLegend(series, colors, data, emptyMessage) {
  const legend = $("legend");
  legend.innerHTML = series.map((item, index) => `<button class="legend-item" type="button" data-index="${index}" aria-pressed="${!hiddenModels.has(item.model)}"><i class="swatch" style="background:${colors.get(item.model)}"></i>${esc(item.model)}</button>`).join("");
  legend.querySelectorAll(".legend-item").forEach(button => {
    const index = Number(button.dataset.index);
    const model = series[index].model;
    button.onclick = () => {
      if (hiddenModels.has(model)) hiddenModels.delete(model);
      else hiddenModels.add(model);
      renderGraph(data, emptyMessage);
    };
    button.onmouseenter = () => { hoveredModel = index; updateHighlight(); };
    button.onmouseleave = () => { hoveredModel = null; updateHighlight(); };
    button.onfocus = () => { hoveredModel = index; updateHighlight(); };
    button.onblur = () => { hoveredModel = null; updateHighlight(); };
  });
}

function renderGraph(data, emptyMessage = "No generations recorded in this period.") {
  graphState = {data, emptyMessage};
  const svg = $("graphSvg");
  const empty = $("emptyText");
  const legend = $("legend");
  const series = data.series || [];
  const monthly = data.range === "1mo";
  const colors = new Map(series.map(item => [item.model, modelColor(item.model)]));
  refreshModelLabelColors();
  const points = series.flatMap(item => item.points.filter(point => point.avgTokensPerSecond != null).map(point => ({...point, model: item.model})));
  if (!points.length) {
    svg.innerHTML = "";
    empty.textContent = emptyMessage;
    empty.classList.remove("hidden");
    legend.innerHTML = "";
    return;
  }
  empty.classList.add("hidden");
  const bounds = $("graphArea").getBoundingClientRect();
  const width = bounds.width;
  const height = bounds.height;
  const pad = {top: 6, right: 8, bottom: 20, left: 36};
  const window = win();
  const min = window.start.getTime();
  const max = window.end.getTime();
  const maxValue = Math.max(...points.map(point => point.avgTokensPerSecond));
  const step = niceStep(maxValue);
  const yMax = Math.max(step * 3, Math.ceil(maxValue / step) * step);
  const x = value => monthly ? pad.left + (value - 1) / 9 * (width - pad.left - pad.right) : pad.left + (value - min) / (max - min || 1) * (width - pad.left - pad.right);
  const y = value => pad.top + height - pad.top - pad.bottom - value / yMax * (height - pad.top - pad.bottom);
  let output = "";
  for (let value = 0; value <= yMax; value += step) {
    const position = y(value);
    output += `<text x="${pad.left - 4}" y="${position + 3}" text-anchor="end" fill="var(--color-secondary)" font-size="9">${value}</text><line x1="${pad.left}" y1="${position}" x2="${width - pad.right}" y2="${position}" stroke="var(--color-grid)" stroke-dasharray="2 4"/>`;
  }
  if (monthly) {
    for (let index = 1; index <= 10; index += 1) {
      output += `<text x="${x(index)}" y="${height - 4}" text-anchor="middle" fill="var(--color-secondary)" font-size="9">${index}</text>`;
    }
  } else {
    for (let index = 0; index <= 4; index += 1) {
      const timestamp = min + (max - min) * index / 4;
      const position = x(timestamp);
      const label = new Date(timestamp).toLocaleTimeString("en-GB", {hour: "2-digit", minute: "2-digit", timeZone: LOCAL_ZONE});
      const anchor = index === 4 ? "end" : "middle";
      output += `<text x="${position}" y="${height - 4}" text-anchor="${anchor}" fill="var(--color-secondary)" font-size="9">${label}</text>`;
    }
  }
  for (const [modelIndex, item] of series.entries()) {
    if (hiddenModels.has(item.model)) continue;
    const visible = item.points.filter(point => point.avgTokensPerSecond != null);
    const paint = colors.get(item.model);
    output += `<path class="graph-line" data-model="${esc(item.model)}" data-model-key="${modelIndex}" d="${visible.map((point, index) => (index ? "L" : "M") + x(monthly ? index + 1 : new Date(point.timestamp).getTime()).toFixed(1) + "," + y(point.avgTokensPerSecond).toFixed(1)).join(" ")}" fill="none" stroke="${paint}" stroke-width="1.5"/>`;
    output += visible.map((point, index) => `<circle class="pt" cx="${x(monthly ? index + 1 : new Date(point.timestamp).getTime()).toFixed(1)}" cy="${y(point.avgTokensPerSecond).toFixed(1)}" r="3" fill="${paint}" data-model="${esc(item.model)}" data-timestamp="${point.timestamp}" data-index="${index + 1}" data-tps="${point.avgTokensPerSecond}" data-count="${point.count}"/>`).join("");
  }
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.innerHTML = output;
  renderLegend(series, colors, data, emptyMessage);
  updateHighlight();
  svg.querySelectorAll(".pt").forEach(point => point.onmouseenter = event => {
    const tooltip = $("tooltip");
    const area = $("graphArea");
    const label = monthly ? `Entry ${point.dataset.index} of 10` : bucketLabel(point.dataset.timestamp, data.range);
    tooltip.innerHTML = `${point.dataset.model}<br>${label}<br>${point.dataset.tps} tok/s · ${point.dataset.count} reqs`;
    tooltip.style.display = "block";
    const left = Math.min(Math.max(0, event.offsetX + 8), area.clientWidth - tooltip.offsetWidth);
    tooltip.style.left = left + "px";
    tooltip.style.top = Math.max(0, event.offsetY - 40) + "px";
    point.onmouseleave = () => tooltip.style.display = "none";
  });
}

async function fetchHistory() {
  const sequence = ++fetchSeq;
  controls();
  try {
    let response = await fetch("/api/dashboard?" + params());
    let data;
    if (response.status === 404) {
      response = await fetch("/api/history?range=24h");
      const history = await response.json();
      const unavailable = "Detailed rows require the dashboard API. Restart LM Speed Viewer to enable them.";
      if (legacyHistoryAvailable(history)) {
        data = {history: filterHistory(history), recent: [], summary: [], unavailable};
      } else {
        data = {history: {series: []}, recent: [], summary: [], unavailable, emptyMessage: "Historical navigation requires the dashboard API."};
      }
    } else {
      if (!response.ok) throw Error();
      data = await response.json();
    }
    if (sequence !== fetchSeq) return;
    setModelColors(data);
    recent(data.recent, data.unavailable);
    summary(data.summary, data.unavailable);
    renderGraph(data.history, data.emptyMessage);
  } catch (error) {
    if (sequence === fetchSeq) {
      recent([]);
      summary([]);
      renderGraph({series: []});
    }
  }
}

const refresh = fetchHistory;
$("rangeBtns").onclick = event => { const button = event.target.closest("[data-range]"); if (button) { active = {range: button.dataset.range, end: new Date(), start: null}; followingLive = true; refresh(); } };
$("prevBtn").onclick = () => { const window = win(); const span = window.end - window.start; active.end = new Date(window.start); if (active.range === "custom") active.start = new Date(active.end - span); followingLive = false; refresh(); };
$("nextBtn").onclick = () => { const window = win(); const span = window.end - window.start; active.end = new Date(Math.min(Date.now(), window.end.getTime() + span)); if (active.range === "custom") active.start = new Date(active.end - span); followingLive = active.end >= Date.now() - 1000; refresh(); };
$("customBtn").onclick = () => { const window = win(); const local = date => new Date(date - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16); $("customStart").value = local(window.start); $("customEnd").value = local(window.end); $("formError").textContent = ""; $("customDialog").showModal(); };
$("cancelCustom").onclick = () => $("customDialog").close();
$("customForm").onsubmit = event => { event.preventDefault(); const start = new Date($("customStart").value); const end = new Date($("customEnd").value); if (!(start < end) || end - start > 604800000 || end > Date.now()) { $("formError").textContent = "Choose a past range no longer than seven days."; return; } active = {range: "custom", start, end}; followingLive = false; $("customDialog").close(); refresh(); };
new ResizeObserver(() => { if (graphState) renderGraph(graphState.data, graphState.emptyMessage); }).observe($("graphArea"));
const es = new EventSource("/events");
es.onmessage = event => { try { const state = JSON.parse(event.data); render(state); if (state.prediction && followingLive) { active.end = new Date(); refresh(); } } catch (_) {} };
refresh();
