"""Normalization for LM Studio prediction log events."""

import json


PREDICTION_TYPE = "llm.prediction.output"
MAX_TOKENS_PER_SECOND = 999


def parse_line(line):
    """Return a normalized completed prediction, or ``None`` for unrelated input."""
    line = line.strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
    except ValueError:
        return None
    if not isinstance(obj, dict):
        return None
    data = obj.get("data")
    if not isinstance(data, dict) or data.get("type") != PREDICTION_TYPE:
        return None

    stats = data.get("stats")
    if not isinstance(stats, dict):
        stats = {}

    def num(key):
        value = stats.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return value

    model = data.get("modelIdentifier")
    timestamp = obj.get("timestamp")
    stop_reason = stats.get("stopReason")
    output = data.get("output")
    tokens_per_second = num("tokensPerSecond")
    if tokens_per_second is not None and tokens_per_second > MAX_TOKENS_PER_SECOND:
        return None
    return {
        "modelIdentifier": model if isinstance(model, str) and model else None,
        "tokensPerSecond": tokens_per_second,
        "timeToFirstTokenSec": num("timeToFirstTokenSec"),
        "totalTimeSec": num("totalTimeSec"),
        "promptTokensCount": num("promptTokensCount"),
        "predictedTokensCount": num("predictedTokensCount"),
        "totalTokensCount": num("totalTokensCount"),
        "timestampMs": (
            timestamp
            if isinstance(timestamp, (int, float)) and not isinstance(timestamp, bool)
            else None
        ),
        "stopReason": stop_reason if isinstance(stop_reason, str) else None,
        "output": output if isinstance(output, str) else None,
    }
