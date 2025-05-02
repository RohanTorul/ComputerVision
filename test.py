# subscriber.py
import socket

HOST = 'localhost'
PORT = 12345

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print("Connected to Lua server.")
    try:
        while True:
            data = s.recv(1024).decode()
            if not data:
                break
            print("Received:", data.strip())
    except KeyboardInterrupt:
        print("Disconnected.")
