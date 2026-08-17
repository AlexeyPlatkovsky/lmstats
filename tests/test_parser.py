"""Focused tests for the lms log stream parser."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lm_speed_viewer.parser import PREDICTION_TYPE, parse_line  # noqa: E402

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


def test_real_event_stop_reason_and_output():
    # REAL_EVENT carries both; the parser must surface them (stage 6 group A)
    p = parse_line(REAL_EVENT)
    assert p is not None
    assert p["stopReason"] == "eosFound"
    assert p["output"] == "fixture output text"


def test_synthetic_full_event():
    line = json.dumps({
        "timestamp": 1786744900000,
        "data": {
            "type": PREDICTION_TYPE,
            "output": "hello world",
            "stats": {
                "stopReason": "maxTokens",
                "tokensPerSecond": 12.5,
                "timeToFirstTokenSec": 0.4,
                "totalTimeSec": 2.1,
                "promptTokensCount": 10,
                "predictedTokensCount": 25,
                "totalTokensCount": 35,
            },
            "modelIdentifier": "test-model",
        },
    }).encode()
    p = parse_line(line)
    assert p is not None
    assert p["timestampMs"] == 1786744900000
    assert p["stopReason"] == "maxTokens"
    assert p["output"] == "hello world"


def test_missing_new_optional_fields_are_none():
    line = json.dumps({
        "data": {
            "type": PREDICTION_TYPE,
            "stats": {"tokensPerSecond": 1.0},
        },
    }).encode()
    p = parse_line(line)
    assert p is not None  # still a valid prediction (speed present)
    for key in ("modelIdentifier", "timestampMs", "stopReason", "output"):
        assert p[key] is None


def test_non_string_new_optional_fields_are_none():
    line = json.dumps({
        "timestamp": 1786744900000,
        "data": {
            "type": PREDICTION_TYPE,
            "output": 123,
            "stats": {"stopReason": ["maxTokens"]},
            "modelIdentifier": 42,
        },
    }).encode()
    p = parse_line(line)
    assert p is not None
    assert p["timestampMs"] == 1786744900000
    assert p["stopReason"] is None  # list, not str -> None
    assert p["output"] is None      # int, not str -> None
    assert p["modelIdentifier"] is None  # non-str model -> None (v0.1 rule)


def test_zero_and_implausibly_high_prediction_rates_are_ignored():
    accepted = json.dumps({
        "data": {
            "type": PREDICTION_TYPE,
            "stats": {"tokensPerSecond": 999.0},
        },
    })
    line = json.dumps({
        "data": {
            "type": PREDICTION_TYPE,
            "stats": {"tokensPerSecond": 1000.0},
        },
    })
    zero_rate = json.dumps({
        "data": {
            "type": PREDICTION_TYPE,
            "stats": {"tokensPerSecond": 0},
        },
    })

    assert parse_line(accepted)["tokensPerSecond"] == 999.0
    assert parse_line(line) is None
    assert parse_line(zero_rate) is None
