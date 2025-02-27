"""Main Terraform configuration for Kubiya onboarding."""

CONTENT = '''terraform {
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

      echo "$TOKEN" > ${local_file.token_file.filename}
    EOT
    interpreter = ["/bin/sh", "-c"]
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
''' 