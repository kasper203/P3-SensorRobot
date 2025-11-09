import cv2 as cv
import numpy as np
import time
from typing import Tuple, List


class YoloDetector:
    def __init__(self, cfg_path: str, weights_path: str, names_path: str, use_cuda: bool = False):
        self.cfg_path = cfg_path
        self.weights_path = weights_path
        self.names_path = names_path

        # Load class names
        with open(self.names_path, 'r') as f:
            self.classes = [c.strip() for c in f.readlines()]

        np.random.seed(42)
        self.colors = np.random.randint(0, 255, size=(len(self.classes), 3), dtype='uint8')

        # Load network
        self.net = cv.dnn.readNetFromDarknet(self.cfg_path, self.weights_path)
        self.net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)
        if use_cuda:
            # if OpenCV built with CUDA and cuDNN support
            try:
                self.net.setPreferableTarget(cv.dnn.DNN_TARGET_CUDA)
            except Exception:
                # fallback to CPU if CUDA target isn't available
                self.net.setPreferableTarget(cv.dnn.DNN_TARGET_CPU)
        else:
            self.net.setPreferableTarget(cv.dnn.DNN_TARGET_CPU)

        ln = self.net.getLayerNames()
        self.ln = [ln[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]

    def detect(self, frame, conf_threshold=0.5, nms_threshold=0.4) -> Tuple[List[dict], float]:
        """Run YOLO detection on a BGR frame.
        Returns a list of detection dicts and the forward time in seconds.

        detection dict keys: class_id, class_name, confidence, box=(x, y, w, h)
        """
        H, W = frame.shape[:2]
        blob = cv.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
        self.net.setInput(blob)
        t0 = time.time()
        outputs = self.net.forward(self.ln)
        t = time.time() - t0

        outputs = np.vstack(outputs)

        boxes = []
        confidences = []
        classIDs = []

        for output in outputs:
            scores = output[5:]
            classID = int(np.argmax(scores))
            confidence = float(scores[classID])
            if confidence > conf_threshold:
                x, y, w, h = output[:4] * np.array([W, H, W, H])
                x1 = int(x - w // 2)
                y1 = int(y - h // 2)
                boxes.append([x1, y1, int(w), int(h)])
                confidences.append(confidence)
                classIDs.append(classID)

        indices = cv.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)
        detections = []
        if len(indices) > 0:
            for i in indices.flatten():
                x, y, w, h = boxes[i]
                detections.append({
                    'class_id': classIDs[i],
                    'class_name': self.classes[classIDs[i]],
                    'confidence': confidences[i],
                    'box': (x, y, w, h)
                })

        return detections, t

    def draw_detections(self, frame, detections):
        """Draw boxes and labels on the frame (modifies frame in-place).
        """
        for det in detections:
            x, y, w, h = det['box']
            color = [int(c) for c in self.colors[det['class_id']]]
            cv.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            label = f"{det['class_name']}: {det['confidence']:.2f}"
            cv.putText(frame, label, (x, max(15, y - 5)), cv.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)


if __name__ == '__main__':
    # quick smoke test (requires paths to YOLO files)
    print('Detector module loaded. Use YoloDetector(cfg, weights, names)')