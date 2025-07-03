# modules/vpc/variables.tf

variable "project_id" {
  description = "L'ID del progetto GCP."
  type        = string
}

variable "region" {
  description = "La regione GCP per la VPC e le subnet."
  type        = string
}

variable "network_name" {
  description = "Nome della VPC network."
  type        = string
}

variable "subnet_configs" {
  description = "Configurazioni delle subnet (nome, CIDR, descrizione)."
  type = list(object({
    name        = string
    ip_cidr     = string
    description = string
  }))
}