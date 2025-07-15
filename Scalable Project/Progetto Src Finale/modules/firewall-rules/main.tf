

resource "google_compute_firewall" "security_sim_vpc_allow_ssh_iap_dmz" {
  name    = "security-sim-vpc-allow-ssh-iap-dmz"
  network = var.vpc_self_link # Usa il self_link della VPC
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["dmz-instance"]
  description   = "Allows SSH from IAP IP range to instances with 'dmz-instance' tag."
}

resource "google_compute_firewall" "security_sim_vpc_allow_http_https_internet" {
  name    = "security-sim-vpc-allow-http-https-internet"
  network = var.vpc_self_link
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["web-server"]
  description   = "Allows HTTP/HTTPS from the Internet to instances with 'web-server' tag."
}

resource "google_compute_firewall" "security_sim_vpc_allow_internal_clients_to_db" {
  name    = "security-sim-vpc-allow-internal-clients-to-db"
  network = var.vpc_self_link
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["3306"]
  }

  source_tags = ["internal-client"]
  target_tags = ["db-server"]
  description = "Allows TCP 3306 (MySQL) from 'internal-client' to 'db-server'."
}

resource "google_compute_firewall" "security_sim_vpc_allow_icmp_all_vms" {
  name    = "security-sim-vpc-allow-icmp-all-vms"
  network = var.vpc_self_link
  project = var.project_id

  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.0.0.0/8"]
  target_tags   = ["all-sim-vms"]
  description   = "Allows ICMP within the simulation VPC for VMs tagged 'all-sim-vms'."
}

resource "google_compute_firewall" "security_sim_vpc_allow_flask_web_apps" {
  name    = "security-sim-vpc-allow-flask-web-apps"
  network = var.vpc_self_link
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["5000", "5001"]
  }

  source_tags = ["attacker-node"]
  target_tags = ["http-server"]
  description = "Allows Flask app traffic from attacker nodes to http-server tagged instances."
}

resource "google_compute_firewall" "security_sim_vpc_allow_dns_internal" {
  name    = "security-sim-vpc-allow-dns-internal"
  network = var.vpc_self_link
  project = var.project_id

  allow {
    protocol = "udp"
    ports    = ["53"]
  }

  source_tags = ["internal-client"]
  target_tags = ["dns-server"]
  description = "Allows UDP 53 (DNS) from internal clients to DNS server."
}

resource "google_compute_firewall" "security_sim_vpc_allow_internal_ssh" {
  name    = "security-sim-vpc-allow-internal-ssh"
  network = var.vpc_self_link
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_tags = ["internal-client", "attacker-node"]
  target_tags = ["dmz-instance", "internal-client", "db-server", "dns-server", "web-server"]
  description = "Allows internal SSH between specific simulation VMs."
}

resource "google_compute_firewall" "security_sim_vpc_allow_ssh_internet" {
  name    = "security-sim-vpc-allow-ssh-internet"
  network = var.vpc_self_link
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["dmz-instance"]
  description   = "Allows SSH from the Internet to instances with 'dmz-instance' tag. Use with caution."
}

resource "google_compute_firewall" "default_allow_ssh_iap" {
  name        = "default-allow-ssh-iap"
  direction   = "INGRESS"
  network     = var.vpc_self_link
  project     = var.project_id
  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["allow-ssh-iap-explicit"]

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  description = "Allows IAP-secured SSH access to instances with 'allow-ssh-iap-explicit' tag."
}

resource "google_compute_firewall" "default_allow_ssh" {
  name        = "default-allow-ssh"
  direction   = "INGRESS"
  network     = var.vpc_self_link
  project     = var.project_id
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["allow-ssh"]

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  description = "Allows SSH access to instances with 'allow-ssh' tag. Use with extreme caution."
}