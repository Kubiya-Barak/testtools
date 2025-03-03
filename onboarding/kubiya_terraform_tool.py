import inspect
import sys
from pathlib import Path
import os
import subprocess
import json
from typing import List
from kubiya_sdk.tools import Tool, Arg, FileSpec, Volume
from kubiya_sdk.tools.registry import tool_registry

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

TERRAFORM_ICON_URL = "https://storage.getlatka.com/images/kubiya.ai.png"

def read_terraform_file(path: str) -> str:
    """Read a Terraform file from disk"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, path)
    with open(file_path, 'r') as f:
        return f.read()

def extract_token_from_output(output_json: str) -> str:
    """Extract the Kubiya API token from Terraform output"""
    try:
        data = json.loads(output_json)
        return data.get("result", {}).get("value", {}).get("token", "")
    except json.JSONDecodeError:
        return ""

# Script that will be embedded in the tool
def terraform_handler():
    """
    Handle Terraform execution and token management
    """
    import json
    import os
    import sys

    # Get the token from terraform output
    try:
        output = sys.stdin.read()
        token = extract_token_from_output(output)
        if token:
            os.environ["KUBIYA_API_TOKEN"] = token
            print(json.dumps({
                "status": "success",
                "message": "Token extracted and set successfully",
                "token": token
            }))
        else:
            print(json.dumps({
                "status": "error",
                "message": "No token found in output"
            }))
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e)
        }))

class TerraformTool(Tool):
    def __init__(self, name, description, content, args):
        # Setup Terraform environment and token handling
        setup_script = f"""
set -eu

# Install required packages
apk add --no-cache python3 curl jq

cd /terraform

# Ensure KUBIYA_API_KEY is available
if [ -z "$KUBIYA_API_KEY" ]; then
    echo "Error: KUBIYA_API_KEY environment variable is not set"
    exit 1
fi

# Write tfvars file if provided
if [ ! -z "${{org_name:-}}" ] && [ ! -z "${{admin_email:-}}" ]; then
    cat > terraform.tfvars << EOL
org_name = "${{org_name}}"
admin_email = "${{admin_email}}"
invite_users = [${{invite_users:-}}]
invite_admins = [${{invite_admins:-}}]
managed_runner = ${{managed_runner:-false}}
EOL
fi

# Step 1: Run onboarding to get token
cd /terraform
terraform init
terraform apply -target=null_resource.onboard_organization -target=local_file.token_file -auto-approve

# Step 2: If we got a token, run the resources configuration
if [ -f /terraform/token.txt ]; then
    # Export token and ensure it's available to subsequent commands
    TOKEN=$(cat /terraform/token.txt)
    export KUBIYA_API_KEY="$TOKEN"    # Set the API key to the new token
    echo "Verifying new token:"
    echo "KUBIYA_API_KEY=$KUBIYA_API_KEY"
    echo "KUBIYA_API_TOKEN=$TOKEN"
    
    # Run the second configuration with the new token
    cd /terraform/modules/kubiya_resources
    terraform init
    terraform apply -auto-approve
fi

python3 /opt/scripts/terraform_handler.py
"""

        super().__init__(
            name=name,
            description=description,
            icon_url=TERRAFORM_ICON_URL,
            type="docker",
            image="hashicorp/terraform:latest",
            content=setup_script,
            args=args,
            secrets=["KUBIYA_API_KEY"],
            with_files=[
                # First configuration for onboarding
                FileSpec(
                    destination="/terraform/main.tf",
                    content=read_terraform_file("terraform/main.tf")
                ),
                FileSpec(
                    destination="/terraform/variables.tf",
                    content=read_terraform_file("terraform/variables.tf")
                ),
                # Second configuration for resources
                FileSpec(
                    destination="/terraform/modules/kubiya_resources/main.tf",
                    content=read_terraform_file("terraform/modules/kubiya_resources/main.tf")
                ),
                FileSpec(
                    destination="/terraform/modules/kubiya_resources/variables.tf",
                    content=read_terraform_file("terraform/modules/kubiya_resources/variables.tf")
                ),
                # Python handler script
                FileSpec(
                    destination="/opt/scripts/terraform_handler.py",
                    content=inspect.getsource(terraform_handler)
                )
            ],
            with_volumes=[
                Volume(
                    name="terraform_cache",
                    path="/terraform/.terraform"
                )
            ]
        )

# Create the onboarding tool
terraform_onboarding_tool = TerraformTool(
    name="terraform_onboarding",
    description="""
Execute Terraform for Kubiya onboarding and set API token.
This tool will:
1. Create a new organization
2. Set up initial configuration
3. Configure sources and integrations
4. Set the API token for subsequent operations
""",
    content="""
terraform init && \
terraform apply -auto-approve && \
terraform output -json
""",
    args=[
        Arg(
            name="org_name",
            description="The name of the organization to create",
            required=True
        ),
        Arg(
            name="admin_email",
            description="The email address of the organization administrator",
            required=True
        ),
        Arg(
            name="invite_users",
            description="""
List of user email addresses to invite to the organization.
Format: Provide email addresses as a quoted, comma-separated list, e.g.:
"user1@example.com","user2@example.com"
Note: Each email must be quoted and separated by commas, no spaces
""",
            required=False
        ),
        Arg(
            name="invite_admins",
            description="""
List of admin email addresses to invite to the organization.
Format: Provide email addresses as a quoted, comma-separated list, e.g.:
"admin1@example.com","admin2@example.com"
Note: Each email must be quoted and separated by commas, no spaces
""",
            required=False
        ),
        Arg(
            name="managed_runner",
            description="Whether to use managed runners for this organization",
            required=False,
            default="false"
        )
    ]
)

# Register the tool
tool_registry.register("terraform_onboarding", terraform_onboarding_tool)

# Export the tool
__all__ = ["terraform_onboarding_tool"]

# Make sure the tool is available at module level
globals()["terraform_onboarding_tool"] = terraform_onboarding_tool 