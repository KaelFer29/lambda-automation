terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [
    # GitHub OIDC root CA thumbprint (actualizar si AWS/GitHub cambia cadenas)
    "6938fd4d98bab03faadb97b34396831e3780aea1"
  ]
}

resource "aws_iam_role" "gha_oidc" {
  name = "${var.project_name}-gha-oidc"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Federated = aws_iam_openid_connect_provider.github.arn },
      Action = "sts:AssumeRoleWithWebIdentity",
      Condition = {
        StringEquals = { "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com" },
        StringLike = {
          "token.actions.githubusercontent.com:sub" = [
            "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/${var.github_branch}",
            "repo:${var.github_org}/${var.github_repo}:pull_request"
          ]
        }
      }
    }]
  })
}

# Para simplificar, admin completo. Ajusta a mínimo privilegio en producción.
resource "aws_iam_role_policy_attachment" "gha_admin" {
  role       = aws_iam_role.gha_oidc.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

output "role_to_assume" { value = aws_iam_role.gha_oidc.arn }
