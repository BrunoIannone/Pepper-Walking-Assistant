from matplotlib import pyplot as plt

from graph import Graph
from room import Room


class RoomMapper(Graph):
    
    def __init__(self):
        super(RoomMapper, self).__init__()
        self.rooms = {}

    def add_room(self, name, x, y):
        room = Room(name, x, y)
        self.rooms[name] = room
        self.add_node(room)
        return room

    def add_connection(self, room1_name, room2_name, distance=1, accessibility=0):
        room1 = self.rooms[room1_name]
        room2 = self.rooms[room2_name]
        self.add_edge(room1, room2, distance, accessibility)

    def get_room(self, name):
        return self.rooms.get(name)

    def find_path(self, start_name, end_name, max_accessibility=float('inf')):
        start_room = self.rooms[start_name]
        end_room = self.rooms[end_name]
        distance, path = self.shortest_path(start_room, end_room, max_accessibility)
        return distance, path

    def save(self, filename):
        with open(filename, 'w') as f:
            # Write rooms (coordinates)
            for room in self.rooms.itervalues():
                f.write("{0} {1} {2}\n".format(room.value, room.x, room.y))

            # Write empty line as delimiter
            f.write("\n")

            # Write connections
            for node, neighbors in self.adjacency_list.iteritems():
                for neighbor, weight, accessibility in neighbors:
                    if self.directed or node.value < neighbor.value:  # Avoid duplicate edges in undirected graph
                        f.write("{0} {1} {2} {3}\n".format(
                            node.value, neighbor.value, weight, accessibility))

    def load(self, filename):
        self.rooms.clear()
        self.adjacency_list.clear()

        with open(filename, 'r') as f:
            # Read all lines and split by empty line
            content = f.read().strip()
            coords_section, graph_section = content.split('\n\n')

            # Process coordinates
            for line in coords_section.split('\n'):
                if line.strip():
                    name, x, y = line.strip().split()
                    self.add_room(name, float(x), float(y))

            # Process graph connections
            for line in graph_section.split('\n'):
                if line.strip():
                    room1, room2, distance, accessibility = line.strip().split()
                    self.add_connection(room1, room2, float(distance), int(accessibility))

    @classmethod
    def from_file(cls, filename):
        mapper = cls()
        mapper.load(filename)
        return mapper

    def draw(self):
        plt.figure(figsize=(8, 6))

        # Draw edges
        for node, neighbors in self.adjacency_list.items():
            for neighbor, weight, accessibility_weight in neighbors:
                plt.plot([self.rooms[node].x, self.rooms[neighbor].x],
                         [self.rooms[node].y, self.rooms[neighbor].y], 'k-')
                plt.text((self.rooms[node].x + self.rooms[neighbor].x) / 2,
                         (self.rooms[node].y + self.rooms[neighbor].y) / 2,
                         str(weight) + ", " + str(accessibility_weight), fontsize=10, color='b')

        # Draw nodes
        for room_id, room in self.rooms.items():
            plt.plot(room.x, room.y, 'ro')
            plt.text(room.x, room.y, str(room_id), fontsize=12)

        plt.title('Graph Visualization')
        plt.xlabel('Node')
        plt.ylabel('Weight')
        plt.grid(True)
        plt.show()








if __name__ == "__main__":
    mapper = RoomMapper()

    mapper.add_room("Lobby", 0, 0)
    mapper.add_room("Cafe", 1, 1)
    mapper.add_room("Library", -1, 1)
    mapper.add_room("Office", 0, 2)

    mapper.add_connection("Lobby", "Cafe", 3, 1)  # Stairs
    mapper.add_connection("Lobby", "Library", 3, 0)  # Accessible
    mapper.add_connection("Cafe", "Library", 1, 0)
    mapper.add_connection("Cafe", "Office", 2, 0)
    mapper.add_connection("Library", "Office", 4, 0)

    mapper.save('../../../static/map/map.txt')

    new_mapper = RoomMapper.from_file('../../../static/map/map.txt')

    # Find a path
    distance, path = new_mapper.find_path("Lobby", "Office", max_accessibility=0)
    print("Accessible path from Lobby to Office: {0}".format(" -> ".join(str(room) for room in path)))
    print("Distance: {0}".format(distance))

    # Visualize the map
    new_mapper.draw()