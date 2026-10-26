# Copy this file outside source control and replace the placeholders before
# migrating production state. Do not put credentials in this file.
bucket       = "replace-with-private-versioned-state-bucket"
key          = "ripple/production/terraform.tfstate"
region       = "us-east-1"
use_lockfile = true
