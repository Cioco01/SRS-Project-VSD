
variable "project_id" {
  description = "L'ID del progetto Google Cloud."
  type        = string
}

variable "vpc_self_link" {
  description = "Il self_link della VPC a cui applicare le regole firewall."
  type        = string
}