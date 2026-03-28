import threading
import time
import cv2 as cv
from jetbot import Camera, bgr8_to_jpeg
import ipywidgets.widgets as widgets
from IPython.display import display
from jetbot import Robot

from Detector import YoloDetector


class NotebookYoloApp:
    def __init__(self, yolo_cfg='yolov3.cfg', yolo_weights='yolov3.weights', coco_names='coco.names', use_cuda=False, width=416, height=416):
        self.detector = YoloDetector(yolo_cfg, yolo_weights, coco_names, use_cuda=use_cuda)
        self.camera = Camera.instance(width=224, height=224)
        self.image_widget = widgets.Image(format='jpeg', width=640, height=480)
        display(self.image_widget)


        self._running = False
        self._thread = None
        # thresholds
        self.conf_threshold = 0.5
        self.nms_threshold = 0.4



class NotebookYoloApp:
    def __init__(self, yolo_cfg, yolo_weights, coco_names, use_cuda=False, width=416, height=416):
        self.detector = YoloDetector(yolo_cfg, yolo_weights, coco_names, use_cuda)
        self.camera = Camera.instance(width=224, height=224)
        self.image_widget = widgets.Image(format='jpeg', width=640, height=480)
        self._running = False
        self._thread = None

    def _process_loop(self):
        from jetbot import Robot
        import time
        robot = Robot()

        while self._running:
            frame = self.camera.value
            if frame is None:
                time.sleep(0.01)
                continue

            detections, t = self.detector.detect(frame)
            self.detector.draw_detections(frame, detections)

            # Example simple avoidance logic
            too_close = any((w * h) > 20000 for (x, y, w, h) in [d['box'] for d in detections])
            if too_close:
                robot.stop()
            else:
                robot.forward(0.3)

            self.image_widget.value = bgr8_to_jpeg(frame)
            time.sleep(0.01)

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._process_loop)
            self._thread.start()

    def stop(self):
        if self._running:
            self._running = False
            if self._thread is not None:
                self._thread.join()




# Usage (in a Jupyter notebook cell):
# from notebook_demo import NotebookYoloApp
# app = NotebookYoloApp(yolo_cfg='yolov3.cfg', yolo_weights='yolov3.weights', coco_names='coco.names')
# app.start()
# ... when done: app.stop()