#MAIN
locals {
  gcs_script_base_paths = {
    "attacker-node-01"   = "scripts/Attacker-node-scripts/",
    "internal-client-01" = "scripts/Client-node-scripts/",
    "db-server-01"       = "scripts/DB-node-scripts/",
    "dns-server-01"      = "scripts/DNS-node-scripts/",
    "web-server-01"      = "scripts/WS-node-scripts/",
  }

  main_startup_scripts = {
    "attacker-node-01"   = "attacker_orchestrator_startup.sh",
    "internal-client-01" = "start_simulation.sh",
    "db-server-01"       = "db_server_startup.sh",
    "dns-server-01"      = "dns_server_startup.sh",
    "web-server-01"      = "web_server_startup.sh",
  }
  vm_install_dirs = {
    "attacker-node-01"   = "/home/cristian_ciocoiu",
    "internal-client-01" = "/opt/simulation",
    "db-server-01"       = "/opt/db-scripts",
    "dns-server-01"      = "/opt/dns-scripts",
    "web-server-01"      = "/var/www/html/web-app",
  }
}

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# Chiamata al modulo VPC
module "vpc" {
  source     = "./modules/vpc"
  project_id = var.gcp_project_id
  region     = var.gcp_region
  vpc_name   = "security-sim-vpc"
}

# Chiamata al modulo Firewall Rules
module "firewall_rules" {
  source     = "./modules/firewall-rules"
  project_id = var.gcp_project_id
  vpc_self_link = module.vpc.vpc_self_link
}

# Chiamata al modulo Cloud Storage
module "cloud_storage" {
  source     = "./modules/cloud-storage"
  project_id = var.gcp_project_id
  region     = var.gcp_region
  bucket_name = "gruppo-9-456912-gcs-bucket" 
}

# Chiamata al modulo Cloud SQL
module "cloud_sql" {
  source               = "./modules/cloudsql"
  project_id           = var.gcp_project_id
  region               = var.gcp_region
  zone                 = var.gcp_zone
  vpc_self_link        = module.vpc.vpc_self_link
  sql_simuser_password = var.sql_simuser_password
  sql_db_tier          = var.sql_db_tier
  sql_db_disk_size     = var.sql_db_disk_size
  sql_db_disk_type     = var.sql_db_disk_type
}

# Attacker-node-scripts
resource "google_storage_bucket_object" "attacker_orchestrator_startup_sh" {
  name   = "scripts/Attacker-node-scripts/attacker_orchestrator_startup.sh"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Attacker-node-scripts/attacker_orchestrator_startup.sh"
}

resource "google_storage_bucket_object" "attacker_agent_py" {
  name   = "scripts/Attacker-node-scripts/NetChaos/attacker_agent.py"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Attacker-node-scripts/NetChaos/attacker_agent.py"
}

resource "google_storage_bucket_object" "data_viewer_backend_py" {
  name   = "scripts/Attacker-node-scripts/NetChaos/data_viewer_backend.py"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Attacker-node-scripts/NetChaos/data_viewer_backend.py"
}

resource "google_storage_bucket_object" "orchestrator_backend_py" {
  name   = "scripts/Attacker-node-scripts/NetChaos/orchestrator_backend.py"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Attacker-node-scripts/NetChaos/orchestrator_backend.py"
}

# Attacker-node-scripts/NetChaos/DB_setup
resource "google_storage_bucket_object" "create_tables_sql" {
  name   = "scripts/Attacker-node-scripts/NetChaos/DB_setup/create_tables.sql"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Attacker-node-scripts/NetChaos/DB_setup/create_tables.sql"
}

resource "google_storage_bucket_object" "db_init_py" {
  name   = "scripts/Attacker-node-scripts/NetChaos/DB_setup/db_init.py"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Attacker-node-scripts/NetChaos/DB_setup/db_init.py"
}

# Attacker-node-scripts/NetChaos/static
resource "google_storage_bucket_object" "data_viewer_html" {
  name   = "scripts/Attacker-node-scripts/NetChaos/static/data_viewer.html"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Attacker-node-scripts/NetChaos/static/data_viewer.html"
}

resource "google_storage_bucket_object" "index_html_attacker" {
  name   = "scripts/Attacker-node-scripts/NetChaos/static/index.html"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Attacker-node-scripts/NetChaos/static/index.html"
}

resource "google_storage_bucket_object" "script_js" {
  name   = "scripts/Attacker-node-scripts/NetChaos/static/script.js"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Attacker-node-scripts/NetChaos/static/script.js"
}

# Attacker-node-scripts/NetChaos/Traffic_capture
resource "google_storage_bucket_object" "traffic_capture_agent_py" {
  name   = "scripts/Attacker-node-scripts/NetChaos/Traffic_capture/traffic_capture_agent.py"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Attacker-node-scripts/NetChaos/Traffic_capture/traffic_capture_agent.py"
}

