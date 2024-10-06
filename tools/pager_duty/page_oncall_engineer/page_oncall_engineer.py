from kubiya_sdk.tools import Arg
from base import PagerDuty
from kubiya_sdk.tools.registry import tool_registry

# PagerDuty Tool
pager_duty = PagerDuty(long_running=False)

# Register the PagerDuty tool
tool_registry.register("pager_duty", pager_duty)