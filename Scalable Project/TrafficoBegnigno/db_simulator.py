import mysql.connector

def simulate_db_access(ip, user="root", password="", anomaly=False):
    try:
        conn = mysql.connector.connect(
            host=ip,
            user=user,
            password=password,
            database="test" if not anomaly else "information_schema"
        )
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        for row in cursor.fetchall():
            print(f"[DB] Table: {row}")
        conn.close()
    except Exception as e:
        print(f"[DB] Connection error: {e}")
