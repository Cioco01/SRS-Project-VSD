
output "bucket_name" {
  description = "Il nome del bucket GCS creato."
  value       = google_storage_bucket.simulation_scripts_bucket.name
}

output "bucket_self_link" {
  description = "Il self_link del bucket GCS creato."
  value       = google_storage_bucket.simulation_scripts_bucket.self_link
}