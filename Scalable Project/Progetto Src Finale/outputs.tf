#OUTPUTS

# Output dal modulo VPC
output "vpc_name" {
  description = "Il nome della rete VPC creata."
  value       = module.vpc.vpc_name
}

output "dmz_subnet_self_link" {
  description = "Il self_link della subnet DMZ."
  value       = module.vpc.dmz_subnet_self_link
}

output "internal_subnet_self_link" {
  description = "Il self_link della subnet interna."
  value       = module.vpc.internal_subnet_self_link
}

output "db_subnet_self_link" {
  description = "Il self_link della subnet DB."
  value       = module.vpc.db_subnet_self_link
}

# Output dal modulo Cloud Storage
output "gcs_bucket_name" {
  description = "Il nome del bucket GCS creato per gli script."
  value       = module.cloud_storage.bucket_name
}

# Output dal modulo Compute Instance
output "attacker_node_01_ip_internal" {
  description = "L'indirizzo IP interno del nodo attaccante."
  value       = module.compute_instance.attacker_node_01_ip_internal
}

output "attacker_node_01_ip_external" {
  description = "L'indirizzo IP esterno del nodo attaccante."
  value       = module.compute_instance.attacker_node_01_ip_external
}

output "db_server_01_ip_internal" {
  description = "L'indirizzo IP interno del server DB."
  value       = module.compute_instance.db_server_01_ip_internal
}

output "dns_server_01_ip_internal" {
  description = "L'indirizzo IP interno del server DNS."
  value       = module.compute_instance.dns_server_01_ip_internal
}

output "dns_server_01_ip_external" {
  description = "L'indirizzo IP esterno del server DNS."
  value       = module.compute_instance.dns_server_01_ip_external
}

output "internal_client_01_ip_internal" {
  description = "L'indirizzo IP interno del client interno."
  value       = module.compute_instance.internal_client_01_ip_internal
}

output "web_server_01_ip_internal" {
  description = "L'indirizzo IP interno del server web."
  value       = module.compute_instance.web_server_01_ip_internal
}

output "web_server_01_ip_external" {
  description = "L'indirizzo IP esterno del server web."
  value       = module.compute_instance.web_server_01_ip_external
}

# Output dal modulo Cloud SQL
output "cloudsql_instance_connection_name" {
  description = "Il nome di connessione dell'istanza Cloud SQL."
  value       = module.cloud_sql.instance_connection_name
}

output "cloudsql_instance_private_ip" {
  description = "L'indirizzo IP privato dell'istanza Cloud SQL."
  value       = module.cloud_sql.instance_private_ip
}

output "cloudsql_instance_public_ip" {
  description = "L'indirizzo IP pubblico dell'istanza Cloud SQL."
  value       = module.cloud_sql.instance_public_ip
}

output "cloudsql_database_name" {
  description = "Il nome del database creato in Cloud SQL."
  value       = module.cloud_sql.database_name
}

output "cloudsql_simuser_username" {
  description = "Il nome utente per il database simuser."
  value       = module.cloud_sql.simuser_username
}

# Output dal modulo Packet Mirroring
output "packet_mirroring_policy_self_link" {
  description = "Self link (ID) of the Packet Mirroring Policy."
  value       = google_compute_packet_mirroring.security_sim_packet_mirroring_policy.id
}

output "packet_mirroring_collector_ilb_forwarding_rule_self_link" {
  description = "Self link of the Internal Load Balancer forwarding rule used as Packet Mirroring collector."
  value       = google_compute_forwarding_rule.packet_mirroring_collector_forwarding_rule.self_link
}

output "packet_mirroring_collector_ilb_ip" {
  description = "IP address of the Internal Load Balancer forwarding rule used as Packet Mirroring collector."
  value       = google_compute_forwarding_rule.packet_mirroring_collector_forwarding_rule.ip_address
}