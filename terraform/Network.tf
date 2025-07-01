resource "google_compute_network" "vpc_network" {
  name                    = "demo-vpc"
  auto_create_subnetworks = false
}
resource "google_compute_subnetwork" "vpc_subnet" {
  name          = "demo-subnet"
  ip_cidr_range = "10.0.0.0/16"
  region        = var.region
  network= google_compute_network.vpc_network.id
}
resource "google_compute_firewall" "allow-internal" {
  name    = "allow-firewall"
  network = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  source_ranges = ["10.0.0.0/16"]
}
resource "google_compute_firewall" "allow-ssh-http" {
  name    = "allow-ssh-http"
  # Use the network created above
  network = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["22","80"]
  }

  source_ranges = ["0.0.0.0/0"]
}