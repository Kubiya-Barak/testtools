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

      # Print response for debugging
      echo "Full Response:"
      echo "$RESPONSE" | jq '.'

      # Extract and verify token
      TOKEN=$(echo "$RESPONSE" | jq -r '.token')
      if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
        echo "Error: Failed to extract token from response"
        echo "Response was: $RESPONSE"
        exit 1
      fi

      # Export the new token for Kubiya provider
      # Save token to file and export it for Kubiya provider
      echo "$TOKEN" > ${local_file.token_file.filename}
      echo "Successfully obtained and exported new API token"
    EOT
    interpreter = ["/bin/sh", "-c"]
  }
}

# Read the token from the file
data "local_file" "token" {
  depends_on = [null_resource.onboard_organization]
  filename = local_file.token_file.filename
}

# Output message
output "result" {
  description = "Organization onboarding status"
  sensitive   = true
  value = {
    message = "Organization ${var.org_name} onboarding completed. Check the output above for status code and response."
  }
}
