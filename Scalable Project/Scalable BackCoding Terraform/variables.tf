#VARIABLES
variable "gcp_project_id" {
  description = "L'ID del progetto Google Cloud."
  type        = string
}

variable "gcp_region" {
  description = "La regione predefinita per le risorse GCP."
  type        = string
  default     = "europe-west1"
}

variable "gcp_zone" {
  description = "La zona predefinita per le risorse Compute e SQL."
  type        = string
  default     = "europe-west1-b"
}

variable "sql_simuser_password" {
  description = "La password per l'utente 'simuser' del database Cloud SQL."
  type        = string
  sensitive   = true
}

variable "client_vm_sa_email" {
  description = "L'email del Service Account per le VM client (Attacker e Internal Client)."
  type        = string
  default     = "client-vm-sa@<YOUR_PROJECT_ID>.iam.gserviceaccount.com" # CAMBIA <YOUR_PROJECT_ID>
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

variable "db_server_ip_metadata" {
  description = "IP del DB server per i metadata del client interno."
  type        = string
  default     = "10.0.3.2" # IP interno del db-server-01
}

variable "dns_server_ip_metadata" {
  description = "IP del DNS server per i metadata del client interno."
  type        = string
  default     = "10.0.1.2"
}

variable "gcs_scripts_bucket_name_metadata" {
  description = "Nome del bucket GCS per gli script nei metadata."
  type        = string
  default     = "gruppo-9-456912-gcs-bucket" # Sostituisci con il nome del bucket che hai usato/vuoi usare
}

variable "web_server_ip_metadata" {
  description = "IP del Web server per i metadata del client interno."
  type        = string
  default     = "10.0.1.4"
}