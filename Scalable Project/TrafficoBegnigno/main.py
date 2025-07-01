import yaml
from http_simulator import simulate_http_traffic
from dns_simulator import simulate_dns_queries
from db_simulator import simulate_db_access

with open(r"C:/Users/loren/Desktop/Uni/Scalable Project/TrafficoBegnigno/config.yaml") as f:
    config = yaml.safe_load(f)

# HTTP
simulate_http_traffic(config["web_server_ip"], port=8081 if config["simulate_http_port_change"] else 80)

# DNS
domains = ["example.com", "google.com", "unibo.it"]
simulate_dns_queries(config["dns_server_ip"], domains, spike=config["simulate_dns_spike"])

# DB
simulate_db_access(config["db_server_ip"], anomaly=config["simulate_unusual_db_client"])
