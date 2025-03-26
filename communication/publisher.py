import socket
import time

# Create a socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reusing the port
server_socket.bind(('localhost', 5555))
server_socket.listen(5)  # Allow multiple reconnection attempts

print("Waiting for subscriber to connect...")

while True:
    client_socket, client_address = server_socket.accept()
    print(f"Connected to {client_address}")

    try:
        message = "Hello, Lua Subscriber!  "  # 24 characters long
        while True:
            client_socket.sendall(message.encode())  # Send the message
            print(f"Sent: {message}")
            time.sleep(0.1)  # Send every 2 seconds
    except (BrokenPipeError, ConnectionResetError, socket.error):
        print("Client disconnected. Waiting for a new connection...")
        client_socket.close()  # Ensure socket is closed and go back to waiting
