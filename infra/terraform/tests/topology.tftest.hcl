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
    condition     = length(aws_route53_zone.main) == 0 && length(aws_route53_record.app) == 0
    error_message = "Route 53 resources must remain opt-in."
  }
}

run "optional_paid_features_require_opt_in" {
  command = plan

  variables {
    db_password        = "terraform-test-only-password"
    host_bootstrap_ref = "0123456789abcdef0123456789abcdef01234567"
    enable_multi_az_rds = true
    enable_route53      = true
    domain_name         = "ripple.example"
  }

  assert {
    condition     = aws_db_instance.main.multi_az == true
    error_message = "Multi-AZ RDS should only appear when explicitly enabled."
  }

  assert {
    condition     = length(aws_route53_zone.main) == 1 && length(aws_route53_record.app) == 1
    error_message = "Route 53 resources should only appear when explicitly enabled."
  }
}
