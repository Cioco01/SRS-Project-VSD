# scripts/db_simulator.py
import mysql.connector
import json
from datetime import datetime
import os
import requests # Per get_local_ip

# Funzione per ottenere l'IP locale, riusata da http_simulator
def get_local_ip():
    try:
        response = requests.get("http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/ip",
                                headers={"Metadata-Flavor": "Google"}, timeout=0.5)
        if response.status_code == 200:
            return response.text
    except requests.exceptions.RequestException:
        pass
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

LOCAL_IP = get_local_ip()

def simulate_db_access(ip, user="sim_user", password="your_strong_password", anomaly=False,log_file=os.path.join(os.path.dirname(__file__),"db_traffic.log")):
    """
    Simula l'accesso a un database MySQL/MariaDB.
    Introduce un'anomalia tentando di accedere a un database insolito.
    Registra gli eventi in un file di log JSON.
    """
    db_to_access = "information_schema" if anomaly else "test"
    is_anomaly = anomaly # L'anomalia è definita dal database tentato

    print(f"[DB Simulator] Attempting DB access to {ip}/{db_to_access} (Anomaly: {anomaly})")

    timestamp = datetime.now().isoformat()
    try:
        conn = mysql.connector.connect(
            host=ip,
            user=user,
            password=password,
            database=db_to_access,
            connection_timeout=5 # Timeout per la connessione
        )
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = [row[0] for row in cursor.fetchall()]
        
        log_entry = {
            "timestamp": timestamp,
            "event_type": "DB_Access",
            "source_ip": LOCAL_IP,
            "destination_ip": ip,
            "destination_port": 3306,
            "db_user": user,
            "db_name_attempted": db_to_access,
            "status": "Success",
            "tables_found": tables,
            "anomaly": is_anomaly,
            "message": f"Successfully accessed database '{db_to_access}'. Tables: {tables}"
        }
        print(f"[DB] Successfully connected to {db_to_access}. Tables: {tables}")
        conn.close()
    except mysql.connector.Error as err:
        log_entry = {
            "timestamp": timestamp,
            "event_type": "DB_Access_Failed",
            "source_ip": LOCAL_IP,
            "destination_ip": ip,
            "destination_port": 3306,
            "db_user": user,
            "db_name_attempted": db_to_access,
            "status": "Failed",
            "anomaly": is_anomaly,
            "error_code": err.errno,
            "sql_state": err.sqlstate,
            "error_message": err.msg,
            "message": f"[DB] Connection error: {err.msg}"
        }
        print(f"[DB] Connection error: {err.msg}")
    except Exception as e:
        log_entry = {
            "timestamp": timestamp,
            "event_type": "DB_Access_Failed",
            "source_ip": LOCAL_IP,
            "destination_ip": ip,
            "destination_port": 3306,
            "db_user": user,
            "db_name_attempted": db_to_access,
            "status": "Other Error",
            "anomaly": is_anomaly,
            "error": str(e),
            "message": f"[DB] An unexpected DB error occurred: {e}"
        }
        print(f"[DB] An unexpected DB error occurred: {e}")

    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

if __name__ == '__main__':
    # Esempio di utilizzo standalone per test locali
    simulate_db_access("127.0.0.1", user="root", password="", anomaly=False)
    simulate_db_access("127.0.0.1", user="root", password="", anomaly=True) # Questo dovrebbe generare un errore di accesso
