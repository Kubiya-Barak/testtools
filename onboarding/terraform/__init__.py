"""
Terraform configuration for Kubiya onboarding
"""

def get_terraform_content():
    """Get the Terraform configuration content"""
    return {
        "main": {
            "path": "main.tf",
            "content": '''terraform {
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

      TOKEN=$(echo "$RESPONSE" | jq -r '.token')
      if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
        echo "Error: Failed to extract token from response"
        echo "Response was: $RESPONSE"
        exit 1
      fi

      # Save token to file and export it for Kubiya provider
      echo "$TOKEN" > ${local_file.token_file.filename}
      export KUBIYA_API_TOKEN="$TOKEN"
      echo "Exported KUBIYA_API_TOKEN=$TOKEN"
    EOT
    interpreter = ["/bin/sh", "-c"]
  }
}

# Read the token from the file
data "local_file" "token" {
  depends_on = [null_resource.onboard_organization]
  filename = local_file.token_file.filename
}

# Configure the Kubiya provider with the token from onboarding
provider "kubiya" {}

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
'''
        },
        "variables": {
            "path": "variables.tf",
            "content": '''variable "org_name" {
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
'''
        },
        "modules": {
            "kubiya_resources": {
                "main": {
                    "path": "main.tf",
                    "content": '''terraform {
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

provider "kubiya" {}

# Knowledge base data sources
data "http" "kubernetes_security" {
  url = "https://raw.githubusercontent.com/kubiyabot/terraform-modules/refs/heads/main/kubernetes-crew/terraform/knowledge/kubernetes_security.md"
}

data "http" "kubernetes_troubleshooting" {
  url = "https://raw.githubusercontent.com/kubiyabot/terraform-modules/refs/heads/main/kubernetes-crew/terraform/knowledge/kubernetes_troubleshooting.md"
}

data "http" "kubernetes_ops" {
  url = "https://raw.githubusercontent.com/kubiyabot/terraform-modules/refs/heads/main/kubernetes-crew/terraform/knowledge/kubernetes_ops.md"
}

# Sources
resource "kubiya_source" "kubernetes" {
  count = var.enable_k8s_source ? 1 : 0
  url = "https://github.com/kubiyabot/community-tools/tree/main/kubernetes"
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

# Knowledge resources
resource "kubiya_knowledge" "kubernetes_ops" {
  count = var.enable_k8s_source ? 1 : 0
  name             = "Kubernetes Operations and Housekeeping Guide"
  groups           = var.kubiya_groups
  description      = "Knowledge base for Kubernetes housekeeping operations"
  labels           = ["kubernetes", "operations", "housekeeping"]
  supported_agents = [var.agent_name]
  content          = data.http.kubernetes_ops.response_body
}

resource "kubiya_knowledge" "kubernetes_security" {
  count = var.enable_k8s_source ? 1 : 0
  name             = "Kubernetes Security Best Practices"
  groups           = var.kubiya_groups
  description      = "Knowledge base for Kubernetes security practices"
  labels           = ["kubernetes", "security", "best-practices"]
  supported_agents = [var.agent_name]
  content          = data.http.kubernetes_security.response_body
}

resource "kubiya_knowledge" "kubernetes_troubleshooting" {
  count = var.enable_k8s_source ? 1 : 0
  name             = "Kubernetes Troubleshooting Guide"
  groups           = var.kubiya_groups
  description      = "Knowledge base for Kubernetes troubleshooting techniques"
  labels           = ["kubernetes", "troubleshooting", "debugging"]
  supported_agents = [var.agent_name]
  content          = data.http.kubernetes_troubleshooting.response_body
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
}'''
                },
                "variables": {
                    "path": "variables.tf",
                    "content": '''variable "kubiya_runner" {
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
}'''
                }
            }
        }
    }

__all__ = ["get_terraform_content"] 