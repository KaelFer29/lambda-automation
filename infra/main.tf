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

# ECR repository for the Lambda container image
resource "aws_ecr_repository" "repo" {
  name                 = var.function_name
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  encryption_configuration {
    encryption_type = "AES256"
  }
}

# Lambda from container image; created only when image_tag is provided
resource "aws_lambda_function" "this" {
  count            = var.image_tag != "" ? 1 : 0
  function_name    = var.function_name
  package_type     = "Image"
  image_uri        = "${aws_ecr_repository.repo.repository_url}:${var.image_tag}"
  timeout          = 60
  publish          = true

  environment {
    variables = {
      VITACURA_DTE_USER = var.vitacura_dte_user
      VITACURA_DTE_PASS = var.vitacura_dte_pass
    }
  }
}
