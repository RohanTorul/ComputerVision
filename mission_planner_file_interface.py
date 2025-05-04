# parser():
#     chunkArray = []
#     fire_source_info = ""
#     chunk = False

#     fire_source = check_file_exists(fire_source_file)

#     if fire_source_info == "" and fire_source is True:
#         fire_source_info = parse_txt(fire_source_file)
    
#     if chunk not True:
#         if check_file_exists(chunk_list.txt) == False:
#             print("Chunk list file not found. Please check the file path.")
#         else:
#             bottomLine = get_bottom_line(chunk_list.txt)
#             CurrentChunk = getChunkCount(bottomLine)
#             chunk = True
#     else:
#         bottomLine = get_bottom_line(chunk_list.txt)
#         if CurrentChunk != getChunkCount(bottomLine):
#             CurrentChunk = getChunkCount(bottomLine)
#             ir_detection()
#             timer = 0
#         else:
#             timer += 1

#     if timer > 20:
#         print("No new chunks found. Exiting...")
#         saveKMLFile()
# parser():
#     chunkArray = []
#     fire_source_info = ""
#     chunk = False

#     fire_source = check_file_exists(fire_source_file)

#     if fire_source_info == "" and fire_source is True:
#         fire_source_info = parse_txt(fire_source_file)
    
#     if chunk not True:
#         if check_file_exists(chunk_list.txt) == False:
#             print("Chunk list file not found. Please check the file path.")
#         else:
#             bottomLine = get_bottom_line(chunk_list.txt)
#             CurrentChunk = getChunkCount(bottomLine)
#             chunk = True
#     else:
#         bottomLine = get_bottom_line(chunk_list.txt)
#         if CurrentChunk != getChunkCount(bottomLine):
#             CurrentChunk = getChunkCount(bottomLine)
#             ir_detection()
#             timer = 0
#         else:
#             timer += 1

#     if timer > 20:
#         print("No new chunks found. Exiting...")
#         saveKMLFile()

import io #SEE HERE
class MissionPlannerFileParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.dict = {}
        #self.file = open(file_path, 'r')
        

    def read_last_line(self):
        with io.open(self.file_path, 'r') as f:
            last_line = f.readlines()[-1]
        return last_line

    def parse_line_to_dict(self, line):
        if not line:
            return None
        pairs = line.strip().split(';')
        dict = {key: value for key, value in (pair.split(':') for pair in pairs)}
        print(dict)
        return dict
    
    def update_dict(self):
        line = self.read_last_line()
        if not line:
            return None
        self.dict = self.parse_line_to_dict(line)
        return self.dict
    

