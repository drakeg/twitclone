variable "aws_region" {
  description = "AWS Region for Ripple production infrastructure."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "production"
}

variable "name_prefix" {
  description = "Prefix used for resource names and tags."
  type        = string
  default     = "ripple"
}

variable "vpc_cidr" {
  description = "CIDR block for the Ripple VPC."
  type        = string
  default     = "10.42.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public application subnet."
  type        = string
  default     = "10.42.10.0/24"
}

variable "private_db_subnet_a_cidr" {
  description = "CIDR block for the first private database subnet."
  type        = string
  default     = "10.42.20.0/24"
}

variable "private_db_subnet_b_cidr" {
  description = "CIDR block for the second private database subnet."
  type        = string
  default     = "10.42.21.0/24"
}

variable "ec2_instance_type" {
  description = "ARM64 EC2 instance type for the application host."
  type        = string
  default     = "t4g.small"
}

variable "ec2_root_volume_gib" {
  description = "Size of the encrypted gp3 root volume."
  type        = number
  default     = 20
}

variable "host_bootstrap_ref" {
  description = "Immutable 40-character Git commit SHA containing the production Compose/deployment artifacts copied onto the EC2 host at first boot. Required before apply."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition     = var.host_bootstrap_ref == null || can(regex("^[0-9a-fA-F]{40}$", var.host_bootstrap_ref))
    error_message = "host_bootstrap_ref must be null or an immutable 40-character Git commit SHA."
  }
}

variable "ssh_admin_cidr" {
  description = "Optional CIDR allowed to SSH to the application host. Leave null to disable SSH ingress."
  type        = string
  default     = null
  nullable    = true
}

variable "db_instance_class" {
  description = "RDS PostgreSQL instance class."
  type        = string
  default     = "db.t4g.micro"
}

variable "postgres_engine_version" {
  description = "PostgreSQL major version required by Ripple production."
  type        = string
  default     = "18"
}

variable "db_allocated_storage_gib" {
  description = "Initial RDS gp3 storage allocation."
  type        = number
  default     = 20
}

variable "db_name" {
  description = "Initial PostgreSQL database name."
  type        = string
  default     = "ripple"
}

variable "db_username" {
  description = "PostgreSQL master username."
  type        = string
  default     = "ripple_admin"
}

variable "db_password" {
  description = "PostgreSQL master password. Supply with TF_VAR_db_password or an untracked tfvars file; never commit it."
  type        = string
  sensitive   = true
}

variable "db_backup_retention_days" {
  description = "RDS automated backup retention period."
  type        = number
  default     = 7
}

variable "db_deletion_protection" {
  description = "Protect the production database from accidental Terraform deletion. Disable deliberately before destroy."
  type        = bool
  default     = true
}

variable "db_skip_final_snapshot" {
  description = "Skip the RDS final snapshot on destroy. Defaults false for safer production teardown."
  type        = bool
  default     = false
}

variable "media_bucket_name" {
  description = "Optional globally unique S3 media bucket name. When null, Terraform derives one from account, region, and environment."
  type        = string
  default     = null
  nullable    = true
}

variable "enable_route53" {
  description = "Create a Route 53 hosted zone and DNS record. Domain registration is never managed here."
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "DNS name used only when enable_route53 is true."
  type        = string
  default     = null
  nullable    = true
}

variable "enable_multi_az_rds" {
  description = "Enable Multi-AZ RDS. Disabled by default because it materially increases recurring cost."
  type        = bool
  default     = false
}
