
resource "google_compute_network" "security_sim_vpc" {
  name                    = var.vpc_name
  project                 = var.project_id
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "dmz_subnet" {
  name        = "dmz-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region      = var.region
  network     = google_compute_network.security_sim_vpc.self_link
  project     = var.project_id
}

resource "google_compute_subnetwork" "internal_subnet" {
  name        = "internal-subnet"
  ip_cidr_range = "10.0.2.0/24"
  region      = var.region
  network     = google_compute_network.security_sim_vpc.self_link
  project     = var.project_id
}

resource "google_compute_subnetwork" "db_subnet" {
  name        = "db-subnet"
  ip_cidr_range = "10.0.3.0/24"
  region      = var.region
  network     = google_compute_network.security_sim_vpc.self_link
  project     = var.project_id
}