import inspect
import sys
from pathlib import Path
import os
import subprocess
import json
from typing import List, Optional
from kubiya_sdk.tools import Tool, Arg, FileSpec, Volume
from kubiya_sdk.tools.registry import tool_registry

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

TERRAFORM_ICON_URL = "https://storage.getlatka.com/images/kubiya.ai.png"

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

# Define Terraform file contents
MAIN_TF = """terraform {
  required_providers {
    http = {
      source  = "hashicorp/http"
      version = "~> 3.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
    kubiya = {
      source = "kubiya-terraform/kubiya"
    }
  }
}

locals {
  base_url = "https://api.kubiya.ai/api"
  api_endpoint = "${local.base_url}/v1/onboard"
}

# Create a file to track if token was created
resource "local_file" "token_file" {
  content  = "placeholder"
  filename = "${path.module}/token.txt"
  lifecycle {
    ignore_changes = [content]
  }
}

# HTTP POST request for organization onboarding
resource "null_resource" "onboard_organization" {
  triggers = {
    org_name = var.org_name
    admin_email = var.admin_email
  }

  provisioner "local-exec" {
    command = <<-EOT
      RESPONSE=$(curl -s -X POST '${local.api_endpoint}' \
      -H "Authorization: UserKey $KUBIYA_API_KEY" \
      -H 'Content-Type: application/json' \
      -d '${jsonencode({
        org_name     = var.org_name
        admin_email  = var.admin_email
        invites     = length(var.invite_users) > 0 || length(var.invite_admins) > 0 ? {
          users  = var.invite_users
          admins = var.invite_admins
        } : null
        set_api_key = true
      })}')

      TOKEN=$(echo $RESPONSE | jq -r '.token')
      if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
        echo "Error: Failed to extract token from response"
        exit 1
      fi

      echo $TOKEN > ${local_file.token_file.filename}
    EOT
    interpreter = ["/bin/bash", "-c"]
    environment = {
      KUBIYA_API_KEY = "$$KUBIYA_API_KEY"
    }
  }
}

# Read the token from the file
data "local_file" "token" {
  depends_on = [null_resource.onboard_organization]
  filename = local_file.token_file.filename
}

# Use the Kubiya resources module
module "kubiya_resources" {
  source = "./modules/kubiya_resources"
  
  depends_on = [data.local_file.token]

  kubiya_runner = "default"
  agent_name    = "kubiya-agent"
  kubiya_groups = []
  
  enable_k8s_source     = var.enable_k8s_source
  enable_github_source  = var.enable_github_source
  enable_jenkins_source = var.enable_jenkins_source
  enable_jira_source    = var.enable_jira_source
  enable_slack_source   = var.enable_slack_source

  providers = {
    kubiya = kubiya
  }
}

# Configure the Kubiya provider with the token
provider "kubiya" {
  # The token will be automatically used from KUBIYA_API_TOKEN environment variable
}

# Output message
output "result" {
  description = "Organization onboarding status"
  sensitive   = true
  value = {
    message = "Organization ${var.org_name} onboarding completed"
    token = data.local_file.token.content
    source_ids = module.kubiya_resources.source_ids
  }
}
"""

VARIABLES_TF = """
variable "org_name" {
  description = "The name of the organization to onboard"
  type        = string
}

variable "admin_email" {
  description = "The email of the organization admin"
  type        = string
}

variable "invite_users" {
  description = "List of user emails to invite to the organization"
  type        = list(string)
  default     = []
}

variable "invite_admins" {
  description = "List of admin emails to invite to the organization"
  type        = list(string)
  default     = []
}

variable "enable_k8s_source" {
  description = "Whether to enable the Kubernetes source"
  type        = bool
  default     = true
}

variable "enable_github_source" {
  description = "Whether to enable the GitHub source"
  type        = bool
  default     = true
}

variable "enable_jenkins_source" {
  description = "Whether to enable the Jenkins source"
  type        = bool
  default     = true
}

variable "enable_jira_source" {
  description = "Whether to enable the Jira source"
  type        = bool
  default     = true
}

variable "enable_slack_source" {
  description = "Whether to enable the Slack source"
  type        = bool
  default     = true
}
"""

