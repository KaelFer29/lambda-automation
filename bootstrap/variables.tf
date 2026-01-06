variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
  default     = "lambda-automation"
}

variable "github_org" {
  description = "Organización o usuario de GitHub"
  type        = string
}

variable "github_repo" {
  description = "Nombre del repositorio en GitHub"
  type        = string
}

variable "github_branch" {
  description = "Rama permitida para asumir el rol"
  type        = string
  default     = "main"
}