# Client-node-scripts
resource "google_storage_bucket_object" "brute_force_simulator_py" {
  name   = "scripts/Client-node-scripts/brute_force_simulator.py"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Client-node-scripts/brute_force_simulator.py"
}

resource "google_storage_bucket_object" "config_yaml" {
  name   = "scripts/Client-node-scripts/config.yaml"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Client-node-scripts/config.yaml"
}

resource "google_storage_bucket_object" "db_simulator_py" {
  name   = "scripts/Client-node-scripts/db_simulator.py"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Client-node-scripts/db_simulator.py"
}

resource "google_storage_bucket_object" "db_traffic_log" {
  name   = "scripts/Client-node-scripts/db_traffic.log"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Client-node-scripts/db_traffic.log"
}

resource "google_storage_bucket_object" "dns_simulator_py" {
  name   = "scripts/Client-node-scripts/dns_simulator.py"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Client-node-scripts/dns_simulator.py"
}

resource "google_storage_bucket_object" "dns_traffic_log" {
  name   = "scripts/Client-node-scripts/dns_traffic.log"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Client-node-scripts/dns_traffic.log"
}

resource "google_storage_bucket_object" "http_simulator_py" {
  name   = "scripts/Client-node-scripts/http_simulator.py"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Client-node-scripts/http_simulator.py"
}

resource "google_storage_bucket_object" "http_traffic_log" {
  name   = "scripts/Client-node-scripts/http_traffic.log"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Client-node-scripts/http_traffic.log"
}

resource "google_storage_bucket_object" "lateral_movement_simulator_py" {
  name   = "scripts/Client-node-scripts/lateral_movement_simulator.py"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Client-node-scripts/lateral_movement_simulator.py"
}

resource "google_storage_bucket_object" "main_py_client" {
  name   = "scripts/Client-node-scripts/main.py"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Client-node-scripts/main.py"
}

resource "google_storage_bucket_object" "main_py_save" {
  name   = "scripts/Client-node-scripts/main.py.save"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Client-node-scripts/main.py.save"
}

resource "google_storage_bucket_object" "malicious_config_yaml" {
  name   = "scripts/Client-node-scripts/malicious_config.yaml"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Client-node-scripts/malicious_config.yaml"
}

resource "google_storage_bucket_object" "malicious_main_py" {
  name   = "scripts/Client-node-scripts/malicious_main.py"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Client-node-scripts/malicious_main.py"
}

resource "google_storage_bucket_object" "malware_drop_simulator_py" {
  name   = "scripts/Client-node-scripts/malware_drop_simulator.py"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Client-node-scripts/malware_drop_simulator.py"
}

resource "google_storage_bucket_object" "port_scan_simulator_py" {
  name   = "scripts/Client-node-scripts/port_scan_simulator.py"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Client-node-scripts/port_scan_simulator.py"
}

resource "google_storage_bucket_object" "setup_client_sh" {
  name   = "scripts/Client-node-scripts/setup_client.sh"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Client-node-scripts/setup_client.sh"
}

resource "google_storage_bucket_object" "start_simulation_sh" {
  name   = "scripts/Client-node-scripts/start_simulation.sh"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/Client-node-scripts/start_simulation.sh"
}

##  Packet Mirroring Configuration
# Data source for the packet mirroring collector
data "google_compute_instance_group" "attacker_node_instance_group" {
  name    = "instance-group-1" 
  zone    = var.gcp_zone
  project = var.gcp_project_id
}

#Health check for the packet mirroring collector
resource "google_compute_health_check" "packet_mirroring_collector_health_check" {
  name        = "packet-mirror-collector-hc"
  project     = var.gcp_project_id
  timeout_sec = 5
  check_interval_sec = 5
  tcp_health_check {
    port = 80
  }
}

# Packet Mirroring collector backend service
resource "google_compute_region_backend_service" "packet_mirroring_collector_backend_service" {
  name                  = "traffic-load-balancer-for-mirroring" # Il nome del tuo backendService dal JSON originale
  region                = var.gcp_region
  project               = var.gcp_project_id
  protocol              = "TCP"
  load_balancing_scheme = "INTERNAL" # Necessario per un Internal Load Balancer che funge da collector

  health_checks = [google_compute_health_check.packet_mirroring_collector_health_check.self_link]

  backend {
    group = data.google_compute_instance_group.attacker_node_instance_group.self_link
    # Non sono necessarie named_port per il Packet Mirroring collector,
    # ma il backend service deve esistere.
  }
}

