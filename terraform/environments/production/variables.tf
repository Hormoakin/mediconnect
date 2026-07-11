# ── variables.tf ─────────────────────────────────────────────
variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "ingress_lb_hostname" {
  description = "Hostname of the Kubernetes NGINX Ingress ELB (populated after cluster creation)"
  type        = string
  default     = "PLACEHOLDER_UPDATE_AFTER_CLUSTER_CREATION"
}

variable "cluster_name" {
  description = "Kops Kubernetes cluster name"
  type        = string
  default     = "mediconnect.k8s.local"
}

variable "kops_state_bucket" {
  description = "S3 bucket for Kops state"
  type        = string
  default     = "mediconnect-kops-state-aak"
}

variable "domain_name" {
  description = "Base domain name for MediConnect"
  type        = string
  default     = "mediconnect.salman-aak.com"
}
