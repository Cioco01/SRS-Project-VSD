# modules/vpc/main.tf

resource "google_compute_network" "main_vpc" {
  name                    = var.network_name
  project                 = var.project_id
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "subnets" {
  for_each    = { for sc in var.subnet_configs : sc.name => sc }
  name        = each.value.name
  ip_cidr_range = each.value.ip_cidr
  region      = var.region
  network     = google_compute_network.main_vpc.id
  description = each.value.description
}