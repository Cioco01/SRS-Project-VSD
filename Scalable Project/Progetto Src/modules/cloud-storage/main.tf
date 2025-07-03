# modules/cloud-storage/main.tf

resource "google_storage_bucket" "main_bucket" {
  name          = var.bucket_name
  location      = var.region # O "US" se vuoi un bucket multi-region
  project       = var.project_id
  storage_class = "STANDARD" # O NEARLINE, COLDLINE, ARCHIVE

  uniform_bucket_level_access = true

  # Prevenzione di eliminazione accidentale
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 365 # Elimina oggetti più vecchi di 365 giorni
    }
  }

  # Versioning per mantenere le versioni precedenti dei file
  versioning {
    enabled = true
  }

  # Per la sicurezza, blocca l'accesso pubblico a livello di bucket
  public_access_prevention = "enforced"
}