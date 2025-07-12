
variable "project_id" {
  description = "L'ID del progetto Google Cloud."
  type        = string
}

variable "region" {
  description = "La regione GCP per Cloud SQL."
  type        = string
}

variable "zone" {
  description = "La zona GCP per Cloud SQL."
  type        = string
}

variable "vpc_self_link" {
  description = "Il self_link della VPC per la connessione privata."
  type        = string
}

variable "sql_simuser_password" {
  description = "La password per l'utente 'simuser' del database Cloud SQL."
  type        = string
  sensitive   = true
}

variable "sql_db_tier" {
  description = "Il tier (tipo di macchina) per l'istanza Cloud SQL."
  type        = string
  default     = "db-e2-micro"
}

variable "sql_db_disk_size" {
  description = "La dimensione del disco (GB) per l'istanza Cloud SQL."
  type        = number
  default     = 10
}

variable "sql_db_disk_type" {
  description = "Il tipo di disco per l'istanza Cloud SQL (SSD o HDD)."
  type        = string
  default     = "SSD"
}