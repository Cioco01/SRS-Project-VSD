# modules/firewall-rules/variables.tf

variable "project_id" {
  description = "L'ID del progetto GCP."
  type        = string
}

variable "network_name" {
  description = "Il nome della VPC network a cui applicare le regole."
  type        = string
}

variable "subnet_self_links" {
  description = "Mappa dei self link e CIDR delle subnet, indicizzati per nome."
  type = map(object({
    self_link     = string
    ip_cidr_range = string
  }))
}