# modules/cloud-sql/outputs.tf

output "cloudsql_connection_name" {
  description = "Connection name dell'istanza Cloud SQL (per connessioni autorizzate)."
  value       = google_sql_database_instance.main_instance.connection_name
}

output "cloudsql_public_ip_address" {
  description = "Indirizzo IP pubblico dell'istanza Cloud SQL (se abilitato)."
  value       = try(google_sql_database_instance.main_instance.public_ip_address, null)
}

output "cloudsql_private_ip_address" {
  description = "Indirizzo IP privato dell'istanza Cloud SQL (se abilitato)."
  value       = try(google_sql_database_instance.main_instance.private_ip_address, null)
}

output "cloudsql_database_name" {
  description = "Nome del database creato."
  value       = google_sql_database.main_database.name
}

output "cloudsql_user_name" {
  description = "Nome utente creato."
  value       = google_sql_user.main_user.name
}