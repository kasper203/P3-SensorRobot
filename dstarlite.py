import heapq
from typing import List, Tuple
from math import sqrt

class Cell:
    def __init__(self):
        self.gvalue = float('inf')
        self.rhs = float('inf')
        self.is_startnode = False
        self.is_endnode = False
        self.heuristic = float('inf')
        self.key1 = float('inf')
        self.key2 = float('inf')
        self.is_available = True
        self.parent = None
        self.x = None
        self.y = None

    def __lt__(self, other):
        if self.key1 != other.key1:
            return self.key1 < other.key1
        return self.key2 < other.key2

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
        self.U: List[Cell] = []
        self.km = 0
        self.startnode: Cell = None
        self.endnode: Cell = None

    # -------------------- Basic grid setup --------------------
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

    # -------------------- D* Lite core --------------------
    def CalcKey(self, node: Cell) -> Tuple[float, float]:
        node.heuristic = self.calcHeuristic(node, self.startnode)
        node.key1 = min(node.gvalue, node.rhs) + node.heuristic + self.km
        node.key2 = min(node.gvalue, node.rhs)
        return (node.key1, node.key2)

    def updateVertex(self, node: Cell):
        if node != self.endnode:
            node.rhs = float('inf')
            for pred in self.getPredecessors(node):
                node.rhs = min(node.rhs, self.cost(pred, node) + pred.gvalue)

        self.removeFromQueue(node)

        if node.gvalue != node.rhs:
            self.CalcKey(node)
            heapq.heappush(self.U, node)

    def computeShortestPath(self):
        while self.U:
            start_key = self.CalcKey(self.startnode)
            top = self.U[0]

            if not (top.key1 < start_key[0] or self.startnode.rhs != self.startnode.gvalue):
                break

            k_old = (top.key1, top.key2)
            u = heapq.heappop(self.U)
            k_new = self.CalcKey(u)

            if k_old < k_new:
                heapq.heappush(self.U, u)
            elif u.gvalue > u.rhs:
                u.gvalue = u.rhs
                successors = self.getSuccessors(u)
                valid = [s for s in successors if s.gvalue < float("inf")]
                u.parent = min(valid, key=lambda s: self.cost(u, s) + s.gvalue) if valid else None
                for succ in successors:
                    self.updateVertex(succ)

            else:
                old_g = u.gvalue
                u.gvalue = float('inf')
                self.updateVertex(u)
                for pred in self.getPredecessors(u):
                    if abs(self.cost(pred, u) + old_g - pred.rhs) < 1e-9:
                        self.updateVertex(pred)

    # -------------------- Successors / Predecessors --------------------
    def getSuccessors(self, node: Cell) -> List[Cell]:
        successors = []
        directions = [(-1,0), (-1,1), (1,0), (1,1), (0,1), (1,-1), (0,-1), (-1,-1)]
        for dx, dy in directions:
            nx, ny = node.x + dx, node.y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                neighbor = self.nodes[ny][nx]
                if neighbor.is_available:
                    if dx != 0 and dy != 0:
                        if (self.nodes[node.y][node.x + dx].is_available and
                            self.nodes[node.y + dy][node.x].is_available):
                            successors.append(neighbor)
                    else:
                        successors.append(neighbor)
        return successors

    def getPredecessors(self, node: Cell) -> List[Cell]:
        return self.getSuccessors(node)

    # -------------------- Heuristic & Cost --------------------
    def calcHeuristic(self, node1: Cell, node2: Cell) -> float:
        dx = abs(node1.x - node2.x)
        dy = abs(node1.y - node2.y)
        return dx + dy + (sqrt(2) - 2) * min(dx, dy)

    def cost(self, node1: Cell, node2: Cell) -> float:
        if not node1.is_available or not node2.is_available:
            return float('inf')
        return sqrt(2) if (node1.x != node2.x and node1.y != node2.y) else 1

    # -------------------- Priority Queue --------------------
    def removeFromQueue(self, node: Cell) -> bool:
        for i, cell in enumerate(self.U):
            if cell == node:
                self.U.pop(i)
                heapq.heapify(self.U)
                return True
        return False

    # -------------------- Path Reconstruction --------------------
    def reconstruct_path(self, start_node: Cell, goal_node: Cell):
        if start_node.gvalue == float('inf'):
            return None

        path = []
        current = start_node

        # Follow parent pointers until we reach the goal
        while current is not None:
            path.append((current.x, current.y))
            if current == goal_node:
                break
            current = current.parent

        # If we didn’t reach the goal, path is invalid
        if current != goal_node:
            return None

        return path

    # -------------------- Path to Command with Robot Heading --------------------
    def pathToCommand(self, path: List[Tuple[int,int]], robotHeading: int) -> Tuple[List[Tuple[int,float]], int]:
        moves = []
        heading = robotHeading
        for (x1,y1),(x2,y2) in zip(path,path[1:]):
            dx = x2 - x1
            dy = y2 - y1
            if (dx,dy) == (0,0):
                continue
            direction_map = {
                (1,0): 90, (1,1): 45, (0,1): 0, (-1,1):-45,
                (-1,0):-90, (-1,-1):-135, (0,-1):180, (1,-1):135
            }
            angle_abs = direction_map[(dx,dy)]
            angle_relative = angle_abs - heading
            if angle_relative > 180: angle_relative -= 360
            elif angle_relative < -180: angle_relative += 360
            dist = sqrt(dx*dx + dy*dy)
            moves.append((angle_relative, dist))
            heading = angle_abs
        return moves, heading

    # -------------------- Dynamic obstacle --------------------
    def addWall(self, wall) -> List[Cell]:
        changed_nodes = set()
        def mark(x,y):
            cell = self.nodes[y][x]
            if cell.is_available:
                cell.is_available = False
                changed_nodes.add(cell)

        if wall.x1 == wall.x2:
            for y in range(min(wall.y1, wall.y2), max(wall.y1, wall.y2)+1):
                mark(wall.x1, y)
        elif wall.y1 == wall.y2:
            for x in range(min(wall.x1, wall.x2), max(wall.x1, wall.x2)+1):
                mark(x, wall.y1)
        else:
            # Bresenham line for diagonal walls
            x1, y1, x2, y2 = wall.x1, wall.y1, wall.x2, wall.y2
            dx = abs(x2-x1); dy=abs(y2-y1)
            sx = 1 if x2>x1 else -1
            sy = 1 if y2>y1 else -1
            err = dx-dy
            x, y = x1, y1
            while True:
                mark(x,y)
                if x==x2 and y==y2: break
                e2 = 2*err
                if e2 > -dy: err-=dy; x+=sx
                if e2 < dx: err+=dx; y+=sy
    
        return list(changed_nodes)
    

