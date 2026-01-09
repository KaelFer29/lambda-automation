variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "function_name" {
  description = "Nombre de la función Lambda"
  type        = string
  default     = "dte-fetcher-lambda"
}

variable "vitacura_dte_user" {
  description = "Usuario para login en DTE Detail"
  type        = string
  default     = ""
}

variable "vitacura_dte_pass" {
  description = "Password para login en DTE Detail"
  type        = string
  default     = ""
}
