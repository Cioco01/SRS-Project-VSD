# modules/cloud-storage/variables.tf

variable "project_id" {
  description = "L'ID del progetto GCP."
  type        = string
}

variable "bucket_name" {
  description = "Nome del bucket Cloud Storage. Deve essere globalmente unico."
  type        = string
}

variable "region" {
  description = "La regione in cui creare il bucket. Può essere una regione o 'US'/'EU'."
  type        = string
}