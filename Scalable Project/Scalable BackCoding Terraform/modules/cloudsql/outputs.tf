
output "instance_connection_name" {
  description = "Il nome di connessione dell'istanza Cloud SQL."
  value       = google_sql_database_instance.simulation_db_instance.connection_name
}

output "instance_private_ip" {
  description = "L'indirizzo IP privato dell'istanza Cloud SQL."
  value       = google_sql_database_instance.simulation_db_instance.private_ip_address
}

output "instance_public_ip" {
  description = "L'indirizzo IP pubblico dell'istanza Cloud SQL."
  value       = google_sql_database_instance.simulation_db_instance.public_ip_address
}

output "database_name" {
  description = "Il nome del database creato in Cloud SQL."
  value       = google_sql_database.simulation_data_db.name
}

output "simuser_username" {
  description = "Il nome utente per il database simuser."
  value       = google_sql_user.sim_user.name
}