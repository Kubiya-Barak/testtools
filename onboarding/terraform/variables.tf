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

variable "managed_runner" {
  description = "Whether to create a managed runner for the organization"
  type        = bool
  default     = false
}
