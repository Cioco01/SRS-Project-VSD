# security-sim-project/main.tf

# Chiama il modulo VPC per creare la rete e le subnet
module "vpc" {
  source        = "./modules/vpc"
  project_id    = var.gcp_project_id
  region        = var.gcp_region
  network_name  = var.network_name
  subnet_configs = var.subnet_configs
}

# Chiama il modulo firewall-rules
module "firewall_rules" {
  source      = "./modules/firewall-rules"
  project_id  = var.gcp_project_id
  network_name = module.vpc.vpc_name
  # Passa gli ID delle subnet se le regole devono essere specifiche per subnet
  subnet_self_links = module.vpc.subnet_self_links # Passa direttamente l'output completo

}

# --- NUOVO: Variabili Locali per Separare le Configurazioni delle Istanze ---
locals {
  # Istanza del client che ha bisogno degli IP degli altri server
  client_instance_config = var.instance_configs["internal-client-1"]

  # Tutte le altre istanze che fungono da server (web, db, attacker, e un eventuale dns-server)
  server_instances_configs = {
    for k, v in var.instance_configs : k => v
    if k != "internal-client-1" # Esclude il client dalla lista dei server
  }
}



# --- NUOVO: Chiama il modulo per le istanze "Server" (web, db, attacker) ---
module "server_compute_instance" {
  source     = "./modules/compute-instance"
  for_each   = local.server_instances_configs # Crea le istanze server
  project_id = var.gcp_project_id
  zone       = each.value.zone
  subnet_id  = module.vpc.subnet_self_links[each.value.subnet_name].self_link

  name             = each.value.name
  machine_type     = each.value.machine_type
  image            = each.value.image
  tags             = each.value.tags
  startup_script   = each.value.startup_script
  create_public_ip = each.value.create_public_ip

  # Per le istanze server, i metadati e il service account possono essere presi direttamente da `each.value`
  # (se non sono definiti in `var.instance_configs` per queste istanze, useranno il default del modulo)
  metadata              = lookup(each.value, "metadata", {})
  service_account_email = lookup(each.value, "service_account_email", null)
  service_account_scopes = lookup(each.value, "service_account_scopes", [])
}

# --- NUOVO: Chiama il modulo per l'istanza "Client" (internal-client-1) ---
module "client_compute_instance" {
  source = "./modules/compute-instance"
  # Utilizza for_each con una mappa a singolo elemento per trattare il client come un caso a sé
  # Questo mantiene la coerenza nell'accesso agli output del modulo, ad esempio: module.client_compute_instance["internal-client-1"].internal_ip
  for_each = { "internal-client-1" : local.client_instance_config }

  project_id = var.gcp_project_id
  zone       = each.value.zone
  subnet_id  = module.vpc.subnet_self_links[each.value.subnet_name].self_link

  name             = each.value.name
  machine_type     = each.value.machine_type
  image            = each.value.image
  tags             = each.value.tags
  startup_script   = each.value.startup_script # Lo startup script completo del client

  # Il client non ha IP pubblico (come definito in variables.tf)
  create_public_ip = each.value.create_public_ip

  # --- Ora i metadati possono fare riferimento agli IP dei server già definiti ---
  metadata = {
    GCS_SCRIPTS_BUCKET_NAME_METADATA = module.cloud_storage.gcs_bucket_name
    # Usa le chiavi esatte definite in `var.instance_configs` per i server
    WEB_SERVER_IP_METADATA   = module.server_compute_instance["web-server"].internal_ip
    # Se hai un'istanza DNS separata:
    DNS_SERVER_IP_METADATA   = module.server_compute_instance["dns-server"].internal_ip # Assumi che "dns-server" sia una chiave valida in `var.instance_configs`
    # Se non hai un DNS server dedicato, potresti usare un IP statico o quello di Google (8.8.8.8)
    # DNS_SERVER_IP_METADATA   = "8.8.8.8" # Esempio per DNS pubblico
    DB_SERVER_IP_METADATA    = module.cloud_sql.cloudsql_private_ip_address
  }

  # Service account specifico per il client
  service_account_email = google_service_account.client_vm_sa.email
  service_account_scopes = ["https://www.googleapis.com/auth/devstorage.read_only", "https://www.googleapis.com/auth/logging.write", "https://www.googleapis.com/auth/monitoring.write", "https://www.googleapis.com/auth/servicecontrol", "https://www.googleapis.com/auth/service.management.readonly", "https://www.googleapis.com/auth/trace.append"]

  # Aggiungi una dipendenza esplicita per garantire che i server siano creati prima del client
  depends_on = [module.server_compute_instance]
}

