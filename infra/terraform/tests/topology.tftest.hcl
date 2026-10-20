mock_provider "aws" {
  override_during = plan

  override_data {
    target = data.aws_caller_identity.current
    values = {
      account_id = "123456789012"
    }
  }

  override_data {
    target = data.aws_availability_zones.available
    values = {
      names = ["us-east-1a", "us-east-1b"]
    }
  }

  override_data {
    target = data.aws_ssm_parameter.al2023_arm64
    values = {
      value = "ami-0123456789abcdef0"
    }
  }
  override_data {
    target = data.aws_iam_policy_document.ec2_assume_role
    values = {
      json = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":\"sts:AssumeRole\",\"Principal\":{\"Service\":\"ec2.amazonaws.com\"}}]}"
    }
  }

  override_data {
    target = data.aws_iam_policy_document.media_access
    values = {
      json = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"s3:ListBucket\"],\"Resource\":[\"arn:aws:s3:::ripple-test-media\"]},{\"Effect\":\"Allow\",\"Action\":[\"s3:GetObject\",\"s3:PutObject\",\"s3:DeleteObject\"],\"Resource\":[\"arn:aws:s3:::ripple-test-media/*\"]}]}"
    }
  }

}

run "default_low_cost_topology" {
  command = plan

  variables {
    db_password        = "terraform-test-only-password"
    host_bootstrap_ref = "0123456789abcdef0123456789abcdef01234567"
  }

  assert {
    condition     = aws_instance.app.instance_type == "t4g.small"
    error_message = "The default application host must remain t4g.small."
  }

  assert {
    condition     = aws_instance.app.metadata_options[0].http_tokens == "required"
    error_message = "The application host must require IMDSv2 tokens."
  }

  assert {
    condition     = aws_db_instance.main.instance_class == "db.t4g.micro"
    error_message = "The default database must remain db.t4g.micro."
  }

  assert {
    condition     = aws_db_instance.main.publicly_accessible == false
    error_message = "The production database must remain private."
  }

  assert {
    condition     = aws_db_instance.main.multi_az == false
    error_message = "Multi-AZ RDS must remain disabled by default."
  }

  assert {
    condition     = aws_s3_bucket_versioning.media.versioning_configuration[0].status == "Enabled"
    error_message = "Production media versioning must remain enabled."
  }

  assert {
    condition     = aws_s3_bucket_public_access_block.media.block_public_acls && aws_s3_bucket_public_access_block.media.block_public_policy && aws_s3_bucket_public_access_block.media.ignore_public_acls && aws_s3_bucket_public_access_block.media.restrict_public_buckets
    error_message = "Production media must block every form of public S3 access."
  }

  assert {
    condition = length([
      for rule in aws_s3_bucket_server_side_encryption_configuration.media.rule : rule
      if length([
        for encryption in rule.apply_server_side_encryption_by_default : encryption
        if encryption.sse_algorithm == "AES256"
      ]) == 1
    ]) == 1
    error_message = "Production media must remain encrypted at rest."
  }

  assert {
    condition     = aws_instance.app.root_block_device[0].encrypted == true
    error_message = "The application host root volume must remain encrypted."
  }

  assert {
    condition     = aws_db_instance.main.storage_encrypted == true
    error_message = "The production database storage must remain encrypted."
  }

  assert {
    condition     = aws_subnet.db_a.availability_zone != aws_subnet.db_b.availability_zone
    error_message = "RDS subnet group members must remain in distinct availability zones."
  }

  assert {
    condition = length([
      for rule in aws_security_group.db.ingress : rule
      if rule.from_port == 5432
      && rule.to_port == 5432
      && rule.protocol == "tcp"
      && length(rule.security_groups) == 1
      && length(rule.cidr_blocks) == 0
      && length(rule.ipv6_cidr_blocks) == 0
      && length(rule.prefix_list_ids) == 0
    ]) == 1 && length(aws_security_group.db.ingress) == 1
    error_message = "PostgreSQL ingress must remain limited to exactly one security-group source and expose no CIDR-based access."
  }

  assert {
    condition     = length(aws_route53_zone.main) == 0 && length(aws_route53_record.app) == 0
    error_message = "Route 53 resources must remain opt-in."
  }

  assert {
    condition     = length([for rule in aws_security_group.app.ingress : rule if rule.from_port == 22]) == 0
    error_message = "SSH ingress must remain disabled by default."
  }
}

run "bootstrap_ref_is_required_for_host_plan" {
  command = plan

  variables {
    db_password = "terraform-test-only-password"
  }

  expect_failures = [
    aws_instance.app,
  ]
}

run "optional_paid_features_require_opt_in" {
  command = plan

  variables {
    db_password        = "terraform-test-only-password"
    host_bootstrap_ref = "0123456789abcdef0123456789abcdef01234567"
    enable_multi_az_rds = true
    enable_route53      = true
    domain_name         = "ripple.example"
    ssh_admin_cidr      = "203.0.113.10/32"
  }

  assert {
    condition     = aws_db_instance.main.multi_az == true
    error_message = "Multi-AZ RDS should only appear when explicitly enabled."
  }

  assert {
    condition     = length(aws_route53_zone.main) == 1 && length(aws_route53_record.app) == 1
    error_message = "Route 53 resources should only appear when explicitly enabled."
  }

  assert {
    condition     = length([for rule in aws_security_group.app.ingress : rule if rule.from_port == 22 && contains(rule.cidr_blocks, "203.0.113.10/32")]) == 1
    error_message = "SSH ingress should only appear for the explicitly configured administration CIDR."
  }
}
