terraform {
  required_version = ">= 1.0.0" # Assicurati di avere una versione di Terraform compatibile
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0.0" # Usa una versione recente del provider Google
    }
  }
}

# Configurazione del provider Google Cloud
provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  zone    = var.gcp_zone
}