class DStarLiteController:
    def __init__(self, width, height, start, goal):
        self.grid = Grid(width, height)
        self.grid.createAllNodes()
        
        # Set start/end in the grid
        self.current_node = self.grid.setStartNode(*start)
        self.grid.setEndNode(*goal)
        self.goal_node = self.grid.endnode

        # Robot state
        self.last_node = self.current_node
        self.robot_heading = 0

        # Initialize D* Lite
        self.grid.U = []
        self.grid.km = 0

        for row in self.grid.nodes:
            for node in row:
                node.rhs = float('inf')
                node.gvalue = float('inf')
                node.parent = None

        # End node rhs = 0
        self.goal_node.rhs = 0
        self.grid.CalcKey(self.goal_node)
        heapq.heappush(self.grid.U, self.goal_node)

        # Compute initial shortest path
        self.grid.computeShortestPath()

    # ------------------------------------------------
    # Produce initial command plan
    # ------------------------------------------------
    def get_initial_commands(self):
        path = self.grid.reconstruct_path(self.current_node, self.goal_node)
        cmds, self.robot_heading = self.grid.pathToCommand(path, self.robot_heading)
        return cmds

    # ------------------------------------------------
    # Only call this when robot physically moves
    # ------------------------------------------------
    def update_robot_position(self, pos):
        x, y = pos
        self.last_node = self.current_node
        self.current_node = self.grid.nodes[y][x]
        self.grid.startnode = self.current_node

    # ------------------------------------------------
    # Robot detects obstacle → replan
    # ------------------------------------------------
    def handle_obstacle(self, wall: Wall):
        changed_nodes = self.grid.addWall(wall)  # nodes already pushed to U

        # Update km
        self.grid.km += self.grid.calcHeuristic(self.last_node, self.current_node)
        self.last_node = self.current_node

        for v in changed_nodes:
            self.grid.updateVertex(v)
            for u in self.grid.getPredecessors(v):
                self.grid.updateVertex(u)

        # Compute shortest path
        self.grid.computeShortestPath()

        # Generate new commands
        path = self.grid.reconstruct_path(self.current_node, self.goal_node)
        if not path:
            return []

        cmds, self.robot_heading = self.grid.pathToCommand(path, self.robot_heading)
        return cmds



# -------------------- Simulation --------------------
if __name__ == "__main__":
    # Initialize
    controller = DStarLiteController(width=20, height=20, start=(0,0), goal=(10,10))
    commands = controller.get_initial_commands()
    print("Initial commands:", commands)

    # Robot moves to (1,1)
    controller.update_robot_position((1,1))

    # Robot detects obstacle at (2,2)
    obstacle = Wall(2,2,2,2)
    new_commands = controller.handle_obstacle(obstacle)
    print("New commands:", new_commands)