# Forwarding Rule for the Packet Mirroring collector
resource "google_compute_forwarding_rule" "packet_mirroring_collector_forwarding_rule" {
  name                  = "traffic-load-balancer-for-mirr-forwarding-rule-2" 
  ip_address            = "10.0.1.10" 
  region                = var.gcp_region
  project               = var.gcp_project_id
  port_range            = "1-65535" # Corrisponde a "allPorts": true
  load_balancing_scheme = "INTERNAL"
  backend_service       = google_compute_region_backend_service.packet_mirroring_collector_backend_service.self_link
  network               = module.vpc.vpc_self_link
  subnetwork            = module.vpc.dmz_subnet_self_link 
  ip_protocol           = "TCP"
  service_label         = "mirroring"
}

# Packet Mirroring Policy
resource "google_compute_packet_mirroring" "security_sim_packet_mirroring_policy" {
  name        = "security-sim-packet-mirroring-policy"
  description = "Packet mirroring policy for security simulation traffic to attacker-node-01 (collector)."
  project     = var.gcp_project_id
  region      = var.gcp_region

  network {
    url = module.vpc.vpc_self_link
  }

# Le risorse da cui mirrorare il traffico: i nodi VM specificati.
  mirrored_resources {
    instances {
      url = module.compute_instance.internal_client_01_self_link
    }
    instances {
      url = module.compute_instance.db_server_01_self_link
    }
    instances {
      url = module.compute_instance.dns_server_01_self_link
    }
    instances {
      url = module.compute_instance.web_server_01_self_link
    }
  }

  # La destinazione del traffico mirrorato: l'Internal Load Balancer Collector.
  collector_ilb {
    url = google_compute_forwarding_rule.packet_mirroring_collector_forwarding_rule.self_link
  }
}

# DB-node-scripts
resource "google_storage_bucket_object" "db_server_startup_sh" {
  name   = "scripts/DB-node-scripts/db_server_startup.sh"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/DB-node-scripts/db_server_startup.sh"
}

# DNS-node-scripts
resource "google_storage_bucket_object" "dns_server_startup_sh" {
  name   = "scripts/DNS-node-scripts/dns_server_startup.sh"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/DNS-node-scripts/dns_server_startup.sh"
}

# WS-node-scripts
resource "google_storage_bucket_object" "web_server_startup_sh" {
  name   = "scripts/WS-node-scripts/web_server_startup.sh"
  bucket = module.cloud_storage.bucket_name
  source = "${path.root}/scripts/WS-node-scripts/web_server_startup.sh"
}

module "compute_instance" {
  source                     = "./modules/compute-instance"
  project_id                 = var.gcp_project_id
  zone                       = var.gcp_zone
  dmz_subnet_self_link       = module.vpc.dmz_subnet_self_link
  internal_subnet_self_link  = module.vpc.internal_subnet_self_link
  db_subnet_self_link        = module.vpc.db_subnet_self_link
  client_vm_sa_email         = var.client_vm_sa_email
  gcs_scripts_bucket_name_metadata = module.cloud_storage.bucket_name

 
  gcs_script_base_paths = local.gcs_script_base_paths
  main_startup_scripts  = local.main_startup_scripts
  vm_install_dirs       = local.vm_install_dirs

  depends_on = [
    google_storage_bucket_object.attacker_orchestrator_startup_sh,
    google_storage_bucket_object.attacker_agent_py,
    google_storage_bucket_object.data_viewer_backend_py,
    google_storage_bucket_object.orchestrator_backend_py,
    google_storage_bucket_object.create_tables_sql,
    google_storage_bucket_object.db_init_py,
    google_storage_bucket_object.data_viewer_html,
    google_storage_bucket_object.index_html_attacker,
    google_storage_bucket_object.script_js,
    google_storage_bucket_object.traffic_capture_agent_py,
    google_storage_bucket_object.brute_force_simulator_py,
    google_storage_bucket_object.config_yaml,
    google_storage_bucket_object.db_simulator_py,
    google_storage_bucket_object.db_traffic_log,
    google_storage_bucket_object.dns_simulator_py,
    google_storage_bucket_object.dns_traffic_log,
    google_storage_bucket_object.http_simulator_py,
    google_storage_bucket_object.http_traffic_log,
    google_storage_bucket_object.lateral_movement_simulator_py,
    google_storage_bucket_object.main_py_client,
    google_storage_bucket_object.main_py_save,
    google_storage_bucket_object.malicious_config_yaml,
    google_storage_bucket_object.malicious_main_py,
    google_storage_bucket_object.malware_drop_simulator_py,
    google_storage_bucket_object.port_scan_simulator_py,
    google_storage_bucket_object.setup_client_sh,
    google_storage_bucket_object.start_simulation_sh,
    google_storage_bucket_object.db_server_startup_sh,
    google_storage_bucket_object.dns_server_startup_sh,
    google_storage_bucket_object.web_server_startup_sh,
  ]
}

