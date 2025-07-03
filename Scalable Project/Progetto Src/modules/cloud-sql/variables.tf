# modules/cloud-sql/variables.tf

variable "project_id" {
  description = "L'ID del progetto GCP."
  type        = string
}

variable "region" {
  description = "La regione GCP per l'istanza Cloud SQL."
  type        = string
}

variable "database_version" {
  description = "Versione del database Cloud SQL."
  type        = string
}

variable "instance_tier" {
  description = "Tier della macchina per l'istanza Cloud SQL."
  type        = string
}

variable "database_name" {
  description = "Nome del database principale."
  type        = string
}

variable "user_name" {
  description = "Nome utente per l'accesso al DB."
  type        = string
}

variable "user_password" {
  description = "Password per l'utente del DB."
  type        = string
  sensitive   = true
}

variable "authorized_networks" {
  description = "Lista di CIDR IP autorizzati a connettersi a Cloud SQL."
  type        = list(string)
  default     = []
}

variable "private_ip_network" {
  description = "Self link della VPC network per la connessione IP privata di Cloud SQL."
  type        = string
}

variable "db_subnet_name" {
  description = "Nome del range IP allocato per il peering di rete privato con Cloud SQL."
  type        = string
}

variable "private_services_ip_range_name" {
  description = "The name of the allocated IP range for Private Services Access."
  type        = string
}