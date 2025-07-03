# modules/compute-instance/variables.tf

variable "project_id" {
  description = "L'ID del progetto GCP."
  type        = string
}

variable "name" {
  description = "Nome dell'istanza VM."
  type        = string
}

variable "machine_type" {
  description = "Tipo di macchina della VM (es. e2-medium)."
  type        = string
}

variable "zone" {
  description = "La zona GCP dove deployare la VM."
  type        = string
}

variable "image" {
  description = "Immagine di avvio per la VM (es. debian-cloud/debian-11)."
  type        = string
}

variable "subnet_id" {
  description = "Self link della subnet a cui collegare la VM."
  type        = string
}

variable "tags" {
  description = "Lista di tag per l'istanza VM (usati per le regole firewall)."
  type        = list(string)
  default     = []
}

variable "startup_script" {
  description = "Script da eseguire all'avvio della VM."
  type        = string
  default     = ""
}

variable "create_public_ip" {
  description = "Se true, la VM avrà un indirizzo IP pubblico."
  type        = bool
  default     = false
}

# --- NUOVO: Variabili per metadati ---
variable "metadata" {
  description = "A map of metadata keys and values for the instance."
  type        = map(string)
  default     = {}
}

# --- NUOVO: Variabili per Service Account ---
variable "service_account_email" {
  description = "Email of the service account to assign to the instance."
  type        = string
  default     = null # Rendi opzionale se non tutte le VM lo usano
}

variable "service_account_scopes" {
  description = "List of service account scopes."
  type        = list(string)
  default     = ["https://www.googleapis.com/auth/devstorage.read_only", "https://www.googleapis.com/auth/logging.write", "https://www.googleapis.com/auth/monitoring.write", "https://www.googleapis.com/auth/servicecontrol", "https://www.googleapis.com/auth/service.management.readonly", "https://www.googleapis.com/auth/trace.append"] # Scope comuni
}

# Queste variabili sono opzionali, se vuoi configurare chiavi SSH tramite Terraform
# variable "ssh_username" {
#   description = "Nome utente per l'accesso SSH."
#   type        = string
#   default     = "your-ssh-user"
# }

# variable "ssh_public_key_path" {
#   description = "Percorso al file della chiave pubblica SSH."
#   type        = string
#   default     = "~/.ssh/id_rsa.pub"
# }