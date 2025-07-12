
resource "google_compute_instance" "attacker_node_01" {
  name         = "attacker-node-01"
  zone         = var.zone
  machine_type = "e2-small"
  tags         = ["attacker-node", "all-sim-vms", "dmz-instance", "allow-ssh", "allow-ssh-iap-explicit"] # Aggiunti tags per coerenza con le regole firewall

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

  metadata_startup_script = "#!/bin/bash\nsudo apt-get update && sudo apt-get install -y nmap hydra python3 python3-pip && pip3 install python-nmap paramiko"

  service_account {
    email  = var.client_vm_sa_email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}

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

  metadata_startup_script = "#!/bin/bash\nsudo apt-get update && sudo apt-get install -y mariadb-server && sudo systemctl start mariadb && sudo systemctl enable mariadb"
}

resource "google_compute_instance" "dns_server_01" {
  name         = "dns-server-01"
  zone         = var.zone
  machine_type = "e2-small"
  tags         = ["allow-ssh-iap-explicit", "allow-ssh", "dns-server", "all-sim-vms", "dmz-instance"] # Aggiunto all-sim-vms, dmz-instance

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

  metadata_startup_script = "#!/bin/bash\nsudo apt-get update && sudo apt-get install -y bind9 bind9utils bind9-doc && sudo systemctl start bind9 && sudo systemctl enable bind9"
}

resource "google_compute_instance" "internal_client_01" {
  name         = "internal-client-01"
  zone         = var.zone
  machine_type = "e2-small"
  tags         = ["internal-client", "all-sim-vms", "allow-ssh", "allow-ssh-iap-explicit"] # Aggiunti tags

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
    DB_SERVER_IP_METADATA            = var.db_server_ip_metadata
    DNS_SERVER_IP_METADATA           = var.dns_server_ip_metadata
    GCS_SCRIPTS_BUCKET_NAME_METADATA = var.gcs_scripts_bucket_name_metadata
    WEB_SERVER_IP_METADATA           = var.web_server_ip_metadata
  }
  metadata_startup_script = "#!/bin/bash\nsudo apt-get update && sudo apt-get install -y python3 python3-pip && pip3 install requests dnspython psycopg2-binary"

  service_account {
    email  = var.client_vm_sa_email
    scopes = ["https://www.googleapis.com/auth/compute", "https://www.googleapis.com/auth/devstorage.read_only"]
  }
}

resource "google_compute_instance" "web_server_01" {
  name         = "web-server-01"
  zone         = var.zone
  machine_type = "e2-medium"
  tags         = ["dmz-instance", "web-server", "all-sim-vms", "allow-ssh", "allow-ssh-iap-explicit", "http-server"] # Aggiunti tags per Flask e all-sim-vms

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

  metadata_startup_script = "#!/bin/bash\nsudo apt-get update && sudo apt-get install -y nginx && echo '<h1>Simulated Web Server</h1>' | sudo tee /var/www/html/index.html && sudo systemctl start nginx"
}