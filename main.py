## main_dstar_vision.ipynb

# --- Celle 1: Opsætning og Imports ---
%load_ext autoreload
%autoreload 2

import time
import socket
import time
import cv2 # Nødvendigt for billedbehandling
import numpy as np # Nødvendigt for array-operationer
from jetbot import Robot, Camera 
import traitlets # Nødvendigt for at stoppe kamera sikkert

# Importér dit modul med robotbevægelser (skal ligge i samme mappe)
import OurRobot 

# Importer DStarLite komponenter 
from dstarlite import DStarLiteController, Wall 

ARDUINO_IP = "172.20.10.14"   # Arduino WiFi IP address
ARDUINO_PORT = 8888            # Must match Arduino localUdpPort

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# -------------------- Function to send coordinates --------------------
def send_coordinates(x, y):
    message = f"{x},{y}"
    sock.sendto(message.encode(), (ARDUINO_IP, ARDUINO_PORT))
    print(f"Sent to Arduino: {message}")

# --- 2. KONSTANTER & THRESHOLDS ---
GRID_W, GRID_H = 20, 20
start = (0, 0)
goal = (5, 5)

# Vision Konstanter (Juster disse efter test)
PIXEL_DIFF_PIXEL_THRESHOLD = 10.0   # Tærskel for forskel i lysstyrke (Støjfilter)
FRACTION_CLOSE_THRESHOLD = 0.85     # Frac over dette = forhindring opdaget
REPLAN_FRAC_THRESHOLD = 0.99       # Frac over dette = robotten er meget tæt på og skal replanne
MIN_FRAC_FOR_DISTANCE = 0.05
K_FRAC = 6.0                        # Kalibreringskonstant for afstand

# Trapezoid ROI Konstanter (Juster disse)
ROI_Y_START_FRAC = 0.60
ROI_Y_END_FRAC = 0.85
ROI_X_TOP_START_FRAC = 0.40  
ROI_X_TOP_END_FRAC = 0.60   
ROI_X_BOTTOM_START_FRAC = 0.25 
ROI_X_BOTTOM_END_FRAC = 0.75   

# --- 3. Init hardware ---
robot = OurRobot.robot
# Initialiser kamera én gang
camera = Camera.instance(width=224, height=224) 


# --- 4. TRAPEZOID MASK FUNKTION ---
def create_trapezoid_mask(width, height):
    """ Skaber en sort/hvid maske, der kun er hvid (255) inden for trapezoiden. """
    
    y1 = int(height * ROI_Y_START_FRAC)
    y2 = int(height * ROI_Y_END_FRAC)
    x1_top = int(width * ROI_X_TOP_START_FRAC)
    x2_top = int(width * ROI_X_TOP_END_FRAC)
    x1_bottom = int(width * ROI_X_BOTTOM_START_FRAC)
    x2_bottom = int(width * ROI_X_BOTTOM_END_FRAC)

    pts = np.array([
        [x1_top, y1],
        [x2_top, y1],
        [x2_bottom, y2],
        [x1_bottom, y2]
    ], np.int32)
    
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.fillPoly(mask, [pts], 255) # Fyld trapezoiden med hvid
    
    return mask

# Beregn masken og antallet af pixels i ROI (Køres kun én gang)
WIDTH, HEIGHT = camera.width, camera.height 
FULL_IMAGE_TRAPEZOID_MASK = create_trapezoid_mask(WIDTH, HEIGHT)
ROI_PIXEL_COUNT = np.count_nonzero(FULL_IMAGE_TRAPEZOID_MASK) # Antal gyldige pixels


# --- 5. KALIBRERING (Beregner bg_gray) ---
print("--- Kalibrering Starter ---")
print("Sørg for, at der IKKE står noget i den grønne trapezoid ROI.")
time.sleep(2)

low_frames = []
for _ in range(25):
    frame = camera.value
    
    # Konverter HELE billedet til gråtoner
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(np.float32)

    # ANVEND MASKEN: Sæt alle pixels UDEN for trapezoiden til nul
    # Dette sikrer, at kun data fra ROI bruges til kalibrering
    masked_gray = cv2.bitwise_and(gray, gray, mask=FULL_IMAGE_TRAPEZOID_MASK)

    low_frames.append(masked_gray) 
    time.sleep(0.05)

# Beregn gennemsnit af det maskerede gulv
bg_gray = np.mean(low_frames, axis=0) 
print("Kalibrering færdig. bg_gray er beregnet.")


# --- 6. DETEKTIONSFUNKTION ---
def detect_close_obstacle():
    """Tager nyt billede, analyserer og returnerer synkront resultatet."""
    frame = camera.value
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(np.float32)

    # ANVEND MASKEN på det aktuelle billede
    masked_gray = cv2.bitwise_and(gray, gray, mask=FULL_IMAGE_TRAPEZOID_MASK)

    # 1. Forskellen (Subtraktion)
    diff_pixels = np.abs(masked_gray - bg_gray)
    
    # NULSTIL UDENFOR TRAPEZOIDEN I DIFFERENCEN (Sikrer ren ROI)
    diff_pixels_masked = cv2.bitwise_and(diff_pixels, diff_pixels, mask=FULL_IMAGE_TRAPEZOID_MASK)

    # 2. Masken: True, hvis forskellen er stor nok
    mask = diff_pixels_masked > PIXEL_DIFF_PIXEL_THRESHOLD
    
    # 3. Frac: Andelen af pixels, der er en forhindring i forhold til ROI's størrelse
    # np.sum(mask) giver antallet af "True" pixels
    frac = float(np.sum(mask)) / ROI_PIXEL_COUNT 

    obstacle_close = frac > FRACTION_CLOSE_THRESHOLD

    distance_cm = None
    if frac > MIN_FRAC_FOR_DISTANCE:
        distance_cm = K_FRAC / frac

    return obstacle_close, frac, distance_cm, frame


