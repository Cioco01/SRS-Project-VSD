
output "vpc_self_link" {
  description = "Il self_link della VPC creata."
  value       = google_compute_network.security_sim_vpc.self_link
}

output "dmz_subnet_self_link" {
  description = "Il self_link della subnet DMZ."
  value       = google_compute_subnetwork.dmz_subnet.self_link
}

output "internal_subnet_self_link" {
  description = "Il self_link della subnet interna."
  value       = google_compute_subnetwork.internal_subnet.self_link
}

output "db_subnet_self_link" {
  description = "Il self_link della subnet DB."
  value       = google_compute_subnetwork.db_subnet.self_link
}

output "vpc_name" {
  description = "Il nome della VPC creata."
  value       = google_compute_network.security_sim_vpc.name
}