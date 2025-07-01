import dns.resolver
import time

def simulate_dns_queries(dns_ip, domains, spike=False):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dns_ip]
    for i in range(50 if spike else 5):
        domain = domains[i % len(domains)]
        try:
            answer = resolver.resolve(domain, 'A')
            print(f"[DNS] {domain} -> {answer[0]}")
        except Exception as e:
            print(f"[DNS] Query failed: {e}")
        time.sleep(0.1 if spike else 1)
