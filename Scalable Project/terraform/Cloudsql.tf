

resource "google_sql_database_instance" "pg_instance" {
  name             = "pg-demo"
  database_version = "POSTGRES_14"
  region           = var.region # Ensure this is a valid region

  settings {
    tier = "db-f1-micro"
    ip_configuration {
      ipv4_enabled    = true
      
      authorized_networks {
        name  = "allow-vpc"
        value = "95.239.174.8/32" # Change this to restrict access to your VPC or specific IPs
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