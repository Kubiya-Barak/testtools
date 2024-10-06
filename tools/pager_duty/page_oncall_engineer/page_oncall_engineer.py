from kubiya_sdk.tools import Arg
from .base import SlackTool
from kubiya_sdk.tools.registry import tool_registry

# Slack Send Message Tool
pager_duty = PagerDuty(
   long_running = false
)

tool_registry.register("pager_duty", pager_duty)