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

provider "kubiya" {
  # API key will be set via KUBIYA_API_TOKEN environment variable
}
# Sources
resource "kubiya_source" "kubernetes" {
  count = var.enable_k8s_source ? 1 : 0
  name = "kubernetes-source"
  url = "https://github.com/kubiyabot/community-tools/tree/main/kubernetes"
  runner = var.kubiya_runner
  dynamic_config = jsonencode({})
}

resource "kubiya_source" "github" {
  count = var.enable_github_source ? 1 : 0
  name = "github-source"
  url = "https://github.com/kubiyabot/community-tools/tree/main/github"
  runner = var.kubiya_runner
  dynamic_config = jsonencode({})
}

resource "kubiya_source" "jenkins" {
  count = var.enable_jenkins_source ? 1 : 0
  name = "jenkins-source"
  url = "https://github.com/kubiyabot/community-tools/tree/main/jenkins"
  runner = var.kubiya_runner
  dynamic_config = jsonencode({})
}

resource "kubiya_source" "jira" {
  count = var.enable_jira_source ? 1 : 0
  name = "jira-source"
  url = "https://github.com/kubiyabot/community-tools/tree/main/jira"
  runner = var.kubiya_runner
  dynamic_config = jsonencode({})
}

resource "kubiya_source" "slack" {
  count = var.enable_slack_source ? 1 : 0
  name = "slack-source"
  url = "https://github.com/kubiyabot/community-tools/tree/main/slack"
  runner = var.kubiya_runner
  dynamic_config = jsonencode({})
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
  }
} 