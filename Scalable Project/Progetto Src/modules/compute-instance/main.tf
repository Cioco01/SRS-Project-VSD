# modules/compute-instance/main.tf

resource "google_compute_instance" "vm" {
  name         = var.name
  machine_type = var.machine_type
  zone         = var.zone
  project      = var.project_id
  tags         = var.tags

  boot_disk {
    initialize_params {
      image = var.image
    }
  }

  network_interface {
    subnetwork = var.subnet_id
    dynamic "access_config" {
      for_each = var.create_public_ip ? [1] : []
      content {}
    }
  }

  metadata_startup_script = var.startup_script

  # --- NUOVO: Includi i metadati passati al modulo ---
  metadata = var.metadata

 # --- MODIFICATO: Rendi il blocco service_account condizionale ---
  dynamic "service_account" {
    for_each = var.service_account_email != null ? [1] : [] # Crea il blocco solo se l'email è fornita
    content {
      email  = var.service_account_email
      scopes = var.service_account_scopes # Questo sarà un elenco vuoto se non fornito, ma il blocco non sarà creato se email è null
    }
  }



  # Per consentire SSH da Terraform (con una chiave SSH configurata localmente)
  # Se non hai una chiave SSH pre-esistente configurata con GCP, dovrai aggiungerla manualmente
  # o generarla e aggiungerla qui.
  # metadata = {
  #   ssh-keys = "${var.ssh_username}:${file(var.ssh_public_key_path)}"
  # }
}