import time
import cv2
import numpy as np
from jetbot import Camera

PIXEL_DIFF_PIXEL_THRESHOLD = 10.0
FRACTION_CLOSE_THRESHOLD = 0.85
MIN_FRAC_FOR_DISTANCE = 0.05
K_FRAC = 6.0

ROI_Y_START_FRAC = 0.60
ROI_Y_END_FRAC = 0.85
ROI_X_TOP_START_FRAC = 0.40
ROI_X_TOP_END_FRAC = 0.60
ROI_X_BOTTOM_START_FRAC = 0.25
ROI_X_BOTTOM_END_FRAC = 0.75

def create_trapezoid_mask(width, height):
    """Return a white-on-black mask for trapezoid ROI."""
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
    ], dtype=np.int32)

    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.fillPoly(mask, [pts], 255)
    return mask

class VisionSystem:
    def __init__(self, width=224, height=224):
        self.camera = Camera.instance(width=width, height=height)
        self.width = width
        self.height = height

        self.mask = create_trapezoid_mask(width, height)
        self.roi_pixel_count = np.count_nonzero(self.mask)

        self.bg_gray = None

    def calibrate(self, frames=25):
        print("--- Vision Calibration Started ---")
        print("Ensure NOTHING is inside the trapezoid ROI...")
        time.sleep(2)

        collected = []

        for _ in range(frames):
            frame = self.camera.value
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(np.float32)
            masked = cv2.bitwise_and(gray, gray, mask=self.mask)
            collected.append(masked)
            time.sleep(0.05)

        self.bg_gray = np.mean(collected, axis=0)
        print("Calibration complete.")

    def detect_close_obstacle(self):
        """Returns: obstacle_close (bool), frac, distance_cm or None, frame"""
        if self.bg_gray is None:
            raise RuntimeError("VisionSystem must be calibrated before use.")

        frame = self.camera.value
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(np.float32)

        masked_gray = cv2.bitwise_and(gray, gray, mask=self.mask)

        # Difference to background
        diff = np.abs(masked_gray - self.bg_gray)
        diff_masked = cv2.bitwise_and(diff, diff, mask=self.mask)

        # Binary mask of "changed" pixels
        changed = diff_masked > PIXEL_DIFF_PIXEL_THRESHOLD

        frac = float(np.sum(changed)) / self.roi_pixel_count
        obstacle_close = frac > FRACTION_CLOSE_THRESHOLD

        distance_cm = None
        if frac > MIN_FRAC_FOR_DISTANCE:
            distance_cm = K_FRAC / frac

        return obstacle_close, frac, distance_cm, frame

    def stop(self):
        """Safely stop camera."""
        self.camera.stop()
