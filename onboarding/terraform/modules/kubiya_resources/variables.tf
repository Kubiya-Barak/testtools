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