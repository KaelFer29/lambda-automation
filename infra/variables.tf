variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "function_name" {
  description = "Nombre de la función Lambda"
  type        = string
  default     = "hello-lambda"
}