/* MOMENTANEAMENTE SOSPESO E SOSTIUTO CON locals e module "server_compute_instance"
# Chiama il modulo compute-instance per deployare le VM
module "compute_instance" {
  source     = "./modules/compute-instance"
  for_each   = var.instance_configs # Crea più istanze basate sulla mappa
  project_id = var.gcp_project_id
  zone       = each.value.zone # Utilizza la zona definita nella configurazione dell'istanza
  subnet_id  = module.vpc.subnet_self_links[each.value.subnet_name].self_link # Associa alla subnet corretta

  name             = each.value.name
  machine_type     = each.value.machine_type
  image            = each.value.image
  tags             = each.value.tags
  startup_script   = each.value.startup_script
  create_public_ip = each.value.create_public_ip

  # --- NUOVO: Aggiungi i metadati e il Service Account in base all'istanza ---
  metadata = (each.key == "internal-client-1") ? { # Applica questi metadati solo a "internal-client-1"
    GCS_SCRIPTS_BUCKET_NAME_METADATA = module.cloud_storage.gcs_bucket_name
    WEB_SERVER_IP_METADATA   = module.compute_instance["web-server"].internal_ip
    DNS_SERVER_IP_METADATA   = module.compute_instance["dns-server"].internal_ip # Se hai un DNS server separato
    DB_SERVER_IP_METADATA    = module.cloud_sql.cloudsql_private_ip_address # Ottieni l'IP privato del DB
  } : {} # Per tutte le altre istanze, i metadati sono vuoti (o puoi specificare altri)

  service_account_email = (each.key == "internal-client-1") ? google_service_account.client_vm_sa.email : null
  # service_account_scopes può essere gestito dal default del modulo o specificato qui se necessario
  service_account_scopes = (each.key == "internal-client-1") ? ["https://www.googleapis.com/auth/devstorage.read_only", "https://www.googleapis.com/auth/logging.write", "https://www.googleapis.com/auth/monitoring.write", "https://www.googleapis.com/auth/servicecontrol", "https://www.googleapis.com/auth/service.management.readonly", "https://www.googleapis.com/auth/trace.append"] : [] # Ometti gli scopes se usi i default del modulo
}
*/


# --- NUOVO: Service Account per la VM Client ---
# Questo account verrà assegnato alla VM client per darle i permessi necessari
resource "google_service_account" "client_vm_sa" {
  account_id   = "client-vm-sa" # ID univoco per l'account di servizio
  display_name = "Service Account for Internal Client VM"
  project      = var.gcp_project_id
}

# --- NUOVO: Permesso per leggere dal bucket GCS degli script ---
# Concede al Service Account il permesso di leggere gli oggetti nel bucket GCS
resource "google_project_iam_member" "client_gcs_reader" {
  project = var.gcp_project_id
  role    = "roles/storage.objectViewer" # Ruolo per la sola lettura di oggetti
  member  = "serviceAccount:${google_service_account.client_vm_sa.email}"
  # Dipende dal bucket GCS per assicurarsi che esista quando il permesso viene assegnato
  depends_on = [module.cloud_storage]
}

resource "google_project_service" "service_networking" {
  project                    = var.gcp_project_id
  service                    = "servicenetworking.googleapis.com"
  disable_on_destroy         = false
  disable_dependent_services = false
}

resource "google_compute_global_address" "private_ip_alloc" {
  project       = var.gcp_project_id
  name          = "google-managed-services-private-ip-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 20
  network       = module.vpc.vpc_self_link
  depends_on    = [google_project_service.service_networking]
}

# Crea la connessione di rete ai servizi privati
resource "google_service_networking_connection" "vpc_private_connection" {
  network                 = module.vpc.vpc_self_link
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
  depends_on = [
    google_project_service.service_networking,
    google_compute_global_address.private_ip_alloc
  ]
}

# Chiama il modulo cloud-sql per l'istanza del database
module "cloud_sql" {
  source                  = "./modules/cloud-sql"
  project_id              = var.gcp_project_id
  region                  = var.gcp_region
  database_version        = var.cloudsql_database_version
  instance_tier           = var.cloudsql_instance_tier
  database_name           = var.cloudsql_database_name
  user_name               = var.cloudsql_user_name
  user_password           = var.cloudsql_user_password
  private_ip_network      = module.vpc.vpc_self_link
  authorized_networks     = ["10.0.0.0/24", "10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24 "] # CAMBIA QUESTO! Limita solo agli IP necessari, es. subnet interne, IP della GUI
  private_services_ip_range_name = google_compute_global_address.private_ip_alloc.name
  db_subnet_name          = google_compute_global_address.private_ip_alloc.name
}


# Chiama il modulo cloud-storage per il bucket
module "cloud_storage" {
  source        = "./modules/cloud-storage"
  project_id    = var.gcp_project_id
  bucket_name   = var.gcs_bucket_name
  region        = var.gcp_region
}