# IMPORTANT: MODIFY WSL CONFIG FILE IF THEY CANNOT CONNECT
# WSL: /etc/wsl.conf
import socket
from pymavlink import mavutil
import time
class MissionPlannerInterface:
    """
    Interface for the Mission Planner.
    uses sockets to communicate with lua scripts.
    """

    def __init__(self,port=5760, dict = {"STAT":None,"ALT":None,"POS":None}):

        #Mavlink connection
        self.mavlink_connection = None
        self.mavlink_running = True
        self.mavlink_connection_string = 'tcp:127.0.0.1:14550'
        self.mavlink_reconnect_interval = 0.5  # Seconds between connection attempts
        self.mavlink_timeout = 5  # Seconds before considering connection dead
        self.mavlink_last_message_time = time.time()
        self.mavlink_dict = dict



        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(('localhost', port))  # New port for socket subscriber
        self.socket.setblocking(False)
        self.dict = {}

    def mavlink_connect(self):
        '''
        Establish Mavlink connection with retries'''

        print(f"Connecting to {self.mavlink_connection_string}...")
        try:
            self.mavlink_connection = mavutil.mavlink_connection(
                self.mavlink_connection_string,
                autoreconnect=False,
                source_system=255,
                source_component=0
            )

            if self.mavlink_connection.wait_heartbeat(timeout=self.mavlink_reconnect_interval):
                self.mavlink_last_message_time = time.time()
                print("Connected to MAVLink!")
                return True
            return False

        except Exception as e:
            print(f"Connection failed: {str(e)}")
            return False
        
    def mavlink_check_connection(self):
        """Verify connection is still active"""
        return time.time() - self.mavlink_last_message_time < self.mavlink_timeout
        


    def mavlink_step(self):
        if not self.mavlink_connection or not self.mavlink_check_connection():
            if self.mavlink_connection:
                self.mavlink_connection.close()
            if not self.mavlink_connect():
                time.sleep(self.mavlink_reconnect_interval)
                return False
            
            # Process messages
            mavlink_stat_message_obtained = False
            while not mavlink_stat_message_obtained:
                print("Waiting for STATUSTEXT message...")
                msg = self.mavlink_connection.recv_match(type=['STATUSTEXT'],blocking = True)
                if msg:
                    if msg.get_type() == 'STATUSTEXT' and msg.severity ==6 and msg.text[0:4] == "STAT":
                        self.mavlink_dict = self.parse_line_to_dict(msg.text)
                        mavlink_stat_message_obtained = True
                    else:
                        # Update last message time for any message type
                        self.mavlink_last_message_time = time.time()
                else:
                    break
           
    def mavlink_close(self):
        if self.mavlink_connection:
            self.mavlink_connection.close()



    def parse_line_to_dict(self,line):
        print(f"Parsing line: {line[0:-1]}")  # Debugging line
        pairs = line.strip().split(';')  # Remove the last '\n' and split by ';'
        print(f"Parsed pairs: {pairs}")
        if len(pairs) == 0:
            return {}
        else:
            dict = {key: value for key, value in (pair.split(':') for pair in pairs)}
            print(f"Dict: {dict}")
            return dict
    
    def get_data(self,attribute):
        """
        Get the data from the Mission Planner.
        """
        try:
            recieved_packet = self.socket.recv(1024).decode()  # Read a line from the socket
            print(f"Received packet: {recieved_packet}")  # Debugging line
            packet_dict = self.parse_line_to_dict(recieved_packet[0:-1])
            if attribute in packet_dict:
                return packet_dict[attribute]
            else:
                return None
        except BlockingIOError:
            #print("No data available yet.")
            return None
    def get_dict(self):
        try:
            recieved_packet = self.socket.recv(1024).decode()  # Read a line from the socket
            print(f"Received packet: {recieved_packet}")  # Debugging line
            packet_dict = self.parse_line_to_dict(recieved_packet[0:-1])
            return packet_dict
        except BlockingIOError:
            #print("No data available yet.")
            return None


    # def get_uav_position(self):
    #     try:
    #         """
    #         Get the UAV position from the Mission Planner.
    #         """
    #         recieved_packet = self.socket.recv(1024).decode()
    #         packet_dict = self.parse_line_to_dict(recieved_packet)
    #         if 'GPS' in packet_dict:
    #             gps_data = packet_dict['GPS']
    #             lat, lon = map(float, gps_data.split(','))
    #             return (lat, lon)
    #         else:
    #             return None
    #     except BlockingIOError:
    #         print("No data available yet.")
    #         return None  # or handle appropriately
        
    # def get_uav_altitude(self):
    #     try:
    #         """
    #         Get the UAV altitude from the Mission Planner.
    #         """
    #         recieved_packet = self.socket.recv(1024).decode()
    #         packet_dict = self.parse_line_to_dict(recieved_packet)
    #         if 'ALT' in packet_dict:
    #             alt = packet_dict['ALT']
    #             alt = float(alt)
    #             return alt
    #         else:
    #             return None
    #     except BlockingIOError:
    #         print("No data available yet.")
    #         return None