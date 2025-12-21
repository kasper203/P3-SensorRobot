# NOD.py
import time
import threading
import cv2
import numpy as np
from jetbot import Camera

class ObstacleDetector:
    def __init__(self, width=224, height=224):
        self.camera = Camera.instance(width=width, height=height)

        # ROI-funktion
        def get_roi(image):
            h, w, _ = image.shape
            y1 = int(h * 0.65)
            y2 = int(h * 0.92)
            x1 = int(w * 0.45)
            x2 = int(w * 0.55)
            return image[y1:y2, x1:x2]

        self.get_roi = get_roi

        print("Kalibrerer gulv... fjern objekter foran robotten.")
        time.sleep(2)

        low_frames = []
        for _ in range(25):
            frame = self.camera.value
            roi = self.get_roi(frame)
            gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY).astype(np.float32)
            low_frames.append(gray)
            time.sleep(0.05)

        self.bg_gray = np.mean(low_frames, axis=0)
        print("Kalibrering færdig.")

        # parametre
        self.PIXEL_DIFF_PIXEL_THRESHOLD = 10.0
        self.FRACTION_CLOSE_THRESHOLD   = 0.40
        self.MIN_FRAC_FOR_DISTANCE      = 0.05
        self.K_FRAC                     = 6.0

        # shared state (beskyttet af lock)
        self.lock = threading.Lock()
        self._obstacle_close = False
        self._frac = 0.0
        self._distance_cm = None
        self._frame = None

        # thread styring
        self._running = False
        self._thread = None

    def _detect_once(self):
        frame = self.camera.value
        roi = self.get_roi(frame)
        gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY).astype(np.float32)

        diff_pixels = np.abs(gray - self.bg_gray)
        mask = diff_pixels > self.PIXEL_DIFF_PIXEL_THRESHOLD

        frac = float(np.mean(mask))
        obstacle_close = frac > self.FRACTION_CLOSE_THRESHOLD

        distance_cm = None
        if frac > self.MIN_FRAC_FOR_DISTANCE:
            distance_cm = self.K_FRAC / frac

        with self.lock:
            self._obstacle_close = obstacle_close
            self._frac = frac
            self._distance_cm = distance_cm
            self._frame = frame

    def _loop(self):
        while self._running:
            self._detect_once()
            time.sleep(0.05)   # ~20 Hz

    def start(self):
        """Start baggrundstråd"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def get_state(self):
        """Læs seneste resultat: obstacle_close, frac, distance_cm, frame"""
        with self.lock:
            return (self._obstacle_close,
                    self._frac,
                    self._distance_cm,
                    self._frame)

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join()
        self.camera.stop()
