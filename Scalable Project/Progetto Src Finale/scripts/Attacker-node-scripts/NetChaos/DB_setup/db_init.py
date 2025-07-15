import os
from google.cloud.sql.connector import Connector
import pymysql

# Funzione per recuperare le variabili d'ambiente
def get_db_env_vars():
    """Recupera le variabili d'ambiente necessarie per la connessione al DB."""
    return {
        'CLOUDSQL_CONNECTION_NAME': os.environ.get('CLOUDSQL_CONNECTION_NAME'),
        'CLOUDSQL_DATABASE_NAME': os.environ.get('CLOUDSQL_DATABASE_NAME'),
        'CLOUDSQL_USER_NAME': os.environ.get('CLOUDSQL_USER_NAME'),
        'CLOUDSQL_USER_PASSWORD': os.environ.get('CLOUDSQL_USER_PASSWORD')
    }

# Funzione per ottenere una connessione al database
def get_cloudsql_conn(env_vars):
    """Stabilisce una connessione al database Cloud SQL."""
    try:
        with Connector() as connector:
            conn = connector.connect(
                env_vars['CLOUDSQL_CONNECTION_NAME'],
                'pymysql',
                user=env_vars['CLOUDSQL_USER_NAME'],
                password=env_vars['CLOUDSQL_USER_PASSWORD'],
                db=env_vars['CLOUDSQL_DATABASE_NAME']
            )
        print("Connessione a Cloud SQL stabilita per DB Init.")
        return conn
    except Exception as e:
        print(f"Errore durante la connessione a Cloud SQL per DB Init: {e}")
        return None

# Funzione per creare le tabelle
def create_tables(conn, sql_script_path):
    """Esegue lo script SQL per creare le tabelle."""
    try:
        cursor = conn.cursor()
        with open(sql_script_path, 'r') as f:
            sql_commands = f.read()

        for command in sql_commands.split(';'):
            command = command.strip()
            if command:
                try:
                    cursor.execute(command)
                    print(f'Eseguito comando SQL: {command[:70]}...')
                except pymysql.err.OperationalError as e:
                    if 'Table ' in str(e) and 'already exists' in str(e):
                        print(f'AVVISO: Tabella già esistente per comando: {command[:70]}... - {e}')
                    else:
                        print(f'ERRORE SQL: {e}')
                        raise # Rilancia altri errori operativi
        conn.commit()
        cursor.close()
        print("Tabelle verificate/create con successo nel database Cloud SQL.")
        return True
    except Exception as e:
        print(f"Errore CRITICO durante la creazione delle tabelle: {e}")
        return False

if __name__ == "__main__":
    SQL_SCRIPT_PATH = os.path.expanduser('~/NetChaos/DB_setup/create_tables.sql')

    env_vars = get_db_env_vars()

    # Validazione delle variabili d'ambiente
    missing_vars = [k for k, v in env_vars.items() if v is None]
    if missing_vars:
        print(f"Errore: Variabili d'ambiente mancanti: {', '.join(missing_vars)}")
        exit(1)

    conn = None
    try:
        conn = get_cloudsql_conn(env_vars)
        if conn:
            if not create_tables(conn, SQL_SCRIPT_PATH):
                exit(1) 
        else:
            exit(1) 
    except Exception as e:
        print(f"Errore generale nel main di db_init.py: {e}")
        exit(1)
    finally:
        if conn:
            conn.close()