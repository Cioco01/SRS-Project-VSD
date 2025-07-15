from flask import Flask, request, jsonify, send_from_directory, Response
import os
import io
import pandas as pd
from google.cloud.sql.connector import Connector
import pymysql
import time
from datetime import datetime
from google.cloud import storage

app = Flask(__name__, static_folder='static')

# --- Configurazione Cloud SQL ---
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID', 'gruppo-9-456912')
CLOUDSQL_CONNECTION_NAME = os.environ.get('CLOUDSQL_CONNECTION_NAME', 'gruppo-9-456912:europe-west1:simulation-db-instance')
CLOUDSQL_DATABASE_NAME = os.environ.get('CLOUDSQL_DATABASE_NAME', 'simulation_data')
CLOUDSQL_USER_NAME = os.environ.get('CLOUDSQL_USER_NAME', 'simuser')
CLOUDSQL_USER_PASSWORD = os.environ.get('CLOUDSQL_USER_PASSWORD', 'password') # Miglirore usare Secret Manager in produzione!
GCS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', 'gruppo-9-456912-traffic-data')

connector = Connector()
storage_client = storage.Client() 
def get_cloudsql_conn():
    """Stabilisce una connessione al database Cloud SQL."""
    try:
        conn = connector.connect(
            CLOUDSQL_CONNECTION_NAME,
            "pymysql",
            user=CLOUDSQL_USER_NAME,
            password=CLOUDSQL_USER_PASSWORD,
            db=CLOUDSQL_DATABASE_NAME
        )
        return conn
    except Exception as e:
        print(f"Errore durante la connessione a Cloud SQL per Data Viewer: {e}")
        return None

# --- API Endpoints per la GUI ---

@app.route('/')
def index():
    """Serve la pagina HTML della GUI del visualizzatore dati."""
    return send_from_directory(app.static_folder, 'data_viewer.html')

@app.route('/api/get_captured_data', methods=['GET'])
def get_captured_data():
    """Recupera i dati catturati dalla tabella raw_network_traffic."""
    conn = None
    try:
        conn = get_cloudsql_conn()
        if not conn:
            return jsonify({"status": "error", "message": "Impossibile connettersi a Cloud SQL."}), 500

        # Aggiornata la query per la nuova tabella e colonne
        query = """
            SELECT
                id, timestamp_capture, source_ip, destination_ip,
                source_port, destination_port, protocol,
                packet_length, flags, ttl, description, full_line
            FROM raw_network_traffic
        """
        
        # Filtri opzionali dalla richiesta
        protocol = request.args.get('protocol')
        source_ip = request.args.get('source_ip')
        destination_ip = request.args.get('destination_ip')
        source_port = request.args.get('source_port', type=int)
        destination_port = request.args.get('destination_port', type=int)
        
        conditions = []
        params = []
        
        if protocol:
            conditions.append("protocol = %s")
            params.append(protocol)
        if source_ip:
            conditions.append("source_ip = %s")
            params.append(source_ip)
        if destination_ip:
            conditions.append("destination_ip = %s")
            params.append(destination_ip)
        if source_port is not None:
            conditions.append("source_port = %s")
            params.append(source_port)
        if destination_port is not None:
            conditions.append("destination_port = %s")
            params.append(destination_port)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY timestamp_capture DESC LIMIT 1000" # Limite per evitare carichi eccessivi

        df = pd.read_sql(query, conn, params=params)
        
        # Riempi i NaN con stringhe vuote per JSON compatibile
        df = df.fillna('-')
        # Rimuovi l'indice e converti in lista di dizionari per JSON
        data = df.to_dict(orient='records')
        
        


        return jsonify({"status": "success", "data": data})

    except pd.io.sql.DatabaseError as e:
        print(f"Errore query database: {e}")
        return jsonify({"status": "error", "message": f"Errore durante il recupero dati dal database (raw_network_traffic): {str(e)}. La tabella potrebbe non esistere o non contenere dati."}), 500
    except Exception as e:
        print(f"Errore generico nel recupero dati: {e}")
        return jsonify({"status": "error", "message": f"Errore generico: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/export_csv', methods=['GET'])
def export_csv():
    """Esporta tutti i dati catturati come file CSV dalla tabella raw_network_traffic."""
    conn = None
    try:
        conn = get_cloudsql_conn()
        if not conn:
            return jsonify({"status": "error", "message": "Impossibile connettersi a Cloud SQL."}), 500

        # Aggiornata la query per la nuova tabella e colonne
        query = """
            SELECT
                timestamp_capture, source_ip, destination_ip,
                source_port, destination_port, protocol,
                packet_length, flags, ttl, description, full_line
            FROM raw_network_traffic
            ORDER BY timestamp_capture ASC
        """
        df = pd.read_sql(query, conn)
        
        # df = df.fillna('-')  # SE C'E' BISOGNO DI RIMUOVERE I NaN
        
        df['timestamp_capture'] = pd.to_datetime(df['timestamp_capture'], unit='us').dt.strftime('%Y-%m-%d %H:%M:%S.%f')

        # Buffer di memoria per il CSV
        output = io.StringIO()
        df.to_csv(output, index=False)
        csv_data = output.getvalue()
        output.close()

        # Generazione nome file univoco con il datetime della richiesta di esportazione
        export_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"raw_network_traffic_export_{export_timestamp}.csv"
        
        # Carica il file su Google Cloud Storage
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(file_name)
        blob.upload_from_string(csv_data, content_type='text/csv')
        
        print(f"File '{file_name}' caricato con successo nel bucket GCS '{GCS_BUCKET_NAME}'.")

        return jsonify({
            "status": "success",
            "message": f"Dati esportati con successo in '{file_name}' e caricati su Google Cloud Storage.",
            "gcs_path": f"gs://{GCS_BUCKET_NAME}/{file_name}"
        })

    except Exception as e:
        print(f"Errore durante l'esportazione CSV: {e}")
        return jsonify({"status": "error", "message": f"Errore esportazione CSV: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/clear_data', methods=['POST'])
def clear_data():
    """Elimina tutti i dati dalla tabella raw_network_traffic."""
    conn = None
    try:
        conn = get_cloudsql_conn()
        if not conn:
            return jsonify({"status": "error", "message": "Impossibile connettersi a Cloud SQL."}), 500
 
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE raw_network_traffic")
        conn.commit()
        cursor.close()
        return jsonify({"status": "success", "message": "Dati eliminati con successo dalla tabella raw_network_traffic."})
    except Exception as e:
        print(f"Errore durante l'eliminazione dei dati: {e}")
        return jsonify({"status": "error", "message": f"Errore eliminazione dati: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/status', methods=['GET'])
def get_status():
    """Endpoint per verificare lo stato del Data Viewer Backend."""
    return jsonify({"status": "Data Viewer Backend running", "timestamp": time.time()})

if __name__ == '__main__':
    print("Avvio Flask Data Viewer Backend su http://0.0.0.0:5004")
    app.run(host='0.0.0.0', port=5004, debug=False)
