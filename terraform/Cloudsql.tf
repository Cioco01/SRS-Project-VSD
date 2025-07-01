resource "google_compute_network" "sim_net" {
  name = "sim-network"
}

resource "google_sql_database_instance" "pg_instance" {
  name             = "pg-demo"
  database_version = "POSTGRES_14"
  region           = var.region

  settings {
    tier = "db-f1-micro"
    ip_configuration {
      ipv4_enabled    = true
      private_network = google_compute_network.sim_net.id
      authorized_networks {
        name  = "allow-vpc"
        value = ""
      }
    }
  }
}

resource "google_sql_user" "pg_user" {
  name     = "admin"
  instance = google_sql_database_instance.pg_instance.name
  password_wo = "securepassword123" # Change this to a secure password
  
}

resource "google_sql_database" "pg_db" {
  name     = "mydatabase" #Change name
  instance = google_sql_database_instance.pg_instance.name
  
}