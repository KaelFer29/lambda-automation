terraform {
  backend "s3" {
    bucket         = "lambda-automation-terraform-state-1767808613"
    key            = "infra/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
