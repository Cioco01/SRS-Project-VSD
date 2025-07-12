
resource "google_sql_database_instance" "simulation_db_instance" {
  database_version = "MYSQL_8_0"
  name             = "simulation-db-instance"
  project          = var.project_id
  region           = var.region
  settings {
    tier            = var.sql_db_tier
    disk_size       = var.sql_db_disk_size
    disk_type       = var.sql_db_disk_type
    availability_type = "ZONAL" # Single zone come specificato
    backup_configuration {
      enabled            = false
      binary_log_enabled = false
    }
    ip_configuration {
      ipv4_enabled        = true
      private_network     = var.vpc_self_link
      

      authorized_networks {
        value = "0.0.0.0/0"
        name  = "Allow all public IPs (for simulation)"
      }
    }
    location_preference {
      zone = var.zone
    }
    maintenance_window {
      day          = 7
      hour         = 0
      update_track = "stable"
    }
  }
}

resource "google_sql_database" "simulation_data_db" {
  name       = "simulation_data"
  instance   = google_sql_database_instance.simulation_db_instance.name
  charset    = "utf8mb4"
  collation  = "utf8mb4_0900_ai_ci"
  project    = var.project_id
}

resource "google_sql_user" "sim_user" {
  name     = "simuser"
  instance = google_sql_database_instance.simulation_db_instance.name
  host     = "%"
  password = var.sql_simuser_password
  project  = var.project_id
}