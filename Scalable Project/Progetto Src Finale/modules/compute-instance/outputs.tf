
output "attacker_node_01_ip_internal" {
  description = "L'indirizzo IP interno del nodo attaccante."
  value       = google_compute_instance.attacker_node_01.network_interface[0].network_ip
}

output "attacker_node_01_ip_external" {
  description = "L'indirizzo IP esterno del nodo attaccante."
  value       = google_compute_instance.attacker_node_01.network_interface[0].access_config[0].nat_ip
}

output "db_server_01_ip_internal" {
  description = "L'indirizzo IP interno del server DB."
  value       = google_compute_instance.db_server_01.network_interface[0].network_ip
}

output "dns_server_01_ip_internal" {
  description = "L'indirizzo IP interno del server DNS."
  value       = google_compute_instance.dns_server_01.network_interface[0].network_ip
}

output "dns_server_01_ip_external" {
  description = "L'indirizzo IP esterno del server DNS."
  value       = google_compute_instance.dns_server_01.network_interface[0].access_config[0].nat_ip
}

output "internal_client_01_ip_internal" {
  description = "L'indirizzo IP interno del client interno."
  value       = google_compute_instance.internal_client_01.network_interface[0].network_ip
}

output "web_server_01_ip_internal" {
  description = "L'indirizzo IP interno del server web."
  value       = google_compute_instance.web_server_01.network_interface[0].network_ip
}

output "web_server_01_ip_external" {
  description = "L'indirizzo IP esterno del server web."
  value       = google_compute_instance.web_server_01.network_interface[0].access_config[0].nat_ip
}
output "internal_client_01_self_link" {
  description = "Self link of the internal client VM."
  value       = google_compute_instance.internal_client_01.self_link
}

output "db_server_01_self_link" {
  description = "Self link of the DB server VM."
  value       = google_compute_instance.db_server_01.self_link
}

output "dns_server_01_self_link" {
  description = "Self link of the DNS server VM."
  value       = google_compute_instance.dns_server_01.self_link
}

output "web_server_01_self_link" {
  description = "Self link of the web server VM."
  value       = google_compute_instance.web_server_01.self_link
}