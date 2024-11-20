from node import Node
import math


class Room(Node):
    def __init__(self, value, x=0, y=0):
        super(Room, self).__init__(value)
        self.value = value
        self.x = x
        self.y = y

    def distance(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def __str__(self):
        return str(self.value)
