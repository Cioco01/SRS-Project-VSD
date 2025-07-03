# modules/compute-instance/outputs.tf

output "internal_ip" {
  description = "Indirizzo IP interno della VM."
  value       = google_compute_instance.vm.network_interface[0].network_ip
}

output "public_ip" {
  description = "Indirizzo IP pubblico della VM (se creato)."
  value       = try(google_compute_instance.vm.network_interface[0].access_config[0].nat_ip, null)
}

output "self_link" {
  description = "Self link dell'istanza VM."
  value       = google_compute_instance.vm.self_link
}

