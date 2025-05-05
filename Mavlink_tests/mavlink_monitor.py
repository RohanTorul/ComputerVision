from pymavlink import mavutil
import time
import sys

class MAVTextListener:
    def __init__(self):
        self.connection = None
        self.running = True
        self.connection_string = 'tcp:localhost:14550'
        self.reconnect_interval = 0.5  # Seconds between connection attempts
        self.timeout = 5  # Seconds before considering connection dead
        self.last_message_time = time.time()

    def connect(self):
        """Establish MAVLink connection with retries"""
        print(f"Connecting to {self.connection_string}...")
        try:
            self.connection = mavutil.mavlink_connection(
                self.connection_string,
                autoreconnect=False,
                source_system=255,
                source_component=0
            )
            
            if self.connection.wait_heartbeat(timeout=self.reconnect_interval):
                self.last_message_time = time.time()
                print("Connected to MAVLink!")
                return True
            return False
            
        except Exception as e:
            print(f"Connection failed: {str(e)}")
            return False

    def check_connection(self):
        """Verify connection is still active"""
        return time.time() - self.last_message_time < self.timeout

    def process_statustext(self, msg):
        """Handle STATUSTEXT messages"""
        self.last_message_time = time.time()
        try:
            # Decode the text payload
            text = msg.text#.decode('utf-8', errors='ignore').rstrip('\x00')
            print(f"\n[STATUS MESSAGE] {text}")
        except Exception as e:
            print(f"Error decoding message: {str(e)}")

    def run(self):
        """Main monitoring loop"""
        while self.running:
            try:
                if not self.connection or not self.check_connection():
                    if self.connection:
                        self.connection.close()
                    if not self.connect():
                        #time.sleep(self.reconnect_interval)
                        continue

                # Process messages
                while True:
                    msg = self.connection.recv_match(type=['STATUSTEXT'],blocking = True)
                    if msg:
                        if msg.get_type() == 'STATUSTEXT' and msg.severity ==6:
                            self.process_statustext(msg)
                        else:
                            # Update last message time for any message type
                            self.last_message_time = time.time()
                    else:
                        break

                #time.sleep(0.01)

            except KeyboardInterrupt:
                self.running = False
                print("\nShutting down...")
                break

            except Exception as e:
                print(f"Error: {str(e)}")
                self.connection = None
                #time.sleep(1)

        if self.connection:
            self.connection.close()

if __name__ == "__main__":
    listener = MAVTextListener()
    try:
        listener.run()
    except KeyboardInterrupt:
        listener.running = False
        sys.exit(0)