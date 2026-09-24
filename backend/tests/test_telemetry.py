import json
import logging
from app.core.telemetry import scrub_secrets, TelemetryLogger, correlation_id_ctx

def test_scrub_secrets_dict_keys():
    data = {
        "password": "my_super_secret_password",
        "api_key": "12345",
        "github_token": "ghp_1234567890",
        "public_field": "hello world"
    }
    scrubbed = scrub_secrets(data)
    assert scrubbed["password"] == "[REDACTED]"
    assert scrubbed["api_key"] == "[REDACTED]"
    assert scrubbed["github_token"] == "[REDACTED]"
    assert scrubbed["public_field"] == "hello world"

def test_scrub_secrets_string_patterns():
    # Test specific regex replacements inside strings
    string_data = "Here is my token: ghp_abc123XYZ. Also Bearer 1234-5678."
    scrubbed = scrub_secrets(string_data)
    assert "ghp_abc123XYZ" not in scrubbed
    assert "[REDACTED_TOKEN]" in scrubbed
    assert "Bearer [REDACTED]" in scrubbed

def test_telemetry_logger(caplog):
    correlation_id_ctx.set("test-corr-id")
    with caplog.at_level(logging.INFO):
        TelemetryLogger.log_event(
            event_type="TEST_EVENT",
            details={"key": "value", "secret": "hide_me"},
            duration_ms=150.5
        )
    
    assert len(caplog.records) == 1
    record = caplog.records[0]
    event = json.loads(record.message)
    
    assert event["schema_version"] == "1.0.0"
    assert event["event_type"] == "TEST_EVENT"
    assert event["correlation_id"] == "test-corr-id"
    assert event["outcome"] == "SUCCESS"
    assert event["duration_ms"] == 150.5
    assert "event_id" in event
    assert "timestamp" in event
    
    # Secret should be scrubbed
    assert event["details"]["key"] == "value"
    assert event["details"]["secret"] == "[REDACTED]"
