# security-sim-project/outputs.tf

output "vpc_self_link" {
  description = "Self link della VPC network."
  value       = module.vpc.vpc_self_link
}

output "subnet_info" {
  description = "Dettagli delle subnet create (nome e CIDR)."
  value = {
    for s_name, s_details in module.vpc.subnet_self_links :
    s_name => {
      self_link   = s_details.self_link
      ip_cidr_range = s_details.ip_cidr_range
    }
  }
}


# --- MODIFICATO: Combina gli IP di entrambe le nuove chiamate del modulo compute_instance ---
output "instance_ips" {
  description = "Indirizzi IP delle istanze GCE simulate."
  value = merge(
    {
      for k, v in module.server_compute_instance : k => { # Istanze server
        internal_ip = v.internal_ip
        public_ip   = v.public_ip
      }
    },
    {
      for k, v in module.client_compute_instance : k => { # Istanza client
        internal_ip = v.internal_ip
        public_ip   = v.public_ip
      }
    }
  )
}

/* OUTPUT ORIGINALE
output "instance_ips" {
  description = "Indirizzi IP delle istanze GCE simulate."
  value = {
    for k, v in module.compute_instance : k => {
      internal_ip = v.internal_ip
      public_ip   = v.public_ip
    }
  }
}
*/

output "cloudsql_connection_name" {
  description = "Connection name dell'istanza Cloud SQL (per connessioni autorizzate)."
  value       = module.cloud_sql.cloudsql_connection_name
}

output "cloudsql_public_ip_address" {
  description = "Indirizzo IP pubblico dell'istanza Cloud SQL (se abilitato)."
  value       = module.cloud_sql.cloudsql_public_ip_address
}

output "gcs_bucket_url" {
  description = "URL del bucket Cloud Storage."
  value       = module.cloud_storage.gcs_bucket_url
}

output "gcp_project_id" {
  description = "L'ID del progetto GCP utilizzato."
  value       = var.gcp_project_id
  
}