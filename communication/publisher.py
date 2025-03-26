import zmq
import time

context = zmq.Context()
socket = context.socket(zmq.PUB)  # PUB = Publisher mode
socket.bind("tcp://localhost:5555")  # Bind to a port

while True:
    # Example: Detect something with OpenCV and send commands
    direction = "LEFT" if time.time() % 2 > 1 else "RIGHT"
    value = int(time.time() % 10)  # Simulated value

    message = f"{direction} {value}"
    print(f"Sending: {message}")
    socket.send_string(message)

    time.sleep(0.5)  # Simulate real-time updates
