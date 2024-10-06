class RoomMapper:
    def __init__(self):
        self.rooms = {}

    def add_room(self, name, x, y):
        self.rooms[name] = (x, y)

    def __getitem__(self, item):
        return self.rooms[item]

    def get_room(self, name):
        return self.rooms.get(name)        

    def save(self, filename):
        with open(filename, 'w') as file:
            for name, (x, y) in self.rooms.items():
                file.write(str(name) + " " + str(x) + " " + str(y) + "\n")

    def load(self, filename):
        self.rooms = {}
        with open(filename, 'r') as file:
            for line in file:
                parts = line.split()
                if len(parts) == 3:
                    name, x, y = parts
                    self.add_room(name, float(x), float(y))

    @classmethod
    def static_load(cls, filename):
        
        rm = RoomMapper()
        rm.load(filename)
        return rm
    
    def __str__(self):
        return "\n".join(str(name) + ": ( " + str(x) + ", " + str(y) + ")" for name, (x, y) in self.rooms.items())

    def __repr__(self):
        return "\n".join(str(name) + ": ( " + str(x) + ", " + str(y) + ")" for name, (x, y) in self.rooms.items())
