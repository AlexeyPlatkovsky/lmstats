"""Focused tests for the lms log stream parser."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import parse_line  # noqa: E402

# Real event captured from `lms log stream --source model --filter output
# --stats --json` in this environment (output text shortened).
REAL_EVENT = json.dumps({
    "timestamp": 1786744778242,
    "data": {
        "type": "llm.prediction.output",
        "output": "fixture output text",
        "stats": {
            "stopReason": "eosFound",
            "tokensPerSecond": 15.841340338684146,
            "numGpuLayers": -1,
            "timeToFirstTokenSec": 13.94,
            "totalTimeSec": 6.755,
            "promptTokensCount": 16632,
            "predictedTokensCount": 107,
            "totalTokensCount": 16739,
        },
        "modelIdentifier": "qwen3.8-27b-mlx",
    },
})


def test_valid_prediction_event():
    p = parse_line(REAL_EVENT)
    assert p is not None
    assert p["modelIdentifier"] == "qwen3.8-27b-mlx"
    assert p["tokensPerSecond"] == 15.841340338684146
    assert p["timeToFirstTokenSec"] == 13.94
    assert p["totalTimeSec"] == 6.755
    assert p["promptTokensCount"] == 16632
    assert p["predictedTokensCount"] == 107
    assert p["totalTokensCount"] == 16739
    assert p["timestampMs"] == 1786744778242


def test_malformed_json_ignored():
    assert parse_line("this is not json") is None
    assert parse_line('{"broken": ') is None
    assert parse_line("") is None
    assert parse_line("   ") is None


def test_unrelated_events_ignored():
    # input-side event (would appear without --filter output)
    event = json.dumps({"timestamp": 1, "data": {"type": "llm.prediction.input", "input": "x"}})
    assert parse_line(event) is None
    # server source event
    data = {"type": "server.request", "path": "/v1/chat/completions"}
    assert parse_line(json.dumps({"timestamp": 1, "data": data})) is None
    # non-dict JSON
    assert parse_line("[1, 2, 3]") is None
    # dict without data
    assert parse_line(json.dumps({"timestamp": 1})) is None


def test_missing_optional_fields_do_not_crash():
    # prediction event with no stats at all
    event = json.dumps({"timestamp": 5, "data": {"type": "llm.prediction.output", "output": "hi"}})
    p = parse_line(event)
    assert p is not None
    assert p["modelIdentifier"] is None
    assert p["tokensPerSecond"] is None
    assert p["timeToFirstTokenSec"] is None
    assert p["totalTimeSec"] is None
    assert p["promptTokensCount"] is None
    assert p["predictedTokensCount"] is None
    assert p["totalTokensCount"] is None
    assert p["timestampMs"] == 5

    # stats present but some fields missing / wrong types
    p = parse_line(json.dumps({
        "data": {
            "type": "llm.prediction.output",
            "output": "hi",
            "stats": {"tokensPerSecond": 6.2, "promptTokensCount": "many"},
            "modelIdentifier": "some-model",
        }
    }))
    assert p is not None
    assert p["tokensPerSecond"] == 6.2
    assert p["promptTokensCount"] is None  # wrong type -> unavailable
    assert p["timeToFirstTokenSec"] is None
    assert p["modelIdentifier"] == "some-model"
    assert p["timestampMs"] is None
