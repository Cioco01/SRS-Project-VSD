# Attacker Node 01
resource "google_compute_instance" "attacker_node_01" {
  name         = "attacker-node-01"
  zone         = var.zone
  machine_type = "e2-small"
  tags         = ["attacker-node", "all-sim-vms", "dmz-instance", "allow-ssh", "allow-ssh-iap-explicit"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 10
    }
  }

  network_interface {
    subnetwork = var.dmz_subnet_self_link
    network_ip = "10.0.1.3"
    access_config {
      nat_ip = "35.195.245.74" # IP esterno statico
    }
  }

 metadata = {
    GCS_SCRIPTS_BUCKET_NAME = var.gcs_scripts_bucket_name_metadata
    GCS_SCRIPT_BASE_PATH    = lookup(var.gcs_script_base_paths, "attacker-node-01", "scripts/default/")
    MAIN_STARTUP_SCRIPT     = lookup(var.main_startup_scripts, "attacker-node-01", "")
    INSTALL_DIR             = lookup(var.vm_install_dirs, "attacker-node-01", "/opt/scripts/default")
  }
  metadata_startup_script = <<-EOT
    # ... (il tuo script di startup per attacker_node_01) ...
  EOT
  service_account {
    email  = var.client_vm_sa_email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}

# DB Server 01
resource "google_compute_instance" "db_server_01" {
  name         = "db-server-01"
  zone         = var.zone
  machine_type = "e2-medium"
  tags         = ["allow-ssh", "allow-ssh-iap-explicit", "db-server", "db-server-01", "internal-instance", "all-sim-vms"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 10
    }
  }

  network_interface {
    subnetwork = var.db_subnet_self_link
    network_ip = "10.0.3.2"
  }

  metadata = {
    GCS_SCRIPTS_BUCKET_NAME = var.gcs_scripts_bucket_name_metadata
    GCS_SCRIPT_BASE_PATH    = lookup(var.gcs_script_base_paths, "db-server-01", "scripts/default/")
    MAIN_STARTUP_SCRIPT     = lookup(var.main_startup_scripts, "db-server-01", "")
    INSTALL_DIR             = lookup(var.vm_install_dirs, "db-server-01", "/opt/scripts/default")
  }
  metadata_startup_script = <<-EOT
    # ... (il tuo script di startup per db_server_01) ...
  EOT
}

# DNS Server 01
resource "google_compute_instance" "dns_server_01" {
  name         = "dns-server-01"
  zone         = var.zone
  machine_type = "e2-small"
  tags         = ["allow-ssh-iap-explicit", "allow-ssh", "dns-server", "all-sim-vms", "dmz-instance"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 10
    }
  }

  network_interface {
    subnetwork = var.dmz_subnet_self_link
    network_ip = "10.0.1.2"
    access_config {
      nat_ip = "34.76.56.110" # IP esterno statico
    }
  }

  metadata = {
    GCS_SCRIPTS_BUCKET_NAME = var.gcs_scripts_bucket_name_metadata
    GCS_SCRIPT_BASE_PATH    = lookup(var.gcs_script_base_paths, "dns-server-01", "scripts/default/")
    MAIN_STARTUP_SCRIPT     = lookup(var.main_startup_scripts, "dns-server-01", "")
    INSTALL_DIR             = lookup(var.vm_install_dirs, "dns-server-01", "/opt/scripts/default")
  }
  metadata_startup_script = <<-EOT
    # ... (il tuo script di startup per dns_server_01) ...
  EOT
}

# Internal Client 01 (REINSERITO QUI!)
resource "google_compute_instance" "internal_client_01" {
  name         = "internal-client-01"
  zone         = var.zone
  machine_type = "e2-small"
  tags         = ["internal-client", "all-sim-vms", "allow-ssh", "allow-ssh-iap-explicit"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 10
    }
  }

  network_interface {
    subnetwork = var.internal_subnet_self_link
    network_ip = "10.0.2.2"
  }

  metadata = {
    # Questi riferimenti funzionano ora perché le risorse sono nello STESSO modulo
    DB_SERVER_IP_METADATA   = google_compute_instance.db_server_01.network_interface[0].network_ip
    DNS_SERVER_IP_METADATA  = google_compute_instance.dns_server_01.network_interface[0].network_ip
    WEB_SERVER_IP_METADATA  = google_compute_instance.web_server_01.network_interface[0].network_ip
    GCS_SCRIPTS_BUCKET_NAME = var.gcs_scripts_bucket_name_metadata
    GCS_SCRIPT_BASE_PATH    = lookup(var.gcs_script_base_paths, "internal-client-01", "scripts/default/")
    MAIN_STARTUP_SCRIPT     = lookup(var.main_startup_scripts, "internal-client-01", "")
    INSTALL_DIR             = lookup(var.vm_install_dirs, "internal-client-01", "/opt/scripts/default")
  }

  metadata_startup_script = <<-EOT
    # ... (il tuo script di startup per internal_client_01) ...
  EOT
  service_account {
    email  = var.client_vm_sa_email
    scopes = ["https://www.googleapis.com/auth/compute", "https://www.googleapis.com/auth/devstorage.read_only"]
  }
}

# Web Server 01
resource "google_compute_instance" "web_server_01" {
  name         = "web-server-01"
  zone         = var.zone
  machine_type = "e2-medium"
  tags         = ["dmz-instance", "web-server", "all-sim-vms", "allow-ssh", "allow-ssh-iap-explicit", "http-server"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 10
    }
  }

  network_interface {
    subnetwork = var.dmz_subnet_self_link
    network_ip = "10.0.1.4"
    access_config {
      nat_ip = "34.79.246.235" # IP esterno statico
    }
  }

  metadata = {
    GCS_SCRIPTS_BUCKET_NAME = var.gcs_scripts_bucket_name_metadata
    GCS_SCRIPT_BASE_PATH    = lookup(var.gcs_script_base_paths, "web-server-01", "scripts/default/")
    MAIN_STARTUP_SCRIPT     = lookup(var.main_startup_scripts, "web-server-01", "")
    INSTALL_DIR             = lookup(var.vm_install_dirs, "web-server-01", "/opt/scripts/default")
  }
  metadata_startup_script = <<-EOT
    # ... (il tuo script di startup per web_server_01) ...
  EOT
}