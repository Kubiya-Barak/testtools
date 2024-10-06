from kubiya_sdk.tools.models import Tool, Arg, FileSpec
import json

class PagerDuty(Tool):
    def __init__(self, long_running=False, mermaid_diagram=None):
        script_content = f"""
#!/usr/bin/env python3

import os
import argparse

import requests


def _get_or_raise_env_var(env_var):
    value = os.getenv(env_var)
    if value is None:
        raise Exception(f"Env var {env_var} is not set")
    return value


def create_pd_incident(description: str):
    PD_API_KEY = _get_or_raise_env_var("PD_API_KEY")
    SERVICE_ID = _get_or_raise_env_var("PD_SERVICE_ID")
    ESCALATION_POLICY_ID = _get_or_raise_env_var("PD_ESCALATION_POLICY_ID")
    KUBIYA_USER_EMAIL = _get_or_raise_env_var("KUBIYA_USER_EMAIL")

    url = "https://api.pagerduty.com/incidents"
    headers = {
        "Authorization": f"Token token={PD_API_KEY}",
        "Content-Type": "application/json",
        "From": KUBIYA_USER_EMAIL,  # Add the From header with the user's email address
    }
    payload = {
        "incident": {
            "type": "incident",
            "title": f"Assistance requested via Kubi - {description}",
            "service": {"id": SERVICE_ID, "type": "service_reference"},
            "escalation_policy": {
                "id": ESCALATION_POLICY_ID,
                "type": "escalation_policy_reference",
            },
            "body": {"type": "incident_body", "details": description},
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise Exception(f"Failed to create incident: {e}")

    try:
        return response.json()["incident"]["id"]
    except Exception as e:
        raise Exception(f"Failed to fetch incident id: {e}")


def main(description):
    if not description:
        print("Usage: page-oncall-engineer.py --description <description>")
        return

    pd_incident_id = create_pd_incident(description)
    print(
        f"The on-call engineer has been paged. They will reach out to you as soon as possible. Your PagerDuty incident URL is https://aetnd.pagerduty.com/incidents/{pd_incident_id}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Page the on-call engineer via PagerDuty."
    )
    parser.add_argument(
        "--description", required=True, help="The description of the problem."
    )
    args = parser.parse_args()
    main(args.description)
"""
        super().__init__(
            name="page-oncall-engineer-python",
            description="This will create a PagerDuty incident and notify the on-call engineer",  # Description is important for the teammate to understand what the tool doesdescription=description,
            type="docker",
            image="python:3.11",
            content="python /tmp/script.py --description '{{ .description }}'",    
            args=[
                Arg(
                    name="description",
                    required=True,
                    description="The description of the incident for the on-call engineer",
                ),
            ],
            secrets=["PD_API_KEY"],
            long_running=long_running,
            mermaid=mermaid_diagram,
            env=[
                "PD_SERVICE_ID",
                "PD_ESCALATION_POLICY_ID",
                "KUBIYA_USER_EMAIL",
            ],
            with_files=[
                FileSpec(
                    destination="/tmp/script.py",
                    content=script_content,
                )
            ],
        )