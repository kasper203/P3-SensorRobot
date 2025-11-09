# main.py
# Script fallback: runs YOLO on a standard webcam (useful if not running in Jupyter)
# NEW


import cv2 as cv
from detector import YoloDetector


CONF = 0.5
NMS = 0.4


if __name__ == '__main__':
    yolo = YoloDetector('yolov3.cfg', 'yolov3.weights', 'coco.names', use_cuda=False)
    cap = cv.VideoCapture(0)


    if not cap.isOpened():
        print('Error: could not open webcam')
        exit(1)


    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            detections, t = yolo.detect(frame, conf_threshold=CONF, nms_threshold=NMS)
            yolo.draw_detections(frame, detections)
            cv.putText(frame, f"inference={t*1000:.1f}ms", (10, 20), cv.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)
            cv.imshow('YOLO', frame)
            if cv.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
            cap.release()
            cv.destroyAllWindows()