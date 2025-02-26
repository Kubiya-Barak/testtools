terraform {
  required_providers {
    http = {
      source  = "hashicorp/http"
      version = "~> 3.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
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
      # Make the initial request and store the full response
      RESPONSE=$(curl -s -X POST '${local.api_endpoint}' \
      -H 'Authorization: UserKey ${env.KUBIYA_API_KEY}' \
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

      # Print response for debugging
      echo "Full Response:"
      echo $RESPONSE | jq '.'

      # Extract and verify token
      TOKEN=$(echo $RESPONSE | jq -r '.token')
      if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
        echo "Error: Failed to extract token from response"
        exit 1
      fi

      echo "Token extracted successfully"
      echo $TOKEN > ${local_file.token_file.filename}

      # Print status and response
      echo "HTTP/1.1 200 OK"
      echo $RESPONSE | jq '.'
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}

# Read the token from the file
data "local_file" "token" {
  depends_on = [null_resource.onboard_organization]
  filename = local_file.token_file.filename
}

# Add Kubernetes source if enabled
resource "null_resource" "add_k8s_source" {
  count = var.enable_k8s_source ? 1 : 0
  depends_on = [data.local_file.token]

  provisioner "local-exec" {
    command = <<-EOT
      # Debug: Print token content
      echo "Using token from file:"
      cat ${local_file.token_file.filename}
      
      # Make the request
      curl -s -X POST '${local.base_url}/sources' \
      -H "Authorization: UserKey $(cat ${local_file.token_file.filename})" \
      -H 'Content-Type: application/json' \
      -d '{
        "name": "Kubernetes",
        "url": "https://github.com/kubiyabot/community-tools/tree/main/kubernetes",
        "dynamic_config": {}
      }' \
      -i | grep -E 'HTTP/|{'
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}

# Add GitHub source if enabled
resource "null_resource" "add_github_source" {
  count = var.enable_github_source ? 1 : 0
  depends_on = [data.local_file.token]

  provisioner "local-exec" {
    command = <<-EOT
      curl -s -X POST '${local.base_url}/sources' \
      -H "Authorization: UserKey $(cat ${local_file.token_file.filename})" \
      -H 'Content-Type: application/json' \
      -d '{
        "name": "GitHub",
        "url": "https://github.com/kubiyabot/community-tools/tree/main/github",
        "dynamic_config": {}
      }' \
      -i | grep -E 'HTTP/|{'
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}

# Add Jenkins source if enabled
resource "null_resource" "add_jenkins_source" {
  count = var.enable_jenkins_source ? 1 : 0
  depends_on = [data.local_file.token]

  provisioner "local-exec" {
    command = <<-EOT
      curl -s -X POST '${local.base_url}/sources' \
      -H "Authorization: UserKey $(cat ${local_file.token_file.filename})" \
      -H 'Content-Type: application/json' \
      -d '{
        "name": "Jenkins",
        "url": "https://github.com/kubiyabot/community-tools/tree/main/jenkins",
        "dynamic_config": {}
      }' \
      -i | grep -E 'HTTP/|{'
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}

# Add Jira source if enabled
resource "null_resource" "add_jira_source" {
  count = var.enable_jira_source ? 1 : 0
  depends_on = [data.local_file.token]

  provisioner "local-exec" {
    command = <<-EOT
      curl -s -X POST '${local.base_url}/sources' \
      -H "Authorization: UserKey $(cat ${local_file.token_file.filename})" \
      -H 'Content-Type: application/json' \
      -d '{
        "name": "Jira",
        "url": "https://github.com/kubiyabot/community-tools/tree/main/jira",
        "dynamic_config": {}
      }' \
      -i | grep -E 'HTTP/|{'
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}

# Add Slack source if enabled
resource "null_resource" "add_slack_source" {
  count = var.enable_slack_source ? 1 : 0
  depends_on = [data.local_file.token]

  provisioner "local-exec" {
    command = <<-EOT
      curl -s -X POST '${local.base_url}/sources' \
      -H "Authorization: UserKey $(cat ${local_file.token_file.filename})" \
      -H 'Content-Type: application/json' \
      -d '{
        "name": "Slack",
        "url": "https://github.com/kubiyabot/community-tools/tree/main/slack",
        "dynamic_config": {}
      }' \
      -i | grep -E 'HTTP/|{'
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}

# Output message
output "result" {
  description = "Organization onboarding status"
  sensitive   = true
  value = {
    message = "Organization ${var.org_name} onboarding completed. Check the output above for status code and response."
    token = data.local_file.token.content
    enabled_sources = {
      kubernetes = var.enable_k8s_source
      github = var.enable_github_source
      jenkins = var.enable_jenkins_source
      jira = var.enable_jira_source
      slack = var.enable_slack_source
    }
  }
}