# --- 7. BEVÆGELSES- OG GRID-FUNKTIONER ---
def cell_step_for_heading(heading_deg):
    """Returner (dx, dy) for 8 retninger baseret på heading"""
    heading_deg = heading_deg % 360
    if heading_deg > 180:
        heading_deg -= 360
    
    # (Simplified for the common D* Lite grid)
    if heading_deg == 0: return (0, 1)
    elif heading_deg == 45: return (1, 1)
    elif heading_deg == 90: return (1, 0)
    elif heading_deg == 135: return (1, -1)
    elif heading_deg == 180 or heading_deg == -180: return (0, -1)
    elif heading_deg == -135: return (-1, -1)
    elif heading_deg == -90: return (-1, 0)
    elif heading_deg == -45: return (-1, 1)
    else: return (0, 0)



def reverseCommand(commands):
    reversed_commands = []
    for angle, dist in reversed(commands):
        if dist != 0:
            reversed_commands.append((0, dist))
        if angle != 0:
            reversed_commands.append((-angle, 0))
    return reversed_commands

    
def cell_in_front(grid_x, grid_y, robot_heading):
    """Beregner grid-cellen umiddelbart foran robotten."""
    dx, dy = cell_step_for_heading(robot_heading)
    return grid_x + dx, grid_y + dy

back_commands = []

def execute_command(angle_deg, dist_cells):
    global robot_heading, grid_x, grid_y
    
    global back_commands
    if not returning_home:
        curr_command = (angle_deg, dist_cells)
        back_commands.append((angle_deg, dist_cells))
    
    # Drej
    if angle_deg < 0:
        OurRobot.turn_left(OurRobot.robot, angle_deg)
    elif angle_deg > 0:
        OurRobot.turn_right(OurRobot.robot, angle_deg)

    # Kør frem
    if dist_cells == 1:
        # Brug en justeret tid for fremkørsel
        duration = dist_cells * 2.2 # Juster denne faktor 
        OurRobot.drive_forward(OurRobot.robot, duration)
    else:
        duration = dist_cells * 2.38 # Juster denne faktor 
        OurRobot.drive_forward(OurRobot.robot, duration)
        
            
    # Opdater heading
    robot_heading += angle_deg
    robot_heading = robot_heading % 360
    if robot_heading > 180: robot_heading -= 360
    if robot_heading < -180: robot_heading += 360
    
    # Opdater grid-position
    if dist_cells > 0:
        dx, dy = cell_step_for_heading(robot_heading)
        grid_x += dx
        grid_y += dy
        
        send_coordinates(grid_x, grid_y)
        
    controller.update_robot_position((grid_x, grid_y), robot_heading)    
    print(f"Ny grid-position: ({grid_x}, {grid_y}), heading={robot_heading}")
    
    

# --- 8. INIT D* Lite & Hovedløkke ---
controller = DStarLiteController(width=GRID_W, height=GRID_H, start=start, goal=goal)

grid_x, grid_y = start
robot_heading = 0 # initial heading

command_queue = controller.get_initial_commands()
command_index = 0

print("D* Lite initialiseret. Starter rute fra:", start, "til:", goal)

returning_home = False   # state flag

try:
    while True:
        

        # ----------------------------
        # Goal reached → return to base
        # ----------------------------
        if (grid_x, grid_y) == goal and not returning_home:
            print("Mål nået!")
            print(back_commands)
            command_queue = reverseCommand(back_commands)
            print(command_queue)
            command_index = 0
            OurRobot.turn_right(OurRobot.robot, 180)
            robot_heading += 180
            returning_home = True
            print("Returning to base!")

        # ----------------------------
        # Execute next command if any
        # ----------------------------
        if command_queue:
            angle, dist = command_queue.pop(0)

            print(f"\nCOMMAND: Drej {angle}°, Kør {dist} celle(r)")
            execute_command(angle, dist)

            # ----------------------------
            # Vision check AFTER movement
            # ----------------------------
            obstacle_close, frac, dist_cm, frame = detect_close_obstacle()

            if dist_cm is not None:
                print(f"Vision: close={obstacle_close}, frac={frac:.4f}")
            else:
                print(f"Vision: close={obstacle_close}, frac={frac:.4f}")

            # ----------------------------
            # Obstacle → D* replanning
            # ----------------------------
            if frac > REPLAN_FRAC_THRESHOLD:
                print(">>> TÆT PÅ FORHINDRING! Starter D* replanlægning. <<<")

                fx, fy = cell_in_front(grid_x, grid_y, robot_heading)
                wall = Wall(fx, fy, fx, fy)

                new_commands = controller.handle_obstacle(wall)

                if new_commands:
                    command_queue = new_commands
                    command_index = 0
                else:
                    print("D* fandt ingen rute – venter.")

        # ----------------------------
        # No commands available
        # ----------------------------
        else:
            if returning_home:
                print("Tilbage ved start – færdig.")
                break
            else:
                print("Ingen flere kommandoer – venter.")
                time.sleep(0.5)

        time.sleep(0.5)

except KeyboardInterrupt:
    pass
finally:
    robot.stop()
    camera.stop() 
    print("Robot og Kamera stoppet.")