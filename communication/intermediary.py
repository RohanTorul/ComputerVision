import zmq
import socket

# Setup ZeroMQ subscriber
context = zmq.Context()
zmq_socket = context.socket(zmq.SUB)
zmq_socket.connect("tcp://localhost:5555")
zmq_socket.setsockopt_string(zmq.SUBSCRIBE, "")

# Setup TCP server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('localhost', 6666))  # New port for socket subscriber
server_socket.listen(5)

print("Waiting for socket subscriber to connect...")
client_socket, _ = server_socket.accept()
print("Socket subscriber connected.")

while True:
    message = zmq_socket.recv_string()
    print(f"Received from ZMQ: {message}")

    try:
        client_socket.sendall(message.ljust(24).encode())  # Ensure 24-char messages
    except (BrokenPipeError, ConnectionResetError):
        print("Socket subscriber disconnected. Waiting for reconnection...")
        client_socket, _ = server_socket.accept()
        print("Reconnected to socket subscriber.")
