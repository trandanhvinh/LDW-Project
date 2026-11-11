import cv2
import numpy as np
import math

cap = cv2.VideoCapture('challenge_video.mp4')
frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("Đã phát hết video, tự động lặp lại...")
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue
    frame_count += 1

    frame = cv2.resize(frame, (400, 300))
    height, width = frame.shape[:2]

    frame1 = frame.copy()
    frame2 = frame.copy()
    frame3 = frame.copy()

    #Polygon Masking
    pts_static = np.array([[40, height], [160, 180], [240, 180], [360, height]], np.int32)
    cv2.polylines(frame1, [pts_static], True, (0, 0, 255), 3)
    cv2.putText(frame1, "1. Static ROI", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    #Dynamic ROI
    vp_y = int(180 + 30 * math.sin(frame_count * 0.1)) 
    pts_dyn = np.array([[40, height], [160, vp_y + 20], [240, vp_y + 20], [360, height]], np.int32)
    cv2.polylines(frame2, [pts_dyn], True, (0, 255, 0), 3)
    cv2.circle(frame2, (width//2, vp_y), 6, (255, 0, 0), -1)
    cv2.putText(frame2, "2. Dynamic ROI", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    #Kalman ROI
    overlay = frame3.copy()
    cv2.line(overlay, (150, 180), (60, height), (0, 255, 255), 45)
    cv2.line(overlay, (250, 180), (340, height), (0, 255, 255), 45)
    
    cv2.addWeighted(overlay, 0.4, frame3, 0.6, 0, frame3)
    cv2.putText(frame3, "3. Kalman ROI", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)


    combined_frames = np.hstack((frame1, frame2, frame3))

    cv2.imshow("Mo phong 3 Thuat toan ROI", combined_frames)

    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()