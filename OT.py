import time
import cv2
import numpy as np
from jetbot import Robot, Camera

robot = Robot()
camera = Camera.instance(width=224, height=224)

# --------- ROI ---------
def get_roi(image):
    h, w, _ = image.shape
    y1 = int(h * 0.65)     
    y2 = int(h * 0.92)
    x1 = int(w * 0.45)     
    x2 = int(w * 0.55)
    return image[y1:y2, x1:x2]

print("Kalibrerer gulv... sørg for at der IKKE står noget foran robotten.")
time.sleep(2)

# ---------- KALIBRERING ----------
low_frames = []

for _ in range(25):
    frame = camera.value
    roi = get_roi(frame)
    gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY).astype(np.float32)
    low_frames.append(gray)
    time.sleep(0.05)

bg_gray = np.mean(low_frames, axis=0)

print("Kalibrering færdig.")

# ---------- PARAMETRE ----------
PIXEL_DIFF_PIXEL_THRESHOLD = 10.0
FRACTION_CLOSE_THRESHOLD   = 0.40     # drej kun hvis fylder ~40%
OBSTACLE_FRAMES_REQUIRED   = 3
COOLDOWN_STEPS = 12

K_FRAC = 6.0   # lille ROI -> lille K. 
MIN_FRAC_FOR_DISTANCE = 0.05

def detect_close_obstacle(frame):
    roi = get_roi(frame)
    gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY).astype(np.float32)

    diff_pixels = np.abs(gray - bg_gray)
    mask = diff_pixels > PIXEL_DIFF_PIXEL_THRESHOLD

    frac = float(np.mean(mask))

    obstacle_close = frac > FRACTION_CLOSE_THRESHOLD

    distance_cm = None
    if frac > MIN_FRAC_FOR_DISTANCE:
        distance_cm = K_FRAC / frac

    return obstacle_close, frac, distance_cm


print("Starter: drej KUN når objektet er tæt på (frac > threshold).")

state = "DRIVE"
obstacle_counter = 0
cooldown_left = 0
