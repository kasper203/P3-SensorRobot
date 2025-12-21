import heapq
from typing import List, Tuple
from math import sqrt
import itertools


class Cell:
    def __init__(self):
        self.gvalue = float('inf')
        self.rhs = float('inf')
        self.is_startnode = False
        self.is_endnode = False
        self.is_available = True
        self.parent = None
        self.x = None
        self.y = None

    def __repr__(self):
        return f"Cell({self.x},{self.y},g={self.gvalue},rhs={self.rhs})"

class Wall:
    def __init__(self, x1, y1, x2, y2):
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2

class Grid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.nodes: List[List[Cell]] = []
        self.U: List[Tuple[Tuple[float,float], int, Cell]] = [] 
        self.km = 0
        self.startnode: Cell = None
        self.endnode: Cell = None

        self.counter = itertools.count()  


    def createAllNodes(self):
        self.nodes = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                c = Cell()
                c.x = x
                c.y = y
                row.append(c)
            self.nodes.append(row)
        return self.nodes

    def setStartNode(self, x, y):
        self.startnode = self.nodes[y][x]
        self.startnode.is_startnode = True
        return self.startnode

    def setEndNode(self, x, y):
        self.endnode = self.nodes[y][x]
        self.endnode.is_endnode = True
        return self.endnode

    def CalcKey(self, node: Cell) -> Tuple[float, float]:
        h = self.calcHeuristic(node, self.startnode)
        return (min(node.gvalue, node.rhs) + h + self.km, min(node.gvalue, node.rhs))

    def updateVertex(self, node: Cell):
        if node != self.endnode:
            node.rhs = float('inf')
            for succ in self.getSuccessors(node):
                if succ.is_available:
                    node.rhs = min(node.rhs, self.cost(succ, node) + succ.gvalue)

        self.removeFromQueue(node)

        if node.gvalue != node.rhs:
            heapq.heappush(self.U, (self.CalcKey(node), next(self.counter), node))



    def computeShortestPath(self):
        while self.U:
            start_key = self.CalcKey(self.startnode)
            top_key, _, _,= self.U[0]  

            if not (top_key < start_key or self.startnode.rhs != self.startnode.gvalue):
                break
            
            k_old, _, u = heapq.heappop(self.U)
            k_new = self.CalcKey(u)

            if k_old < k_new:
                heapq.heappush(self.U, (k_new, next(self.counter), u))

            elif u.gvalue > u.rhs:
                u.gvalue = u.rhs
                self.updateParent(u)
                for succ in self.getSuccessors(u):
                    self.updateVertex(succ)
            else:
                u.gvalue = float('inf')
                self.updateVertex(u)
                for succ in self.getSuccessors(u):
                    self.updateVertex(succ)

    def getSuccessors(self, node: Cell) -> List[Cell]:
        successors = []
        directions = [(-1,0), (-1,1), (1,0), (1,1), (0,1), (1,-1), (0,-1), (-1,-1)]
        for dx, dy in directions:
            nx, ny = node.x + dx, node.y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                neighbor = self.nodes[ny][nx]
                successors.append(neighbor)
        return successors

    def getPredecessors(self, node: Cell) -> List[Cell]:
        return self.getSuccessors(node)

    def calcHeuristic(self, node1: Cell, node2: Cell) -> float:
        dx = abs(node1.x - node2.x)
        dy = abs(node1.y - node2.y)
        return dx + dy + (sqrt(2) - 2) * min(dx, dy)

    def cost(self, node1: Cell, node2: Cell) -> float:
        if not node1.is_available or not node2.is_available:
            return float('inf')
        return sqrt(2) if (node1.x != node2.x and node1.y != node2.y) else 1

    def removeFromQueue(self, node: Cell) -> bool:
        for i, (_, _, cell) in enumerate(self.U):
            if cell == node:
                self.U.pop(i)
                heapq.heapify(self.U)
                return True
        return False

    def updateParent(self, node: Cell):
        successors = self.getSuccessors(node)
        valid = [s for s in successors if s.gvalue < float("inf") and s.is_available]
        if valid:
            node.parent = min(valid, key=lambda s: self.cost(node, s) + s.gvalue)
        else:
            node.parent = None


    def reconstruct_path(self, start_node: Cell, goal_node: Cell) -> List[Tuple[int, int]]:
        path = [(start_node.x, start_node.y)] 
        current = start_node
        visited = {start_node}

        while current != goal_node and current.parent is not None:

            if current.parent in visited:
                print("Path reconstruction failed: Cycle detected.")
                return None

            current = current.parent
            path.append((current.x, current.y))
            visited.add(current)

        if current == goal_node:
            return path
        else:
            return None
        

    def pathToCommand(self, path: List[Tuple[int,int]], robotHeading: int) -> List[Tuple[int,float]]:
        if path is None or len(path) < 2:
            return []
        moves = []
        heading = robotHeading
        for (x1,y1),(x2,y2) in zip(path,path[1:]):
            dx = x2 - x1
            dy = y2 - y1
            print(f"From ({x1},{y1}) to ({x2},{y2}): delta ({dx},{dy})")
            if (dx,dy) == (0,0):
                continue
            direction_map = {
                (1,0): 90, (1,1): 45, (0,1): 0, (-1,1):-45,
                (-1,0):-90, (-1,-1):-135, (0,-1):180, (1,-1):135
            }
            angle_abs = direction_map[(dx,dy)]
            angle_relative = angle_abs - heading
            if angle_relative > 180:
                angle_relative -= 360
            elif angle_relative < -180:
                angle_relative += 360
            dist = sqrt(dx*dx + dy*dy)

            if abs(angle_relative) > 1e-9:
                moves.append((angle_relative, 0.0))
                moves.append((0, dist))
            else:
                moves.append((0, dist))

            heading = angle_abs

        return moves   

    def addWall(self, wall):
        changed_nodes = set()
        cell = self.nodes[wall.y1][wall.x1]
        if cell.is_available:
            cell.is_available = False
            cell.gvalue = float('inf')
            cell.rhs = float('inf')
            cell.parent = None
            changed_nodes.add(cell)

        return list(changed_nodes)


