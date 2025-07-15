
variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "zone" {
  description = "The GCP zone for the instances."
  type        = string
}

variable "dmz_subnet_self_link" {
  description = "Self-link of the DMZ subnetwork."
  type        = string
}

variable "internal_subnet_self_link" {
  description = "Self-link of the Internal subnetwork."
  type        = string
}

variable "db_subnet_self_link" {
  description = "Self-link of the DB subnetwork."
  type        = string
}

variable "client_vm_sa_email" {
  description = "Email of the service account for client VMs."
  type        = string
}

variable "gcs_scripts_bucket_name_metadata" {
  description = "Name of the GCS bucket for scripts (for VM metadata)."
  type        = string
}

variable "gcs_script_base_paths" {
  description = "Map of GCS script base paths for each VM type."
  type        = map(string)
}

variable "main_startup_scripts" {
  description = "Map of main startup script filenames for each VM type."
  type        = map(string)
}

variable "vm_install_dirs" {
  description = "Map of installation directories on each VM type."
  type        = map(string)
}