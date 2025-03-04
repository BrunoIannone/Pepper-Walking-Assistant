import matplotlib.pyplot as plt
import heapq

from node import Node


class Graph(object):

    def __init__(self, directed=False):
        self.adjacency_list = {}
        self.directed = directed

    def add(self, node1, node2, weight=1, accessibility_weight=1):
        # If one of the nodes is not in the adjacency list, add it
        if node1 not in self.adjacency_list:
            self.adjacency_list[node1] = []
        if node2 not in self.adjacency_list:
            self.adjacency_list[node2] = []

        self.adjacency_list[node1].append((node2, weight, accessibility_weight))
        if not self.directed:
            self.adjacency_list[node2].append((node1, weight, accessibility_weight))

    def add_node(self, node):
        if node not in self.adjacency_list:
            self.adjacency_list[node] = []

    def add_edge(self, node1, node2, weight=1, accessibility_weight=1):
        if node1 not in self.adjacency_list:
            self.add_node(node1)
        if node2 not in self.adjacency_list:
            self.add_node(node2)

        self.adjacency_list[node1].append((node2, weight, accessibility_weight))
        if not self.directed:
            self.adjacency_list[node2].append((node1, weight, accessibility_weight))

    def get_nodes(self):
        return list(self.adjacency_list.keys())

    def load(self, path):
        with open(path, 'r') as file:
            for line in file:
                node1, node2, weight, accessibility_weight = line.split()  # Each line has node1, node2, weight, and accessibility_weight separated by tab
                self.add(node1, node2, int(weight), int(accessibility_weight))

    @classmethod
    def static_load(cls, path):
        graph = Graph()
        graph.load(path)
        return graph

    def save(self, path):
        with open(path, 'w') as file:
            for node, neighbors in self.adjacency_list.items():
                for neighbor, weight, accessibility_weight in neighbors:
                    file.write(
                        str(node) + " " + str(neighbor) + " " + str(weight) + " " + str(accessibility_weight) + "\n")

    def shortest_path(self, start, end, accessibility_level):
        return self._astar_shortest_path(start, end, accessibility_level)

    def _astar_shortest_path(self, start, end, accessibility_level):
        priority_queue = [(0, start)]  # (f, node)
        distances = {node: float('inf') for node in self.adjacency_list}
        distances[start] = 0
        parents = {}

        while priority_queue:
            _, current_node = heapq.heappop(priority_queue)

            if current_node == end:
                return distances[end], self._reconstruct_path(parents, start, end)

            for neighbor, weight, accessibility_weight in self.adjacency_list[current_node]:
                if accessibility_weight < accessibility_level:
                    tentative_distance = distances[current_node] + weight
                    if tentative_distance < distances[neighbor]:
                        distances[neighbor] = tentative_distance
                        parents[neighbor] = current_node
                        heuristic = self._heuristic(neighbor, end)
                        f_score = tentative_distance + heuristic
                        heapq.heappush(priority_queue, (f_score, neighbor))

        return float('inf'), []  # No path found

    def _heuristic(self, node, goal):
        return 0

    def _reconstruct_path(self, parents, start, end):
        path = [end]
        while path[-1] != start:
            path.append(parents[path[-1]])
        path.reverse()
        return path


if __name__ == '__main__':
    a = Node('A')
    b = Node('B')
    c = Node('C')
    d = Node('D')

    # Example usage:
    # Create a graph
    graph = Graph()
    graph.add(a, b, 3, 1)  # edge with stairs (accessibility_weight=1)
    graph.add(a, c, 3, 0)  # accessible edge (accessibility_weight=0)
    graph.add(b, c, 1, 0)
    graph.add(b, d, 2, 0)
    graph.add(c, d, 4, 0)

    # Save graph to a file
    graph.save('../../../static/map/graph.txt')

    # Find the shortest path between two nodes considering accessibility level
    start = a
    goal = d
    accessibility_level = 1  # Maximum acceptable accessibility weight
    path = graph.shortest_path(start, goal, accessibility_level)
    print("Shortest distance between " + str(start) + " and " + str(goal) + ": " + str(path[0]))
    print("Shortest path between " + str(start) + " and " + str(goal) + ": " + str(path[1]))
