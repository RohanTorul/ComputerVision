# IMPORTANT: MODIFY WSL CONFIG FILE IF THEY CANNOT CONNECT
# WSL: /etc/wsl.conf
import socket
class MissionPlannerInterface:
    """
    Interface for the Mission Planner.
    uses sockets to communicate with lua scripts.
    """

    def __init__(self,port=5760):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(('localhost', port))  # New port for socket subscriber
        self.socket.setblocking(False)

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