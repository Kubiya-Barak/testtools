variable "kubiya_api_key" {
  description = "Kubiya API key for authentication (set via TF_VAR_kubiya_api_key environment variable)"
  type        = string
  sensitive   = true
}

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
  default     = false
}

variable "enable_github_source" {
  description = "Whether to enable the GitHub source"
  type        = bool
  default     = false
}

variable "enable_jenkins_source" {
  description = "Whether to enable the Jenkins source"
  type        = bool
  default     = false
}

variable "enable_jira_source" {
  description = "Whether to enable the Jira source"
  type        = bool
  default     = false
}

variable "enable_slack_source" {
  description = "Whether to enable the Slack source"
  type        = bool
  default     = false
}
