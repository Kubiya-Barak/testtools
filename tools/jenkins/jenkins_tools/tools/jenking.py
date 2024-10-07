from kubiya_sdk.tools import Arg
from base import JenkinsTool
from kubiya_sdk.tools.registry import tool_registry

hello_world = JenkinsTool(
    name="hello_world",
    description="Hello world",
    script="import os; print(f'Hello {os.environ.get(\"name\", \"User\")}')",
    args=[
        Arg(name="name", type="str", description="Name of the user)", required=True),
    ],
)

tool_registry.register("jenkins", hello_world)
