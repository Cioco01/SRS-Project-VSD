#MAIN
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
  bucket_name = "gruppo-9-456912-gcs-bucket" # Sostituisci con un nome bucket unico globalmente
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

# Chiamata al modulo Compute Instance
module "compute_instance" {
  source                       = "./modules/compute-instance"
  project_id                   = var.gcp_project_id
  zone                         = var.gcp_zone
  dmz_subnet_self_link         = module.vpc.dmz_subnet_self_link
  internal_subnet_self_link    = module.vpc.internal_subnet_self_link
  db_subnet_self_link          = module.vpc.db_subnet_self_link
  client_vm_sa_email           = var.client_vm_sa_email
  db_server_ip_metadata        = var.db_server_ip_metadata
  dns_server_ip_metadata       = var.dns_server_ip_metadata
  gcs_scripts_bucket_name_metadata = module.cloud_storage.bucket_name # Usa l'output del modulo GCS
  web_server_ip_metadata       = var.web_server_ip_metadata
}