
variable "project_id" {
  description = "L'ID del progetto Google Cloud."
  type        = string
}

variable "zone" {
  description = "La zona GCP per le VM."
  type        = string
}

variable "dmz_subnet_self_link" {
  description = "Il self_link della subnet DMZ."
  type        = string
}

variable "internal_subnet_self_link" {
  description = "Il self_link della subnet interna."
  type        = string
}

variable "db_subnet_self_link" {
  description = "Il self_link della subnet DB."
  type        = string
}

variable "client_vm_sa_email" {
  description = "L'email del Service Account per le VM client."
  type        = string
}

# Variabili per i metadata dell'internal-client
variable "db_server_ip_metadata" {
  description = "IP del DB server per i metadata del client interno."
  type        = string
}

variable "dns_server_ip_metadata" {
  description = "IP del DNS server per i metadata del client interno."
  type        = string
}

variable "gcs_scripts_bucket_name_metadata" {
  description = "Nome del bucket GCS per gli script nei metadata."
  type        = string
}

variable "web_server_ip_metadata" {
  description = "IP del Web server per i metadata del client interno."
  type        = string
}