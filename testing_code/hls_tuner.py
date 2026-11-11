import cv2
import numpy as np

def nothing(x): pass

def main():
    cap = cv2.VideoCapture('b1.mp4')
    if not cap.isOpened(): return

    window_name = "HLS Color Tuner"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 640, 400)

    # Khởi tạo thanh trượt (Hue: 0-179, Lightness: 0-255, Saturation: 0-255)
    cv2.createTrackbar('H Min', window_name, 0, 179, nothing)
    cv2.createTrackbar('H Max', window_name, 179, 179, nothing)
    cv2.createTrackbar('L Min', window_name, 150, 255, nothing)
    cv2.createTrackbar('L Max', window_name, 255, 255, nothing)
    cv2.createTrackbar('S Min', window_name, 0, 255, nothing)
    cv2.createTrackbar('S Max', window_name, 255, 255, nothing)

    is_paused = False

    print("=== HƯỚNG DẪN ===")
    print("1. Tìm vạch TRẮNG: Kéo L Min lên cao (~150-180), S Min để thấp, H full dải.")
    print("2. Tìm vạch VÀNG: Thu hẹp H (khoảng 15-35), đẩy S Min lên cao (>50) để lọc màu lợt.")
    print("Nhấn 'p' để Tạm dừng, 'q' để Thoát và in thông số.")

    while True:
        if not is_paused:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            frame = cv2.resize(frame, (640, 360))
            
            # Giả lập lại bước tăng sáng gamma (Nếu video tối)
            gamma = 1.0 
            table = np.array([((i / 255.0) ** gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            frame_gamma = cv2.LUT(frame, table)
            
            hls = cv2.cvtColor(frame_gamma, cv2.COLOR_BGR2HLS)

        h_min = cv2.getTrackbarPos('H Min', window_name)
        h_max = cv2.getTrackbarPos('H Max', window_name)
        l_min = cv2.getTrackbarPos('L Min', window_name)
        l_max = cv2.getTrackbarPos('L Max', window_name)
        s_min = cv2.getTrackbarPos('S Min', window_name)
        s_max = cv2.getTrackbarPos('S Max', window_name)

        lower_bound = np.array([h_min, l_min, s_min], dtype=np.uint8)
        upper_bound = np.array([h_max, l_max, s_max], dtype=np.uint8)

        mask = cv2.inRange(hls, lower_bound, upper_bound)
        result = cv2.bitwise_and(frame, frame, mask=mask)

        # Ghép 2 ảnh: Mask đen trắng và Kết quả màu
        mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        combined = np.hstack((mask_bgr, result))
        
        cv2.imshow(window_name, combined)

        key = cv2.waitKey(1 if not is_paused else 30) & 0xFF
        if key == ord('q'):
            print(f"\n[Thông số bạn vừa chọn]")
            print(f"lower = np.array([{h_min}, {l_min}, {s_min}], dtype=np.uint8)")
            print(f"upper = np.array([{h_max}, {l_max}, {s_max}], dtype=np.uint8)\n")
            break
        elif key == ord('p'):
            is_paused = not is_paused

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()