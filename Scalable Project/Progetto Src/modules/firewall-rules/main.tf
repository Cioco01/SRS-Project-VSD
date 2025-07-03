# modules/firewall-rules/main.tf

# Regola per consentire SSH (porta 22) dall'esterno a qualsiasi istanza con tag 'dmz-instance'
resource "google_compute_firewall" "allow_ssh_from_internet" {
  name    = "${var.network_name}-allow-ssh-internet"
  network = var.network_name
  project = var.project_id

  # Limita questa sorgente solo ai tuoi IP noti se possibile!
  source_ranges = ["10.0.0.0/24", "10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  target_tags   = ["dmz-instance", "attacker-node"] # Permetti SSH verso DMZ e attacker

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

# Regola per consentire HTTP (porta 80) e HTTPS (porta 443) dall'esterno al web server
resource "google_compute_firewall" "allow_http_https_from_internet" {
  name    = "${var.network_name}-allow-http-https-internet"
  network = var.network_name
  project = var.project_id

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["web-server"]

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }
}

# Regola per consentire traffico interno da tutte le subnet
resource "google_compute_firewall" "allow_internal_traffic" {
  name    = "${var.network_name}-allow-internal-traffic"
  network = var.network_name
  project = var.project_id

  source_ranges = [
    # Ottieni i CIDR dalle subnet create
    for s_name, s_link in var.subnet_self_links : s_link.ip_cidr_range
  ]
  destination_ranges = [
    for s_name, s_link in var.subnet_self_links : s_link.ip_cidr_range
  ]

  allow {
    protocol = "icmp"
  }
  allow {
    protocol = "tcp"
    ports    = ["0-65535"] # Permette tutto il TCP
  }
  allow {
    protocol = "udp"
    ports    = ["0-65535"] # Permette tutto l'UDP
  }
}

# Regola specifica: Client interni possono accedere al DB sulla subnet DB
resource "google_compute_firewall" "allow_internal_clients_to_db" {
  name    = "${var.network_name}-allow-internal-clients-to-db"
  network = var.network_name
  project = var.project_id

  source_tags = ["internal-client"] # Solo istanze con tag "internal-client"
  target_tags = ["db-server"] # Possono accedere a istanze con tag "db-server"

  allow {
    protocol = "tcp"
    ports    = ["3306", "5432"] # MySQL/MariaDB (3306), PostgreSQL (5432)
  }
}

# Puoi aggiungere regole più granulari qui, es:
# - Solo il server DNS risponde alle query DNS
# - Solo API Gateway accede ai microservizi
# - Nodi specifici possono fare SSH ad altri nodi specifici