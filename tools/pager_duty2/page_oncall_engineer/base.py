import inspect

from kubiya_sdk import tool_registry
from kubiya_sdk.tools.models import Arg, Tool, FileSpec


page_oncall_engineer_tool = Tool(
    name="page-oncall-engineer-python",
    description="This will create a PagerDuty incident and notify the on-call engineer",  # Description is important for the teammate to understand what the tool does
    type="docker",
    image="python:3.11-bullseye",
    args=[
        Arg(
            name="description",
            required=True,
            description="The description of the incident for the on-call engineer",
        ),
    ],
    secrets=["PD_API_KEY"],
    env=[
        "PD_SERVICE_ID",
        "PD_ESCALATION_POLICY_ID",
        "KUBIYA_USER_EMAIL",
    ],
    content="""
pip install requests==2.32.3 > /dev/null 2>&1

python /tmp/main.py --description "{{ .description }}"
""",
    with_files=[
        FileSpec(
            destination="/tmp/main.py",
            content=inspect.getsource(page_oncall_engineer),
        ),
    ],
)

tool_registry.register("aedm", page_oncall_engineer_tool)