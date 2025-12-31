#############################################################################
# Terraform Configuration for IAM Role: example_role5
# 
# GENERATED USING AWS IAM MCP SERVER AND AWS TERRAFORM MCP SERVER
# Generated: 2025-12-31
#
# This configuration was created by:
# 1. Cloning example_role3_mcp_test configuration
# 2. Applying via awslabs.terraform-mcp-server ExecuteTerraformCommand tool
#
# Role Details:
#   - Role Name: example_role5_mcp_test
#   - Path: /
#   - Trust Principal: glue.amazonaws.com
#   - Max Session Duration: 3600 seconds
#############################################################################

#############################################################################
# IAM Role: example_role5
# 
# This role allows AWS Glue service to assume it for data processing tasks.
# Identical to example_role3_mcp_test.
#############################################################################
resource "aws_iam_role" "example_role5_mcp" {
  name        = "example_role5_mcp_test"
  path        = "/"
  description = "IAM role for AWS Glue - Generated via AWS IAM MCP Server"

  # Maximum session duration in seconds (1 hour)
  max_session_duration = 3600

  # Trust policy (assume role policy)
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

  tags = {
    GeneratedBy = "AWS-IAM-MCP-Server"
    GeneratedAt = "2025-12-31"
  }
}

#############################################################################
# IAM Policy: example_policy5_mcp
# 
# Policy document identical to example_policy3_mcp_test.
#############################################################################
resource "aws_iam_policy" "example_policy5_mcp" {
  name        = "example_policy5_mcp_test"
  path        = "/"
  description = "S3 access policy - Generated via AWS IAM MCP Server"

  # Policy document - same as example_policy3
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

  tags = {
    GeneratedBy = "AWS-IAM-MCP-Server"
    GeneratedAt = "2025-12-31"
  }
}

#############################################################################
# IAM Role Policy Attachment
# 
# Attaches the policy to the role, completing the IAM configuration.
#############################################################################
resource "aws_iam_role_policy_attachment" "example_role5_mcp_attachment" {
  role       = aws_iam_role.example_role5_mcp.name
  policy_arn = aws_iam_policy.example_policy5_mcp.arn
}

#############################################################################
# Outputs
# 
# These outputs can be used to reference the created resources.
#############################################################################
output "role5_mcp_role_arn" {
  description = "ARN of the IAM role created via MCP"
  value       = aws_iam_role.example_role5_mcp.arn
}

output "role5_mcp_role_name" {
  description = "Name of the IAM role created via MCP"
  value       = aws_iam_role.example_role5_mcp.name
}

output "role5_mcp_role_id" {
  description = "Unique ID of the IAM role created via MCP"
  value       = aws_iam_role.example_role5_mcp.unique_id
}

output "role5_mcp_policy_arn" {
  description = "ARN of the IAM policy created via MCP"
  value       = aws_iam_policy.example_policy5_mcp.arn
}
