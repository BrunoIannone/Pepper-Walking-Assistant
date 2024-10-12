from demo.scripts.src.map.room_mapper import RoomMapper


class PositionManager:
    def __init__(self, map_path):
        self.room_mapper = RoomMapper.from_file(map_path)
        self.path = []
        self.current_node_index = 0

    def compute_path(self, start_room, end_room, accessibility_level):
        _, path = self.room_mapper.shortest_path(start_room, end_room, accessibility_level)
        self.path = [self.room_mapper.rooms[node] for node in path]
        self.current_node_index = 0
        return self.path

    def get_next_target(self):
        if self.current_node_index < len(self.path):
            target = self.path[self.current_node_index]
            self.current_node_index += 1
            return target
        else:
            return None

    def is_path_complete(self):
        return self.current_node_index >= len(self.path)

    def reset(self):
        self.current_node_index = 0