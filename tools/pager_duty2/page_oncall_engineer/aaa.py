from kubiya_sdk.tools.models import Tool, Arg, FileSpec

JENKINS_ICON_URL = "https://cdn-icons-png.flaticon.com/256/25/25231.png"

class JenkinsTool(Tool):
    def __init__(self, name, description, script, args, long_running=False, mermaid_diagram=None):
        env = ["JENKINS_URL", "JENKINS_USER", "JENKINS_TOKEN"]
        super().__init__(
            name=name,
            description=description,
            icon_url=JENKINS_ICON_URL,
            type="docker",
            image="python:3.11",
            content="python /tmp/script.py",
            args=args,
            secrets=env,
            long_running=long_running,
            mermaid=mermaid_diagram,
            with_files=[
                FileSpec(
                    destination="/tmp/script.py",
                    content=script,
                )
            ],
        )
