resource "google_storage_bucket" "function_bucket" {
  name          = "${var.project_id}-function-bucket"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true
}

#Dobbiamo inserire il file zip della funzione che vogliamo eseguire
resource "google_storage_bucket_object" "function_zip" {
  name   = "TrafficoBegnigno.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = "C:/Users/loren/Desktop/Uni/Scalable Project/TrafficoBegnigno/TrafficoBegnigno.zip" # Update this path to your function zip file
  
}

resource "google_cloudfunctions_function" "init_db" {
  name        = "init-db"
  description = "Function to initialize the database"
  runtime     = "python310" # Update to your preferred runtime
  entry_point = "init_db" # Update to your function's entry point
  region = var.region

  source_archive_bucket = google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.function_zip.name

  trigger_http = true
  available_memory_mb = 256

  environment_variables = {
    DB_HOST     = google_sql_database_instance.pg_instance.ip_address[0].ip_address
    DB_USER     = google_sql_user.pg_user.name
    DB_PASSWORD = google_sql_user.pg_user.password
    DB_NAME     = google_sql_database.pg_db.name
  }
  
}

resource "null_resource" "trigger_function" {
  depends_on = [google_cloudfunctions_function.init_db]

  provisioner "local-exec" {
    command = "curl -X POST https://${google_cloudfunctions_function.init_db.https_trigger_url} -H 'Content-Type: application/json' -d '{}'"
  }
  
  

  
}