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

resource "kubiya_runner" "runner-dev-cluster" {
  name                     = "runner-dev"
}

resource "kubiya_agent" "kubernetes_crew" {
  depends_on = [kubiya_runner.runner-dev-cluster]
  name         = "test"
  runner       = kubiya_runner.runner-dev-cluster.name
  description  = "AI-powered Kubernetes operations assistant"
  model        = "azure/gpt-4o"
  instructions = ""
  sources      = []
  integrations = ["kubernetes", "slack"]
  users        = []
  groups       = ["Admin"]
  is_debug_mode = true
}
# Outputs
output "source_ids" {
  description = "IDs of created sources"
  value = kubiya_agent.kubernetes_crew.id
} 