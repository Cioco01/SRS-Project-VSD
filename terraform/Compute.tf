resource "google_compute_instance" "nginvx_vm" {
  name         = "nginx-vm"
  machine_type = "e2-micro"
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
    }
  }

  network_interface {
    network    = google_compute_network.vpc_network.name
    # Use the subnetwork created in the previous step
    subnetwork = google_compute_subnetwork.vpc_subnet.name
    access_config {}
  }

  metadata_startup_script = <<-EOF
    #! /bin/bash
    apt-get update
    apt-get install -y nginx
    systemctl start nginx
    systemctl enable nginx
  EOF

  metadata ={
    ssh-keys = "terraform:${file("C:/Users/loren/Desktop/Uni/Scalable Project/terraform/id_rsa.pub")}" # Update with your public SSH key path"
  } 
  tags = ["http-server", "https-server","ssh"]
  #https o http è da rivedere
  
}