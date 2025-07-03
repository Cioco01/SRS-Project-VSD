# modules/cloud-sql/main.tf

resource "google_sql_database_instance" "main_instance" {
  database_version = var.database_version
  name             = "simulation-db-instance"
  project          = var.project_id
  region           = var.region
  settings {
    tier = var.instance_tier
    ip_configuration {
      ipv4_enabled    = true
      # Connessione IP privata
      private_network = var.private_ip_network
    }
  }
}

resource "google_sql_database" "main_database" {
  name     = var.database_name
  instance = google_sql_database_instance.main_instance.name
  project  = var.project_id
  charset  = "utf8"
  collation = "utf8_general_ci"
}

resource "google_sql_user" "main_user" {
  name     = var.user_name
  host     = "%" # Consente connessioni da qualsiasi host, limitato dalle reti autorizzate
  instance = google_sql_database_instance.main_instance.name
  project  = var.project_id
  password = var.user_password
}