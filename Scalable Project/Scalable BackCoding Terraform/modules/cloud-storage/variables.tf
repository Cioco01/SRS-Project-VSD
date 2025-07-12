
variable "project_id" {
  description = "L'ID del progetto Google Cloud."
  type        = string
}

variable "region" {
  description = "La regione del bucket GCS."
  type        = string
}

variable "bucket_name" {
  description = "Il nome del bucket GCS da creare."
  type        = string
  
}
