import cv2
import numpy as np

# Hàm callback trống cho Trackbar
def nothing(x):
    pass

def main():
    # Thay đổi đường dẫn video test của bạn tại đây
    video_path = 'VIDEO_GOC.mp4' 
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Lỗi: Không thể mở video.")
        return

    window_name = "Dynamic ROI Tuner (Advanced)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 900, 700)

    # 1. Các thông số tĩnh cơ bản
    cv2.createTrackbar('Bottom Y (%)', window_name, 95, 100, nothing)
    cv2.createTrackbar('Horizon Y (%)', window_name, 60, 100, nothing)
    cv2.createTrackbar('Bot Left X (%)', window_name, 5, 100, nothing)
    cv2.createTrackbar('Bot Right X (%)', window_name, 85, 100, nothing)

    # 2. Các thông số dành riêng cho TÍNH NĂNG MẶT NẠ ĐỘNG
    cv2.createTrackbar('Top Half Width (px)', window_name, 50, 320, nothing)
    cv2.createTrackbar('Simulate VP X (%)', window_name, 50, 100, nothing) # Mặc định Điểm tụ nằm giữa (50%)

    is_paused = False

    print("==================================================")
    print("=== HƯỚNG DẪN SỬ DỤNG DYNAMIC ROI TUNER ===")
    print("- Kéo các thanh 'Bot/Horizon' để cắt bỏ nắp capo và bầu trời.")
    print("- Kéo thanh 'Simulate VP X' để giả lập xe đang ôm cua (Điểm tụ dịch chuyển).")
    print("- Kéo thanh 'Top Half Width' để đảm bảo mặt nạ lúc trượt không làm đứt vạch đường.")
    print("- Nhấn 'p' để Tạm dừng/Phát tiếp video.")
    print("- Nhấn 'q' để Thoát và in ra thông số dán vào config.py.")
    print("==================================================")

    while True:
        if not is_paused:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            # Đưa về kích thước chuẩn theo config (640x360)
            frame = cv2.resize(frame, (640, 360))

        height, width = frame.shape[:2]

        # 1. Lấy giá trị từ thanh trượt
        bot_y_ratio = cv2.getTrackbarPos('Bottom Y (%)', window_name) / 100.0
        horiz_y_ratio = cv2.getTrackbarPos('Horizon Y (%)', window_name) / 100.0
        bl_x_ratio = cv2.getTrackbarPos('Bot Left X (%)', window_name) / 100.0
        br_x_ratio = cv2.getTrackbarPos('Bot Right X (%)', window_name) / 100.0
        
        dynamic_top_half_width = cv2.getTrackbarPos('Top Half Width (px)', window_name)
        vp_x_ratio = cv2.getTrackbarPos('Simulate VP X (%)', window_name) / 100.0

        # Ràng buộc logic cơ bản (tránh việc đáy lật ngược hoặc trái đè phải)
        bl_x_ratio = min(bl_x_ratio, br_x_ratio - 0.01)
        horiz_y_ratio = min(horiz_y_ratio, bot_y_ratio - 0.01)

        # 2. Tính toán tọa độ Pixel thực tế (Hệ thống MẶT NẠ ĐỘNG)
        bottom_y = int(height * bot_y_ratio)
        horizon_y = int(height * horiz_y_ratio)
        
        # Tính toán tọa độ giả lập của điểm tụ (Vanishing Point)
        vp_x = int(width * vp_x_ratio)

        pt_bl = (int(width * bl_x_ratio), bottom_y)
        # Đỉnh nắp hình thang bây giờ sẽ nở ra từ điểm tụ giả lập
        pt_tl = (vp_x - dynamic_top_half_width, horizon_y)
        pt_tr = (vp_x + dynamic_top_half_width, horizon_y)
        pt_br = (int(width * br_x_ratio), bottom_y)

        polygon = np.array([[pt_bl, pt_tl, pt_tr, pt_br]], np.int32)

        # 3. Tạo hiệu ứng đồ họa
        mask = np.zeros_like(frame)
        cv2.fillPoly(mask, [polygon], (255, 255, 255))
        
        dark_frame = cv2.addWeighted(frame, 0.3, np.zeros_like(frame), 0.7, 0)
        roi_focus = cv2.bitwise_and(frame, mask)
        display = cv2.add(dark_frame, roi_focus)

        # Vẽ đường viền hình thang
        cv2.polylines(display, [polygon], True, (0, 255, 0), 2)
        
        # Vẽ một điểm vàng để hiển thị vị trí Điểm tụ (VP) đang giả lập
        cv2.circle(display, (vp_x, horizon_y), 5, (0, 255, 255), -1)

        if is_paused:
            cv2.putText(display, "PAUSED - Press 'p' to Resume", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow(window_name, display)

        delay = 1 if not is_paused else 30
        key = cv2.waitKey(delay) & 0xFF

        if key == ord('q'):
            print("\n=== COPY ĐOẠN SAU VÀO CONFIG.PY CỦA BẠN ===")
            print(f"BOTTOM_Y_PERCENTAGE = {bot_y_ratio:.2f}")
            print(f"BASE_MASK_HORIZON_RATIO = {horiz_y_ratio:.2f}")
            print(f"BASE_MASK_BOT_LEFT_RATIO = {bl_x_ratio:.2f}")
            print(f"BASE_MASK_BOT_RIGHT_RATIO = {br_x_ratio:.2f}")
            print(f"DYNAMIC_BASE_MASK_TOP_HALF_WIDTH = {dynamic_top_half_width}")
            print("===========================================\n")
            break
        elif key == ord('p'):
            is_paused = not is_paused

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()