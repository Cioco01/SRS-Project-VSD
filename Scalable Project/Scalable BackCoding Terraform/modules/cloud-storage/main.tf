
resource "google_storage_bucket" "simulation_scripts_bucket" {
  name          = var.bucket_name
  project       = var.project_id
  location      = var.region
  force_destroy = false # ATTENZIONE: Questo permette la cancellazione del bucket anche se non vuoto. Utile per simulazioni.
  uniform_bucket_level_access = true # Migliore per la sicurezza
}