class DStarLiteController:
    def __init__(self, width, height, start, goal):
        self.grid = Grid(width, height)
        self.grid.createAllNodes()

        self.current_node = self.grid.setStartNode(*start)
        self.grid.setEndNode(*goal)
        self.goal_node = self.grid.endnode

        self.last_node = self.current_node
        self.robot_heading = 0

        self.grid.U = []
        self.grid.km = 0

        for row in self.grid.nodes:
            for node in row:
                node.rhs = float('inf')
                node.gvalue = float('inf')
                node.parent = None

        self.goal_node.rhs = 0
        heapq.heappush(self.grid.U, (self.grid.CalcKey(self.goal_node), next(self.grid.counter), self.goal_node))

        self.grid.computeShortestPath()

    def get_initial_commands(self):
        print("Getting initial commands")
        path = self.grid.reconstruct_path(self.current_node, self.goal_node)
        if not path:
            return []
        return self.grid.pathToCommand(path, self.robot_heading)

    def update_robot_position(self, pos, heading):
        x, y = pos
        self.last_node = self.current_node
        self.current_node = self.grid.nodes[y][x]
        self.grid.startnode = self.current_node
        self.robot_heading = heading

    def handle_obstacle(self, wall: Wall):
        changed_nodes = self.grid.addWall(wall)
        self.grid.km += self.grid.calcHeuristic(self.last_node, self.current_node)
        self.last_node = self.current_node

        for v in changed_nodes:
            self.grid.updateVertex(v)
            for succ in self.grid.getPredecessors(v):
                self.grid.updateVertex(succ)
                if succ.parent == v:
                    self.grid.updateParent(succ)

        self.grid.computeShortestPath()
        path = self.grid.reconstruct_path(self.current_node, self.goal_node)
        cmds = self.grid.pathToCommand(path, self.robot_heading)
        return cmds