MODULE_MAIN_TF = """
terraform {
  required_providers {
    http = {
      source = "hashicorp/http"
      version = "~> 3.0"
    }
    kubiya = {
      source = "kubiya-terraform/kubiya"
    }
  }
}

# Sources
resource "kubiya_source" "kubernetes" {
  count = var.enable_k8s_source ? 1 : 0
  url = "https://github.com/kubiyabot/community-tools/tree/main/kubernetes_v2"
  runner = var.kubiya_runner
}

resource "kubiya_source" "github" {
  count = var.enable_github_source ? 1 : 0
  url = "https://github.com/kubiyabot/community-tools/tree/main/github"
  runner = var.kubiya_runner
}

resource "kubiya_source" "jenkins" {
  count = var.enable_jenkins_source ? 1 : 0
  url = "https://github.com/kubiyabot/community-tools/tree/main/jenkins"
  runner = var.kubiya_runner
}

resource "kubiya_source" "jira" {
  count = var.enable_jira_source ? 1 : 0
  url = "https://github.com/kubiyabot/community-tools/tree/main/jira"
  runner = var.kubiya_runner
}

resource "kubiya_source" "slack" {
  count = var.enable_slack_source ? 1 : 0
  url = "https://github.com/kubiyabot/community-tools/tree/main/slack"
  runner = var.kubiya_runner
}

resource "kubiya_source" "diagramming" {
  url = "https://github.com/kubiyabot/community-tools/tree/main/mermaid"
  runner = var.kubiya_runner
}

# Outputs
output "source_ids" {
  description = "IDs of created sources"
  value = {
    kubernetes = var.enable_k8s_source ? kubiya_source.kubernetes[0].id : null
    github = var.enable_github_source ? kubiya_source.github[0].id : null
    jenkins = var.enable_jenkins_source ? kubiya_source.jenkins[0].id : null
    jira = var.enable_jira_source ? kubiya_source.jira[0].id : null
    slack = var.enable_slack_source ? kubiya_source.slack[0].id : null
    diagramming = kubiya_source.diagramming.id
  }
}
"""

MODULE_VARIABLES_TF = """
variable "kubiya_runner" {
  description = "The Kubiya runner to use for the sources"
  type        = string
}

variable "agent_name" {
  description = "The name of the agent to associate with knowledge resources"
  type        = string
}

variable "kubiya_groups" {
  description = "List of Kubiya groups to associate with knowledge resources"
  type        = list(string)
  default     = []
}

variable "enable_k8s_source" {
  description = "Whether to enable the Kubernetes source"
  type        = bool
  default     = true
}

variable "enable_github_source" {
  description = "Whether to enable the GitHub source"
  type        = bool
  default     = true
}

variable "enable_jenkins_source" {
  description = "Whether to enable the Jenkins source"
  type        = bool
  default     = true
}

variable "enable_jira_source" {
  description = "Whether to enable the Jira source"
  type        = bool
  default     = true
}

variable "enable_slack_source" {
  description = "Whether to enable the Slack source"
  type        = bool
  default     = true
}
"""

class TerraformTool(Tool):
    def __init__(self, name, description, content, args, terraform_dir="/terraform"):
        # Setup Terraform environment and token handling
        setup_script = f"""
set -eu

# Install Python and curl
apk add --no-cache python3 curl jq

cd {terraform_dir}

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
invite_users = ${{invite_users:-[]}}
invite_admins = ${{invite_admins:-[]}}
enable_k8s_source = true
enable_github_source = true
enable_jenkins_source = true
enable_jira_source = true
enable_slack_source = true
EOL
fi

{content}

# Process the output through our Python handler
python3 /opt/scripts/terraform_handler.py
"""

        # Update the main.tf content to fix environment variable access
        main_tf_content = MAIN_TF.replace("${env.KUBIYA_API_KEY}", "${KUBIYA_API_KEY}")
        
        # Update module main.tf to remove redundant provider block
        module_main_tf_content = MODULE_MAIN_TF.replace(
            """provider "kubiya" {
  # API key will be set via KUBIYA_API_TOKEN environment variable
}""",
            ""
        )

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
                # Include all Terraform files with their content
                FileSpec(
                    destination="/terraform/main.tf",
                    content=main_tf_content
                ),
                FileSpec(
                    destination="/terraform/variables.tf",
                    content=VARIABLES_TF
                ),
                FileSpec(
                    destination="/terraform/modules/kubiya_resources/main.tf",
                    content=module_main_tf_content
                ),
                FileSpec(
                    destination="/terraform/modules/kubiya_resources/variables.tf",
                    content=MODULE_VARIABLES_TF
                ),
                # Include the Python handler script
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
            ],
            long_running=False,
            mermaid="""
sequenceDiagram
    participant U as User
    participant T as Terraform Tool
    participant K as Kubiya API

    U->>T: Execute with org details
    T->>T: Create tfvars
    T->>K: Initialize and apply
    K-->>T: Return token
    T->>T: Set KUBIYA_API_TOKEN
    T-->>U: Return status
"""
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
Example: ["user1@example.com", "user2@example.com"]
""",
            required=False
        ),
        Arg(
            name="invite_admins",
            description="""
List of admin email addresses to invite to the organization.
Example: ["admin1@example.com", "admin2@example.com"]
""",
            required=False
        )
    ]
)

# Register the tool
tool_registry.register("terraform_onboarding", terraform_onboarding_tool)

# Export the tool
__all__ = ["terraform_onboarding_tool"]

# Make sure the tool is available at module level
globals()["terraform_onboarding_tool"] = terraform_onboarding_tool 