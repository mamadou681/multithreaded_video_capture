#!/usr/bin/env python3
import cv2
import threading
import queue
import sys

def apply_filter(frame):
    """CLAHE filter (Contrast Limited Adaptive Histogram Equalization)"""
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    lab = cv2.merge((l2, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

def capture_video(cap, q, stop_event):
    """Thread for capturing video frames"""
    while not stop_event.is_set():
        ok, frame = cap.read()
        if not ok:
            continue
        try:
            q.put(frame, timeout=0.1)
        except queue.Full:
            # If the queue is full, drop the frame
            pass   

def display_video(q, stop_event):
    """Thread for displaying video + applying filter"""
    cv2.namedWindow("Video", cv2.WINDOW_NORMAL)
    while not stop_event.is_set():
        try:
            frame = q.get(timeout=0.1)
        except queue.Empty:
            continue

        # Apply filter before displaying
        frame = apply_filter(frame)

        cv2.imshow("Video", frame)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), 27):  # 'q' or ESC
            stop_event.set()
            break

        # Check if window was closed
        if cv2.getWindowProperty("Video", cv2.WND_PROP_VISIBLE) < 1:
            stop_event.set()
            break

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Failed to open the camera", file=sys.stderr)
        return 1

    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    q = queue.Queue(maxsize=2) # thread-safe queue for frames
    stop_event = threading.Event()  # synchronization for stopping threads

     # Create threads
    t1 = threading.Thread(target=capture_video, args=(cap, q, stop_event))
    t2 = threading.Thread(target=display_video, args=(q, stop_event))
   
    # Start threads
    t1.start()
    t2.start()

    # Wait for both threads to finish
    t1.join()
    t2.join()

    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    return 0

if __name__ == "__main__":
    sys.exit(main())
