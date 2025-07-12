
variable "project_id" {
  description = "L'ID del progetto Google Cloud."
  type        = string
}

variable "region" {
  description = "La regione GCP per le risorse di rete."
  type        = string
}

variable "vpc_name" {
  description = "Il nome della VPC da creare."
  type        = string
}