import socket
import time

# Set up the server socket (Publisher)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("localhost", 5555))  # Bind to localhost and port 5555
server_socket.listen(1)  # Wait for a client connection

print("Waiting for a client to connect...")
client_socket, client_address = server_socket.accept()  # Accept the client connection
print(f"Client connected: {client_address}")

while True:
    # Example: Detect something with OpenCV and send commands
    direction = "LEFT" if time.time() % 2 > 1 else "RIGHT"
    value = int(time.time() % 10)  # Simulated value

    message = f"{direction} {value}"
    print(f"Sending: {message}")
    
    # Send the message to the client
    client_socket.sendall(message.encode('utf-8'))

    time.sleep(0.5)  # Simulate real-time updates

# Close the connection
client_socket.close()
server_socket.close()
