import os
import subprocess
import json
from typing import List, Optional
from kubiya_sdk.tools import Tool
from kubiya_sdk.tools.registry import tool_registry

class TerraformExecutionError(Exception):
    """Custom exception for Terraform execution errors"""
    pass

def run_terraform_command(command: List[str], cwd: str = None) -> str:
    """
    Execute a Terraform command and return its output
    """
    try:
        result = subprocess.run(
            ["terraform"] + command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise TerraformExecutionError(f"Terraform command failed: {e.stderr}")

def extract_token_from_output(terraform_output: str) -> str:
    """
    Extract the Kubiya API token from Terraform output
    """
    try:
        # Parse the JSON output
        output_data = json.loads(terraform_output)
        return output_data.get("result", {}).get("value", {}).get("token", "")
    except json.JSONDecodeError:
        raise ValueError("Failed to parse Terraform output JSON")

def set_kubiya_api_token(token: str):
    """
    Set the KUBIYA_API_TOKEN environment variable
    """
    os.environ["KUBIYA_API_TOKEN"] = token

# Tool definition
terraform_onboarding_tool = Tool(
    name="terraform_onboarding",
    description="Execute Terraform for Kubiya onboarding and set API token",
    image="hashicorp/terraform:latest",
    content="""
    terraform init && \
    terraform apply -auto-approve && \
    terraform output -json
    """,
    secrets=["KUBIYA_API_KEY"],
    args=[
        {
            "name": "org_name",
            "description": "The name of the organization",
            "type": "str",
            "required": True,
        },
        {
            "name": "admin_email",
            "description": "The email of the organization admin",
            "type": "str",
            "required": True,
        },
        {
            "name": "invite_users",
            "description": "List of user emails to invite",
            "type": "list",
            "required": False,
        },
        {
            "name": "invite_admins",
            "description": "List of admin emails to invite",
            "type": "list",
            "required": False,
        },
        {
            "name": "terraform_dir",
            "description": "Directory containing Terraform files",
            "type": "str",
            "required": True,
        }
    ],
    handler=lambda args: handle_terraform_execution(
        args.get("org_name"),
        args.get("admin_email"),
        args.get("invite_users", []),
        args.get("invite_admins", []),
        args.get("terraform_dir")
    )
)

def handle_terraform_execution(
    org_name: str,
    admin_email: str,
    invite_users: Optional[List[str]] = None,
    invite_admins: Optional[List[str]] = None,
    terraform_dir: str = "terraform"
) -> dict:
    """
    Handle the execution of Terraform commands and token management
    """
    try:
        # Initialize Terraform
        run_terraform_command(["init"], cwd=terraform_dir)
        
        # Create tfvars file content
        tfvars_content = f"""
org_name = "{org_name}"
admin_email = "{admin_email}"
invite_users = {json.dumps(invite_users or [])}
invite_admins = {json.dumps(invite_admins or [])}
enable_k8s_source = true
enable_github_source = true
enable_jenkins_source = true
enable_jira_source = true
enable_slack_source = true
"""
        
        # Write tfvars file
        with open(f"{terraform_dir}/terraform.tfvars", "w") as f:
            f.write(tfvars_content)
        
        # Apply Terraform configuration
        run_terraform_command(["apply", "-auto-approve"], cwd=terraform_dir)
        
        # Get outputs
        output = run_terraform_command(["output", "-json"], cwd=terraform_dir)
        
        # Extract and set token
        token = extract_token_from_output(output)
        if token:
            set_kubiya_api_token(token)
            return {
                "status": "success",
                "message": "Terraform execution completed successfully and API token has been set",
                "token_set": True
            }
        else:
            return {
                "status": "warning",
                "message": "Terraform execution completed but no token was found in the output",
                "token_set": False
            }
            
    except (TerraformExecutionError, ValueError) as e:
        return {
            "status": "error",
            "message": str(e),
            "token_set": False
        }

# Register the tool
tool_registry.register("terraform_onboarding", terraform_onboarding_tool) 