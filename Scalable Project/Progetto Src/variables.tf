# security-sim-project/variables.tf

variable "gcp_project_id" {
  description = "L'ID del tuo progetto Google Cloud."
  type        = string
  default     = "gruppo-9-456912" # Cambia con il tuo ID progetto
}

variable "gcp_region" {
  description = "La regione GCP principale per il deployment delle risorse."
  type        = string
  default     = "europe-west1" # Esempio: Cambia se preferisci un'altra regione
}

variable "gcp_zone" {
  description = "La zona GCP predefinita per le istanze a zona singola."
  type        = string
  default     = "europe-west1-b" # Esempio: Cambia se preferisci un'altra zona
}

variable "network_name" {
  description = "Nome della VPC network principale."
  type        = string
  default     = "security-sim-vpc"
}

variable "subnet_configs" {
  description = "Configurazioni delle subnet (nome, CIDR, descrizione)."
  type = list(object({
    name        = string
    ip_cidr     = string
    description = string
  }))
  default = [
    { name = "dmz-subnet", ip_cidr = "10.0.1.0/24", description = "Subnet per servizi esposti (Web, Attacker)." },
    { name = "internal-subnet", ip_cidr = "10.0.2.0/24", description = "Subnet per client interni e servizi applicativi." },
    { name = "db-subnet", ip_cidr = "10.0.3.0/24", description = "Subnet per il database." }
  ]
}

variable "instance_configs" {
  description = "Configurazioni delle istanze GCE simulate."
  type = map(object({
    name             = string
    machine_type     = string
    zone             = string
    image            = string
    subnet_name      = string
    tags             = list(string)
    startup_script   = string
    create_public_ip = bool
    # --- NUOVO: Aggiungi queste proprietà per i metadati e il Service Account ---
    metadata             = optional(map(string), {}) # Rendi opzionale con default vuoto
    service_account_email = optional(string)
    service_account_scopes = optional(list(string))
  }))
  default = {
    "web-server" = {
      name             = "web-server-01"
      machine_type     = "e2-medium"
      zone             = "europe-west1-b"
      image            = "debian-cloud/debian-11"
      subnet_name      = "dmz-subnet"
      tags             = ["web-server", "dmz-instance"]
      startup_script   = "#!/bin/bash\nsudo apt-get update && sudo apt-get install -y nginx && echo '<h1>Simulated Web Server</h1>' | sudo tee /var/www/html/index.html && sudo systemctl start nginx",
      create_public_ip = true
    },
    "db-server" = {
      name             = "db-server-01"
      machine_type     = "e2-medium"
      zone             = "europe-west1-b"
      image            = "debian-cloud/debian-11"
      subnet_name      = "db-subnet"
      tags             = ["db-server", "internal-instance"]
      startup_script   = "#!/bin/bash\nsudo apt-get update && sudo apt-get install -y mariadb-server && sudo systemctl start mariadb && sudo systemctl enable mariadb", # Solo esempio, configura meglio MariaDB
      create_public_ip = false
    },
    #--- NUOVO Aggiungi l'isntanza DNS server ---
    "dns-server" = {
      name             = "dns-server-01"
      machine_type     = "e2-small"
      zone             = "europe-west1-b"
      image            = "debian-cloud/debian-11"
      subnet_name      = "dmz-subnet"
      tags             = ["dns-server"]
      #Esempio di script di avvio per un server DNS (BIND9)
      startup_script   = "#!/bin/bash\nsudo apt-get update && sudo apt-get install -y bind9 bind9utils bind9-doc && sudo systemctl start bind9 && sudo systemctl enable bind9",
      create_public_ip = true # Potrebbe servire un IP pubblico se deve risolvere anche da fuori
    }
    "internal-client-1" = {
      name             = "internal-client-01"
      machine_type     = "e2-small"
      zone             = "europe-west1-b"
      image            = "debian-cloud/debian-11"
      subnet_name      = "internal-subnet"
      tags             = ["internal-client"]
      startup_script   = "#!/bin/bash\nsudo apt-get update && sudo apt-get install -y python3 python3-pip && pip3 install requests dnspython psycopg2-binary",
      create_public_ip = false
     
    },
    "attacker-node" = {
      name             = "attacker-node-01"
      machine_type     = "e2-small"
      zone             = "europe-west1-b"
      image            = "debian-cloud/debian-11"
      subnet_name      = "dmz-subnet"
      tags             = ["attacker-node"]
      startup_script   = "#!/bin/bash\nsudo apt-get update && sudo apt-get install -y nmap hydra python3 python3-pip && pip3 install python-nmap paramiko",
      create_public_ip = true # Potrebbe servire per simulare attacchi esterni
    }
  }
}

variable "cloudsql_database_version" {
  description = "Versione del database Cloud SQL"
  type        = string
  default     = "MYSQL_8_0"
}

variable "cloudsql_instance_tier" {
  description = "Tier della macchina per l'istanza Cloud SQL."
  type        = string
  default     = "db-f1-micro" # Tier economico per test
}

variable "cloudsql_database_name" {
  description = "Nome del database principale in Cloud SQL."
  type        = string
  default     = "simulation_data"
}

variable "cloudsql_user_name" {
  description = "Nome utente per l'accesso al database Cloud SQL."
  type        = string
  default     = "simuser"
}

variable "cloudsql_user_password" {
  description = "Password per l'utente del database Cloud SQL. **CAMBIALA IN PRODUZIONE!**"
  type        = string
  sensitive   = true
  default     = "password123!" 
}

variable "gcs_bucket_name" {
  description = "Nome del bucket Cloud Storage per i dataset CSV. Deve essere globalmente unico."
  type        = string
  default     = "gruppo-9-456912-gcs-bucket"
}