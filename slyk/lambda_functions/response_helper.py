"""Shared response formatter for SLyK Lambda functions.
Handles both API-path and function-based Bedrock Agent invocations."""

import json


def build_response(event, body_data):
    """Build a response compatible with both API-schema and function-schema action groups."""
    body = json.dumps(body_data, default=str) if not isinstance(body_data, str) else body_data

    # Function-based action group
    if event.get("function"):
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get("actionGroup", ""),
                "function": event.get("function", ""),
                "functionResponse": {
                    "responseBody": {
                        "TEXT": {"body": body}
                    }
                }
            }
        }

    # API-path-based action group (legacy)
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "apiPath": event.get("apiPath", ""),
            "httpMethod": event.get("httpMethod", "POST"),
            "httpStatusCode": 200,
            "responseBody": {"application/json": {"body": body}},
        },
    }


def get_params(event):
    """Extract parameters from either function-based or API-based event."""
    # Function-based
    if event.get("parameters"):
        return {p["name"]: p["value"] for p in event["parameters"]}
    # API-based
    if event.get("requestBody"):
        return event["requestBody"]
    return {}
