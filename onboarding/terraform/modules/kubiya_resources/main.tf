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
} 