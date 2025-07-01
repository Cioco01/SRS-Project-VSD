#MAIN DA RIVEDERE 

provider "google" {
  project     = var.project_id
  region      = var.region
  zone        = var.zone
}

output "instance_name" {
  value = google_compute_instance.nginvx_vm.name
  
}

/*
provider "google" {
  project = var.project_id
  region  = var.region
  zone=var.zone
}

resource "google_compute_network" "sim_net" {
  name                    = "sim-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "sim_subnet" {
  name          = "sim-subnet"
  ip_cidr_range = "10.0.0.0/16"
  region        = var.region
  network       = google_compute_network.sim_net.id
}

resource "google_compute_firewall" "allow-internal" {
  name    = "allow-internal"
  network = google_compute_network.sim_net.name

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  source_ranges = ["10.0.0.0/16"]
}

resource "google_compute_firewall" "allow-ssh-http" {
  name    = "allow-ssh-http"
  network = google_compute_network.sim_net.name

  allow {
    protocol = "tcp"
    ports    = ["22", "80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
}
*/
