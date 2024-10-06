from demo.scripts.src.map.node import Node


class Room(Node):
    def __init__(self, value, x=0, y=0):
        super(Room, self).__init__(value)
        self.value = value
        self.x = x
        self.y = y