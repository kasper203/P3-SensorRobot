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
            for succ in self.getSuccessors(node):
                if succ.gvalue < float("inf") and succ.is_available: # only consider available successors, shouldnt be neccesary
                    node.rhs = min(node.rhs, self.cost(succ, node) + succ.gvalue)

        self.removeFromQueue(node)

        if node.gvalue != node.rhs:
            self.CalcKey(node) # tied to the node so the updated keys are in U
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
                self.updateParent(u)
                for succ in self.getSuccessors(u):
                    self.updateVertex(succ)

            else:
                u.gvalue = float('inf')
                self.updateVertex(u)
                for succ in self.getSuccessors(u):
                    self.updateVertex(succ)

    # -------------------- Successors / Predecessors --------------------
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

    def updateParent(self, node: Cell):
        successors = self.getSuccessors(node)
        valid = [s for s in successors if s.gvalue < float("inf") and s.is_available]
        if valid:
            node.parent = min(valid, key=lambda s: self.cost(node, s) + s.gvalue)
        else:
            node.parent = None

    def reconstruct_path(self, start_node: Cell, goal_node: Cell):
        path = []
        current = start_node

        while current != goal_node:
            path.append((current.x, current.y))
            # pick the available successor with minimum cost+g
            successors = [s for s in self.getSuccessors(current) 
                        if s.is_available and s.gvalue < float('inf')]
            if not successors:
                return None

            current = min(successors, key=lambda s: self.cost(current, s) + s.gvalue)

        path.append((goal_node.x, goal_node.y))
        return path


    # -------------------- Path to Command with Robot Heading --------------------
    def pathToCommand(self, path: List[Tuple[int,int]], robotHeading: int) -> List[Tuple[int,float]]:
        moves = []
        heading = robotHeading
        for (x1,y1),(x2,y2) in zip(path,path[1:]):
            dx = x2 - x1
            dy = y2 - y1
            #print(f"From ({x1},{y1}) to ({x2},{y2}): delta ({dx},{dy})")
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

            # If a rotation is required, do rotation (distance 0) first then movement.
            if abs(angle_relative) > 1e-9:
                moves.append((angle_relative, 0.0))
                moves.append((0, dist))
            else:
                moves.append((0, dist))

            # Update heading to the absolute direction after the step
            heading = angle_abs

        return moves

    # -------------------- Dynamic obstacle --------------------
    def addWall(self, wall) -> List[Cell]:
        changed_nodes = set()
        def mark(x,y):
            cell = self.nodes[y][x]
            if cell.is_available: # make sure we reset the values at cells marked as walls
                cell.is_available = False
                cell.parent = None
                cell.gvalue = float('inf')
                cell.rhs = float('inf')
                changed_nodes.add(cell)
        mark(wall.x1, wall.y1)
        #print(f"Marking wall at ({wall.x1},{wall.y1}) is _available={self.nodes[wall.y1][wall.x1].is_available}")
        # if wall.x1 == wall.x2:
        #     for y in range(min(wall.y1, wall.y2), max(wall.y1, wall.y2)+1):
        #         mark(wall.x1, y)
        # elif wall.y1 == wall.y2:
        #     for x in range(min(wall.x1, wall.x2), max(wall.x1, wall.x2)+1):
        #         mark(x, wall.y1)
        # else:
        #     # Bresenham line for diagonal walls
        #     x1, y1, x2, y2 = wall.x1, wall.y1, wall.x2, wall.y2
        #     dx = abs(x2-x1); dy=abs(y2-y1)
        #     sx = 1 if x2>x1 else -1
        #     sy = 1 if y2>y1 else -1
        #     err = dx-dy
        #     x, y = x1, y1
        #     while True:
        #         mark(x,y)
        #         if x==x2 and y==y2: break
        #         e2 = 2*err
        #         if e2 > -dy: err-=dy; x+=sx
        #         if e2 < dx: err+=dx; y+=sy

        for succ in self.getSuccessors(self.nodes[wall.y1][wall.x1]): # make sure we have all the neighboring nodes aswell
            changed_nodes.add(succ)
    
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
        if not path:
            return []
        
        cmds = self.grid.pathToCommand(path, self.robot_heading)
        return cmds

    # ------------------------------------------------
    # Only call this when robot physically moves
    # ------------------------------------------------
    def update_robot_position(self, pos, heading):
        x, y = pos
        self.last_node = self.current_node
        self.current_node = self.grid.nodes[y][x]
        self.grid.startnode = self.current_node
        self.robot_heading = heading

    # ------------------------------------------------
    # Robot detects obstacle → replan
    # ------------------------------------------------
    def handle_obstacle(self, wall: Wall):
        changed_nodes = self.grid.addWall(wall)  

        # Update km
        self.grid.km += self.grid.calcHeuristic(self.last_node, self.current_node)
        self.last_node = self.current_node

        for v in changed_nodes:
            #print("Vx", v.x, "Vy", v.y, "g", v.gvalue, "rhs", v.rhs, "is_available", v.is_available)
            self.grid.updateVertex(v)

        # Compute shortest path
        self.grid.computeShortestPath()

        # Generate new commands
        path = self.grid.reconstruct_path(self.current_node, self.goal_node)
        if not path:
            return []

        cmds = self.grid.pathToCommand(path, self.robot_heading)
        return cmds
