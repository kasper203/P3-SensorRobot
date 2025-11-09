import threading
import time
import cv2 as cv
from jetbot import Camera, bgr8_to_jpeg
import ipywidgets.widgets as widgets
from IPython.display import display


from detector import YoloDetector


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


    def _process_loop(self):
        while self._running:
            frame = self.camera.value # BGR numpy array
            if frame is None:
                time.sleep(0.01)
                continue

            detections, t = self.detector.detect(frame, conf_threshold=self.conf_threshold, nms_threshold=self.nms_threshold)
            self.detector.draw_detections(frame, detections)
            overlay = f"inference={t*1000:.1f}ms" # ms
            cv.putText(frame, overlay, (10, 20), cv.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)

            jpeg = bgr8_to_jpeg(frame)
            # update widget
            self.image_widget.value = jpeg
            # small sleep to yield
            time.sleep(0.01)


    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()
        print('Notebook Yolo App started')


    def stop(self):
        if not self._running:
            return
        self._running = False
        self._thread.join(timeout=1.0)
        self.camera.stop()
        print('Notebook Yolo App stopped')




# Usage (in a Jupyter notebook cell):
# from notebook_demo import NotebookYoloApp
# app = NotebookYoloApp(yolo_cfg='yolov3.cfg', yolo_weights='yolov3.weights', coco_names='coco.names')
# app.start()
# ... when done: app.stop()