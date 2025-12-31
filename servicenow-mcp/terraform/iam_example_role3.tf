#############################################################################
# Terraform Configuration for IAM Role: example_role3
# 
# This configuration recreates the IAM role with ARN:
#   arn:aws:iam::175853813947:role/example_role3
#
# Role Details:
#   - Name: example_role3
#   - Path: /
#   - Max Session Duration: 3600 seconds (1 hour)
#   - Trust Policy: Allows AWS Glue service to assume this role
#   - Attached Managed Policy: example_policy3 (custom policy for S3 access)
#   - Inline Policies: None
#   - Tags: None
#
# Generated: 2025-12-31
#############################################################################

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }
  }
}

#############################################################################
# Provider Configuration
# Uncomment and configure as needed for your environment
#############################################################################
# provider "aws" {
#   region  = "us-east-1"
#   profile = "default"
# }

#############################################################################
# IAM Role: example_role3
# 
# This role is designed for AWS Glue service to assume.
# It grants permissions for Glue jobs to access specific S3 resources.
#############################################################################
resource "aws_iam_role" "example_role3" {
  name        = "example_role3"
  path        = "/"
  description = "IAM role for AWS Glue service to access S3 resources"

  # Maximum session duration in seconds (1 hour)
  max_session_duration = 3600

  # Trust policy (assume role policy)
  # Allows the AWS Glue service to assume this role
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  # Tags (none configured on the original role)
  tags = {}
}

#############################################################################
# IAM Policy: example_policy3
# 
# Custom managed policy that grants S3 GetObject and PutObject permissions
# on a specific S3 bucket and object prefix.
#############################################################################
resource "aws_iam_policy" "example_policy3" {
  name        = "example_policy3"
  path        = "/"
  description = "Policy granting S3 access to whizlabs12 bucket for sample_data.csv"

  # Policy document with S3 permissions
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "arn:aws:s3:::whizlabs12/sample_data.csv*"
        ]
      }
    ]
  })

  # Tags (none configured on the original policy)
  tags = {}
}

#############################################################################
# IAM Role Policy Attachment
# 
# Attaches the example_policy3 managed policy to the example_role3 role.
#############################################################################
resource "aws_iam_role_policy_attachment" "example_role3_policy_attachment" {
  role       = aws_iam_role.example_role3.name
  policy_arn = aws_iam_policy.example_policy3.arn
}

#############################################################################
# Outputs
# 
# Useful outputs for referencing this role in other Terraform configurations
# or for verification purposes.
#############################################################################
output "role_arn" {
  description = "ARN of the IAM role"
  value       = aws_iam_role.example_role3.arn
}

output "role_name" {
  description = "Name of the IAM role"
  value       = aws_iam_role.example_role3.name
}

output "role_id" {
  description = "Unique ID of the IAM role"
  value       = aws_iam_role.example_role3.unique_id
}

output "policy_arn" {
  description = "ARN of the IAM policy"
  value       = aws_iam_policy.example_policy3.arn
}
