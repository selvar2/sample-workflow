#############################################################################
# Terraform Configuration for IAM Role: example_role3
# 
# GENERATED USING AWS IAM MCP SERVER AND AWS TERRAFORM MCP SERVER
# Generated: 2025-12-31
#
# This configuration was created by:
# 1. Querying awslabs.iam-mcp-server list_roles tool to get role details
# 2. Querying awslabs.iam-mcp-server get_managed_policy_document tool
# 3. Validating with terraform validate
#
# Role Details Retrieved via MCP:
#   - Role Name: example_role3
#   - ARN: arn:aws:iam::175853813947:role/example_role3
#   - Path: /
#   - Trust Principal: glue.amazonaws.com
#   - Max Session Duration: 3600 seconds
#############################################################################

#############################################################################
# IAM Role: example_role3
# 
# This role allows AWS Glue service to assume it for data processing tasks.
# Trust policy retrieved via awslabs.iam-mcp-server list_roles tool.
#############################################################################
resource "aws_iam_role" "example_role3_mcp" {
  name        = "example_role3_mcp_test"
  path        = "/"
  description = "IAM role for AWS Glue - Generated via AWS IAM MCP Server"

  # Maximum session duration in seconds (1 hour)
  max_session_duration = 3600

  # Trust policy (assume role policy)
  # Retrieved via awslabs.iam-mcp-server list_roles tool
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
# IAM Policy: example_policy3_mcp
# 
# Policy document retrieved via awslabs.iam-mcp-server 
# get_managed_policy_document tool with policy_arn parameter.
#
# MCP Tool Call:
#   tool: get_managed_policy_document
#   arguments: {policy_arn: "arn:aws:iam::175853813947:policy/example_policy3"}
#
# Response included:
#   - policy_name: example_policy3
#   - version_id: v4
#   - is_default_version: true
#############################################################################
resource "aws_iam_policy" "example_policy3_mcp" {
  name        = "example_policy3_mcp_test"
  path        = "/"
  description = "S3 access policy - Generated via AWS IAM MCP Server"

  # Policy document retrieved via get_managed_policy_document MCP tool
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
resource "aws_iam_role_policy_attachment" "example_role3_mcp_attachment" {
  role       = aws_iam_role.example_role3_mcp.name
  policy_arn = aws_iam_policy.example_policy3_mcp.arn
}

#############################################################################
# Outputs
# 
# These outputs can be used to reference the created resources.
#############################################################################
output "mcp_role_arn" {
  description = "ARN of the IAM role created via MCP"
  value       = aws_iam_role.example_role3_mcp.arn
}

output "mcp_role_name" {
  description = "Name of the IAM role created via MCP"
  value       = aws_iam_role.example_role3_mcp.name
}

output "mcp_role_id" {
  description = "Unique ID of the IAM role created via MCP"
  value       = aws_iam_role.example_role3_mcp.unique_id
}

output "mcp_policy_arn" {
  description = "ARN of the IAM policy created via MCP"
  value       = aws_iam_policy.example_policy3_mcp.arn
}
