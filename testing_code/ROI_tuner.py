import cv2
import numpy as np
from config import FRAME_WIDTH, FRAME_HEIGHT, BOTTOM_Y_PERCENTAGE

def nothing(x):
    pass

def main():
    # Thay đổi đường dẫn video test của bạn tại đây
    video_path = 'VIDEO_GOC.mp4'
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Lỗi: Không thể mở video.")
        return

    window_name = "Dynamic ROI & BEV Tuner (Sync with step2 & step3)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 450)

    # 1. Thanh trượt giả lập tọa độ Điểm tụ (Vanishing Point)
    cv2.createTrackbar('VP X', window_name, FRAME_WIDTH // 2, FRAME_WIDTH, nothing)
    cv2.createTrackbar('VP Y', window_name, int(FRAME_HEIGHT * 0.6), FRAME_HEIGHT, nothing)

    # 2. Thanh trượt thông số hình học Dynamic ROI (Khớp 100% với config.py và step2)
    cv2.createTrackbar('ROI Offset Y', window_name, 30, 100, nothing)
    cv2.createTrackbar('Top Half W', window_name, 45, 200, nothing)
    cv2.createTrackbar('Bot Offset L', window_name, 210, 400, nothing)
    cv2.createTrackbar('Bot Offset R', window_name, 210, 400, nothing)
    
    # 3. Thanh trượt thông số khoảng cách biên BEV (Áp dụng cho step3)
    # Mặc định lấy 200 theo config.py của bạn
    cv2.createTrackbar('BEV Dst X', window_name, 200, 320, nothing)

    is_paused = False

    print("=== HƯỚNG DẪN SỬ DỤNG DYNAMIC ROI TUNER ===")
    print("- Màn hình TRÁI: Vùng ROI bám theo Điểm tụ.")
    print("- Màn hình PHẢI: Kết quả góc nhìn chim bay (BEV).")
    print("- MỤC TIÊU: Chỉnh 'BEV Dst X', 'Top Half W', 'Bot Offset...' để 2 vạch song song.")
    print("- Phím 'p' để Tạm dừng/Phát tiếp video | 'q' để In thông số và Thoát.")
    print("===========================================")

    while True:
        if not is_paused:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        height, width = frame.shape[:2]
        bottom_y = int(height * BOTTOM_Y_PERCENTAGE)

        # Lấy giá trị từ thanh trượt
        vp_x = cv2.getTrackbarPos('VP X', window_name)
        vp_y = cv2.getTrackbarPos('VP Y', window_name)
        
        roi_offset_y = cv2.getTrackbarPos('ROI Offset Y', window_name)
        top_half_w = cv2.getTrackbarPos('Top Half W', window_name)
        bot_offset_l = cv2.getTrackbarPos('Bot Offset L', window_name)
        bot_offset_r = cv2.getTrackbarPos('Bot Offset R', window_name)
        bev_dst_x = cv2.getTrackbarPos('BEV Dst X', window_name)

        # Tính toán tọa độ đỉnh của hình thang ROI y hệt step2_dynamic_roi.py
        top_y = min(max(vp_y + roi_offset_y, 0), height)

        pt_bl = [vp_x - bot_offset_l, bottom_y]   # Đáy dưới trái
        pt_tl = [vp_x - top_half_w, top_y]        # Đỉnh trên trái
        pt_tr = [vp_x + top_half_w, top_y]        # Đỉnh trên phải
        pt_br = [vp_x + bot_offset_r, bottom_y]   # Đáy dưới phải

        polygon = np.array([[pt_bl, pt_tl, pt_tr, pt_br]], np.int32)

        # ==========================================
        # XỬ LÝ MÀN HÌNH TRÁI (HIỂN THỊ ROI ĐỘNG)
        # ==========================================
        left_display = frame.copy()
        
        # Đánh dấu Điểm tụ giả lập
        cv2.circle(left_display, (vp_x, vp_y), 5, (0, 0, 255), -1)

        # Hiệu ứng làm tối vùng ngoài hình thang
        mask = np.zeros_like(frame)
        cv2.fillPoly(mask, polygon, (255, 255, 255))
        dark_frame = cv2.addWeighted(left_display, 0.3, np.zeros_like(left_display), 0.7, 0)
        roi_focus = cv2.bitwise_and(left_display, mask)
        left_display = cv2.add(dark_frame, roi_focus)

        cv2.polylines(left_display, polygon, True, (0, 255, 255), 2)
        cv2.putText(left_display, "1. Dynamic ROI (step2)", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # ==========================================
        # XỬ LÝ MÀN HÌNH PHẢI (HIỂN THỊ BEV PREVIEW)
        # ==========================================
        # Trình tự điểm Nguồn (Src) giống hệt step3_birdseye_view.py
        src_pts = np.float32([pt_bl, pt_tl, pt_tr, pt_br])
        
        # Trình tự điểm Đích (Dst) với tham số BEV_DST_OFFSET_X tùy chỉnh
        dst_pts = np.float32([
            [bev_dst_x, height],          # Tương ứng với pt_bl
            [bev_dst_x, 0],               # Tương ứng với pt_tl
            [width - bev_dst_x, 0],       # Tương ứng với pt_tr
            [width - bev_dst_x, height]   # Tương ứng với pt_br
        ])
        
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        right_display = cv2.warpPerspective(frame, M, (width, height), flags=cv2.INTER_LINEAR)
        
        cv2.putText(right_display, "2. Bird's Eye View (step3)", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Trạng thái tạm dừng
        if is_paused:
            cv2.putText(left_display, "PAUSED - 'p' to Resume", (15, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Ghép 2 màn hình
        combined = np.hstack((left_display, right_display))
        cv2.imshow(window_name, combined)

        # Xử lý phím bấm
        delay = 1 if not is_paused else 30
        key = cv2.waitKey(delay) & 0xFF

        if key == ord('q'):
            print("\n=== CẬP NHẬT THÔNG SỐ VÀO CONFIG.PY ===")
            print(f"ROI_OFFSET_Y = {roi_offset_y}")
            print(f"ROI_TOP_HALF_WIDTH = {top_half_w}")
            print(f"ROI_BOTTOM_OFFSET_LEFT = {bot_offset_l}")
            print(f"ROI_BOTTOM_OFFSET_RIGHT = {bot_offset_r}")
            print(f"BEV_DST_OFFSET_X = {bev_dst_x}")
            print("=======================================\n")
            break
        elif key == ord('p'):
            is_paused = not is_paused

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()