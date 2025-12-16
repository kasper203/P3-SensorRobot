import socket
import json
import mysql.connector
from mysql.connector import Error

# ========================
# MySQL Configuration
# ========================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",          # change if needed
    "password": "",          # change if needed
    "database": "jetbot_data",
    "port": 3306
}

# ========================
# UDP Configuration
# ========================
UDP_IP = "0.0.0.0"   # listen on all interfaces
UDP_PORT = 9999

# ========================
# Database Connection
# ========================
def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print("MySQL connection error:", e)
        return None

# ========================
# Insert Data into DB
# ========================
def insert_data(mq135, mq4, x, y):
    conn = get_db_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO mine_data (mq_135, mq_4, x_coordinate, y_coordinate)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (mq135, mq4, x, y))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Inserted: mq135={mq135}, mq4={mq4}, x={x}, y={y}")
    except Error as e:
        print("DB insert error:", e)

# ========================
# UDP Server
# ========================
def start_udp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    print(f"UDP server listening on {UDP_IP}:{UDP_PORT}")

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            message = data.decode("utf-8")

            print(f"Received from {addr}: {message}")

            payload = json.loads(message)

            mq135 = float(payload["mq135"])
            mq4   = float(payload["mq4"])
            x     = int(payload["x"])
            y     = int(payload["y"])

            insert_data(mq135, mq4, x, y)

        except json.JSONDecodeError:
            print("Invalid JSON received")
        except KeyError as e:
            print("Missing field:", e)
        except Exception as e:
            print("Error:", e)

# ========================
# Main
# ========================
if __name__ == "__main__":
    start_udp_server()
