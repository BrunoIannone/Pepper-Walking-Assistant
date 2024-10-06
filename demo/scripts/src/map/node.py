class Node(object):

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.value == other.value
        elif isinstance(other, str):
            return self.value == other
        raise ValueError("Unable to convert from " + str(type(other)) + " to " + str(type(self)))

    def __hash__(self):
        return hash(self.value)

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        return self.value < other.value