output "vpc_id" {
  description = "Ripple production VPC ID."
  value       = aws_vpc.main.id
}

output "application_instance_id" {
  description = "EC2 instance ID for the Ripple application host."
  value       = aws_instance.app.id
}

output "application_public_ipv4" {
  description = "Stable public IPv4 address assigned to the application host."
  value       = aws_eip.app.public_ip
}

output "database_endpoint" {
  description = "Private RDS PostgreSQL endpoint hostname."
  value       = aws_db_instance.main.address
}

output "database_port" {
  description = "Private PostgreSQL port."
  value       = aws_db_instance.main.port
}

output "media_bucket_name" {
  description = "Private S3 bucket used for Ripple production media."
  value       = aws_s3_bucket.media.bucket
}

output "application_iam_role_name" {
  description = "IAM role attached to the application host for private media access."
  value       = aws_iam_role.app.name
}

output "route53_name_servers" {
  description = "Route 53 name servers when DNS is enabled; empty otherwise. Domain registration is not managed here."
  value       = var.enable_route53 ? aws_route53_zone.main[0].name_servers : []
}
