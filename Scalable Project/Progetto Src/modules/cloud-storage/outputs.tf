# modules/cloud-storage/outputs.tf

output "gcs_bucket_url" {
  description = "URL del bucket Cloud Storage."
  value       = google_storage_bucket.main_bucket.self_link
}

output "gcs_bucket_name" {
  description = "Nome del bucket Cloud Storage."
  value       = google_storage_bucket.main_bucket.name
}