# modules/vpc/outputs.tf

output "vpc_self_link" {
  description = "Self link della VPC network."
  value       = google_compute_network.main_vpc.self_link
}

output "vpc_name" {
  description = "Nome della VPC network."
  value       = google_compute_network.main_vpc.name
}

output "subnet_self_links" {
  description = "Mappa dei self link e CIDR delle subnet, indicizzati per nome."
  value = {
    for k, v in google_compute_subnetwork.subnets : k => {
      self_link   = v.self_link
      ip_cidr_range = v.ip_cidr_range
    }
  }
}