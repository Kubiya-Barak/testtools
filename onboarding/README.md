# Kubiya Terraform Onboarding Tool

This tool automates the process of onboarding new organizations to Kubiya using Terraform.

## Overview

The tool performs two main operations:
1. Creates a new organization and gets an API token
2. Sets up resources (runner and agent) using the new token

## Files Structure

## Features

- Organization creation with admin user
- Support for inviting additional users and admins
- Automated source integration setup for:
  - Kubernetes
  - GitHub
  - Jenkins
  - Jira
  - Slack

## Prerequisites

- Terraform >= 1.0
- Kubiya API key
- `curl` and `jq` installed on the system running Terraform

## Usage

1. Clone this repository
2. Copy `terraform.tfvars.example` to `terraform.tfvars`
3. Set your Kubiya API key as an environment variable:
   ```bash
   export TF_VAR_kubiya_api_key="your-api-key"
   ```

4. Configure your `terraform.tfvars`:
   ```hcl
   # Organization details
   org_name = "your-org-name"
   admin_email = "admin@your-organization.com"

   # Optional: Invite additional users
   invite_users = [
     "user1@example.com",
     "user2@example.com"
   ]

   # Optional: Invite additional admins
   invite_admins = [
     "admin1@example.com",
     "admin2@example.com"
   ]

   # Runner configuration
   managed_runner = false  # Set to true to use managed runners
   ```

5. Initialize and apply the Terraform configuration:
   ```bash
   terraform init
   terraform apply
   ```

## Variables

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| kubiya_api_key | Kubiya API key for authentication | string | - | yes |
| org_name | Name of the organization to create | string | - | yes |
| admin_email | Email of the organization admin | string | - | yes |
| invite_users | List of user emails to invite | list(string) | [] | no |
| invite_admins | List of admin emails to invite | list(string) | [] | no |
| managed_runner | Enable managed runner | bool | false | no |

## Outputs

The module outputs a sensitive result object containing:
- Organization onboarding status message
- API token (sensitive)
- List of enabled sources

## Source Integration Details

### Kubernetes
- Source: [kubiyabot/community-tools/kubernetes](https://github.com/kubiyabot/community-tools/tree/main/kubernetes)
- Provides Kubernetes cluster management capabilities

### GitHub
- Source: [kubiyabot/community-tools/github](https://github.com/kubiyabot/community-tools/tree/main/github)
- Enables GitHub repository and workflow management

### Jenkins
- Source: [kubiyabot/community-tools/jenkins](https://github.com/kubiyabot/community-tools/tree/main/jenkins)
- Provides Jenkins job management and automation

### Jira
- Source: [kubiyabot/community-tools/jira](https://github.com/kubiyabot/community-tools/tree/main/jira)
- Enables Jira issue and project management

### Slack
- Source: [kubiyabot/community-tools/slack](https://github.com/kubiyabot/community-tools/tree/main/slack)
- Provides Slack integration and notifications

## Error Handling

The module includes error checking and validation:
- Validates API responses
- Ensures token extraction success
- Verifies source integration status

## Security Considerations

- API keys and tokens are marked as sensitive
- Credentials are not logged or exposed in outputs
- Token file is managed securely by Terraform

## Terraform Cloud Integration

This module is configured to work with Terraform Cloud:
```hcl
terraform {
  cloud {
    organization = "Kubiya"
    workspaces {
      name = "Onboarding"
    }
  }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
