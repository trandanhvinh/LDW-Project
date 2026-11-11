import cv2
import numpy as np

FRAME_WIDTH = 800
FRAME_HEIGHT = 600

# ==========================================
# 1. CÁC HÀM XỬ LÝ ẢNH CƠ BẢN (Từ bước 1)
# ==========================================
def auto_adjust_gamma(image):
    height, width = image.shape[:2]
    y_start, y_end = int(height * 0.6), height 
    road_roi = image[y_start:y_end, 0:width]
    gray_roi = cv2.cvtColor(road_roi, cv2.COLOR_BGR2GRAY)
    mean_bright = np.mean(gray_roi)
    gamma = np.interp(mean_bright, [30, 110, 160], [1.5, 0.3, 0.05])
    gamma = np.clip(gamma, 0.01, 2.0)
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)

def process_frame_pipeline(frame, threshold=105):
    frame_gamma = auto_adjust_gamma(frame)
    lab = cv2.cvtColor(frame_gamma, cv2.COLOR_BGR2LAB)
    L = lab[:, :, 0]
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    L_clahe = clahe.apply(L)
    _, binary = cv2.threshold(L_clahe, threshold, 255, cv2.THRESH_BINARY)
    kernel = np.ones((3, 3), np.uint8)
    return cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

# ==========================================
# 2. BỘ ĐIỀU KHIỂN TRACKBAR
# ==========================================
def nothing(x): pass

def setup_trackbars():
    cv2.namedWindow("BEV Tuner")
    cv2.resizeWindow("BEV Tuner", 400, 200)
    # Khoảng cách từ tâm ra 2 bên đỉnh (Top Width)
    cv2.createTrackbar("Top Width", "BEV Tuner", 60, 400, nothing) 
    # Khoảng cách từ tâm ra 2 bên đáy (Bottom Width)
    cv2.createTrackbar("Bottom Width", "BEV Tuner", 300, 400, nothing) 
    # Chiều cao của Đỉnh hình thang (Top Y)
    cv2.createTrackbar("Top Y", "BEV Tuner", 380, FRAME_HEIGHT, nothing)
    # Chiều cao của Đáy hình thang (Bottom Y)
    cv2.createTrackbar("Bottom Y", "BEV Tuner", 570, FRAME_HEIGHT, nothing)

def get_src_from_trackbars():
    tw = cv2.getTrackbarPos("Top Width", "BEV Tuner")
    bw = cv2.getTrackbarPos("Bottom Width", "BEV Tuner")
    ty = cv2.getTrackbarPos("Top Y", "BEV Tuner")
    by = cv2.getTrackbarPos("Bottom Y", "BEV Tuner")
    
    center_x = FRAME_WIDTH // 2
    src = np.float32([
        [center_x - tw, ty], # Đỉnh trái
        [center_x + tw, ty], # Đỉnh phải
        [center_x + bw, by], # Đáy phải
        [center_x - bw, by]  # Đáy trái
    ])
    return src

# ==========================================
# 3. VÒNG LẶP CHÍNH
# ==========================================
if __name__ == "__main__":
    cap = cv2.VideoCapture('test7.mp4') # Thay video của bạn
    setup_trackbars()
    
    print("🚀 BỘ TINH CHỈNH BEV ĐÃ MỞ!")
    print("Hãy kéo các thanh trượt trong cửa sổ 'BEV Tuner' để căn chỉnh hình thang.")
    print("Nhấn ESC để thoát.")

    while True:
        ret, frame = cap.read()
        if not ret: 
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
            
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        
        # 1. Lấy mask đen trắng
        final_mask = process_frame_pipeline(frame, threshold=105)
        
        # 2. Lấy tọa độ hình thang từ thanh trượt
        src = get_src_from_trackbars()
        
        # 3. Kéo giãn ảnh (Bird's Eye View)
        offset_x = 200 # Lề an toàn để vạch không dính sát viền
        dst = np.float32([
            [offset_x, 0], 
            [FRAME_WIDTH - offset_x, 0], 
            [FRAME_WIDTH - offset_x, FRAME_HEIGHT], 
            [offset_x, FRAME_HEIGHT]
        ])
        
        M = cv2.getPerspectiveTransform(src, dst)
        warped_mask = cv2.warpPerspective(final_mask, M, (FRAME_WIDTH, FRAME_HEIGHT), flags=cv2.INTER_LINEAR)
        
        # 4. Hiển thị trực quan
        # Vẽ hình thang lên ảnh gốc để dễ nhắm
        frame_with_poly = frame.copy()
        cv2.polylines(frame_with_poly, [np.int32(src)], True, (0, 0, 255), 2)
        
        # Chuyển ảnh BEV sang 3 kênh màu để ghép chung
        warped_color = cv2.cvtColor(warped_mask, cv2.COLOR_GRAY2BGR)
        
        # Ghép 2 màn hình cạnh nhau
        side_by_side = np.hstack((frame_with_poly, warped_color))
        # Thu nhỏ lại một chút để xem trên màn hình máy tính dễ hơn
        side_by_side = cv2.resize(side_by_side, (FRAME_WIDTH * 2 // 2, FRAME_HEIGHT // 2))
        
        cv2.imshow("Left: Khung ngam | Right: BEV Output", side_by_side)
        
        # 5. In tọa độ tối ưu ra terminal nếu người dùng muốn lưu lại
        key = cv2.waitKey(30) & 0xFF
        if key == 27: # Phím ESC
            print("\n=== LƯU LẠI TỌA ĐỘ NÀY CHO CODE CHÍNH ===")
            print(f"src = np.float32([\n    [{src[0][0]}, {src[0][1]}],\n    [{src[1][0]}, {src[1][1]}],\n    [{src[2][0]}, {src[2][1]}],\n    [{src[3][0]}, {src[3][1]}]\n])")
            break

    cap.release()
    cv2.destroyAllWindows()