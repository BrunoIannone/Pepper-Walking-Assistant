from ..map.room_mapper import RoomMapper


class PositionManager:
    def __init__(self, map_path):
        self.room_mapper = RoomMapper.from_file(map_path)
        self.path = []

        self.current_node_index = 0
        self.current_room = None
        self.next_room = None

    def is_valid(self, room):
        return room in self.room_mapper.rooms.keys()

    def compute_path(self, start_room, end_room, accessibility_level):
        path_len, path = self.room_mapper.shortest_path(start_room, end_room, accessibility_level)
        if path_len == float('inf'):
            return []
        self.path = [self.room_mapper.rooms[node] for node in path]

        self.current_room = self.path[self.current_node_index]
        self.next_room = self.path[self.current_node_index + 1]  # At least two nodes

        return self.path

    def get_current_room(self):
        if len(self.path) == 0:
            raise ValueError('Path is empty')
        return self.current_room

    def get_next_room(self):
        if len(self.path) == 0:
            raise ValueError('Path is empty')
        return self.next_room

    def next(self):
        if self.current_node_index < len(self.path):
            self.current_room = self.next_room
            self.current_node_index += 1
            self.next_room = self.path[self.current_node_index]
            return self.current_room
        else:
            return None

    def is_path_complete(self):
        return self.current_node_index >= len(self.path)

    def reset(self):
        self.current_node_index = 0