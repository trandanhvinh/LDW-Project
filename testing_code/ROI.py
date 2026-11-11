import cv2
import numpy as np
import math

FRAME_WIDTH = 800
FRAME_HEIGHT = 600
BOTTOM_Y_PERCENTAGE = 0.95 

def get_base_mask(width, height, bottom_y):
    mask = np.zeros((height, width), dtype=np.uint8)
    horizon_y = int(height * 0.60) 
    polygon = np.array([[(0, bottom_y), (int(width * 0.25), horizon_y), (int(width * 0.75), horizon_y), (width, bottom_y)]], np.int32)
    cv2.fillPoly(mask, [polygon], 255)
    return mask

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
    return cv2.LUT(image, table), gamma, mean_bright

def process_frame_pipeline(frame, threshold=105):
    frame_gamma, gamma_val, mean_bright = auto_adjust_gamma(frame)
    lab = cv2.cvtColor(frame_gamma, cv2.COLOR_BGR2LAB)
    L = lab[:, :, 0]
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    L_clahe = clahe.apply(L)
    _, binary = cv2.threshold(L_clahe, threshold, 255, cv2.THRESH_BINARY)
    kernel = np.ones((3, 3), np.uint8)
    return cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1), gamma_val, mean_bright

def classify(lines, width):
    left, right = [], []
    if lines is None: return left, right
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x1 == x2: continue
        m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1
        if abs(m) < 0.5 or abs(m) > 2.5: continue
        mid_x = (x1 + x2) / 2
        if m < 0 and mid_x < width * 0.65: left.append((m, b))
        elif m > 0 and mid_x > width * 0.35: right.append((m, b))
    return left, right

def find_vanishing_point(left_lines, right_lines, frame_width, frame_height):
    intersections_x, intersections_y = [], []
    for left_m, left_b in left_lines:
        for right_m, right_b in right_lines:
            if left_m == right_m: continue
            x = (right_b - left_b) / (left_m - right_m)
            y = left_m * x + left_b
            if 0 <= x <= frame_width and 0 <= y <= frame_height:
                intersections_x.append(x)
                intersections_y.append(y)
    if len(intersections_x) > 0:
        return (int(np.median(intersections_x)), int(np.median(intersections_y)))
    return None     

def get_roi_polygon(width, height, vp, bottom_y):
    if vp is None:
        vp_y = int(height * 0.6) 
        vp_x = width // 2
    else:
        vp_x, vp_y = vp
    offset_y = 30 
    top_y = min(max(vp_y + offset_y, 0), height)
    offset_x = 60 
    polygon = np.array([[(width * 0.15, bottom_y), (vp_x - offset_x, top_y), (vp_x + offset_x, top_y), (width * 0.85, bottom_y)]], np.int32)
    return polygon

def bird_eye_view(img):
    height, width = img.shape[:2]
    src = np.float32([
    [277.0, 375.0],
    [523.0, 375.0],
    [709.0, 570.0],
    [91.0, 570.0]
    ])
    offset = 150 
    dst = np.float32([
        [offset, 0], 
        [width - offset, 0], 
        [width - offset, height], 
        [offset, height]
    ])
    M = cv2.getPerspectiveTransform(src, dst)
    Minv = cv2.getPerspectiveTransform(dst, src)
    warped = cv2.warpPerspective(img, M, (width, height), flags=cv2.INTER_LINEAR)
    return warped, M, Minv

def get_histogram_peaks(binary_warped):
    height = binary_warped.shape[0]
    bottom_half = binary_warped[height // 2 :, :]
    histogram = np.sum(bottom_half, axis=0)
    midpoint = int(histogram.shape[0] // 2)
    leftx_base = np.argmax(histogram[:midpoint])
    rightx_base = np.argmax(histogram[midpoint:]) + midpoint
    return histogram, leftx_base, rightx_base

def draw_dashed_line(img, pt1, pt2, color, thickness=1, dash_length=10):
    x1, y1 = pt1
    x2, y2 = pt2
    dist = math.hypot(x2 - x1, y2 - y1)
    if dist == 0: return
    dashes = int(dist / dash_length)
    for i in range(dashes):
        start = (int(x1 + (x2 - x1) * i / dashes), int(y1 + (y2 - y1) * i / dashes))
        end = (int(x1 + (x2 - x1) * (i + 0.5) / dashes), int(y1 + (y2 - y1) * (i + 0.5) / dashes))
        cv2.line(img, start, end, color, thickness)

def draw_matplotlib_style_dashboard(binary_warped, histogram, leftx_base, rightx_base):
    h_bev, w_bev = binary_warped.shape
    top_panel_h = 350
    top_panel = np.ones((top_panel_h, w_bev, 3), dtype=np.uint8) * 255 
    
    bottom_half = binary_warped[h_bev // 2 :, :]
    bottom_half_bgr = cv2.cvtColor(bottom_half, cv2.COLOR_GRAY2BGR)
    
    draw_dashed_line(bottom_half_bgr, (leftx_base, 0), (leftx_base, bottom_half.shape[0]), (0, 0, 255), 2)
    draw_dashed_line(bottom_half_bgr, (rightx_base, 0), (rightx_base, bottom_half.shape[0]), (0, 0, 255), 2)
    
    top_panel[50:50+bottom_half.shape[0], 0:w_bev] = bottom_half_bgr
    cv2.putText(top_panel, "Nua duoi cua anh Bird's Eye view", (w_bev//2 - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    bot_panel_h = 400
    bot_panel = np.ones((bot_panel_h, w_bev, 3), dtype=np.uint8) * 255 
    
    pad_x, pad_y = 50, 50
    graph_w, graph_h = w_bev - 2*pad_x, bot_panel_h - 2*pad_y
    
    for i in range(0, w_bev, 100):
        cv2.line(bot_panel, (i, pad_y), (i, pad_y + graph_h), (230, 230, 230), 1)
    for i in range(0, 120, 20):
        y_pos = pad_y + graph_h - int(i/100 * graph_h)
        cv2.line(bot_panel, (pad_x, y_pos), (pad_x + graph_w, y_pos), (230, 230, 230), 1)

    cv2.rectangle(bot_panel, (pad_x, pad_y), (pad_x + graph_w, pad_y + graph_h), (150, 150, 150), 1)

    max_val = np.max(histogram)
    if max_val > 0:
        pts = []
        for x in range(pad_x, pad_x + graph_w):
            y = pad_y + graph_h - int((histogram[x] / max_val) * graph_h)
            pts.append([x, y])
        cv2.polylines(bot_panel, [np.array(pts, np.int32)], False, (255, 0, 127), 2) 

        y_left = pad_y + graph_h - int((histogram[leftx_base] / max_val) * graph_h)
        y_right = pad_y + graph_h - int((histogram[rightx_base] / max_val) * graph_h)
        
        cv2.circle(bot_panel, (leftx_base, y_left), 6, (0, 0, 255), -1)
        cv2.circle(bot_panel, (rightx_base, y_right), 6, (0, 0, 255), -1)
        
        cv2.putText(bot_panel, f"Left: {leftx_base}", (leftx_base - 20, y_left - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        cv2.putText(bot_panel, f"Right: {rightx_base}", (rightx_base - 20, y_right - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

    cv2.putText(bot_panel, "Do thi Spatial Histogram", (w_bev//2 - 100, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    return np.vstack((top_panel, bot_panel))

def sliding_window(binary_warped, leftx_base, rightx_base):
    out_img = np.dstack((binary_warped, binary_warped, binary_warped)) * 255
    nwindows, margin, minpix = 9, 50, 50
    window_height = int(binary_warped.shape[0] // nwindows)
    
    nonzero = binary_warped.nonzero()
    nonzeroy = np.array(nonzero[0])
    nonzerox = np.array(nonzero[1])
    
    leftx_current, rightx_current = leftx_base, rightx_base
    left_lane_inds, right_lane_inds = [], []
    
    for window in range(nwindows):
        win_y_low = binary_warped.shape[0] - (window + 1) * window_height
        win_y_high = binary_warped.shape[0] - window * window_height
        win_xleft_low, win_xleft_high = leftx_current - margin, leftx_current + margin
        win_xright_low, win_xright_high = rightx_current - margin, rightx_current + margin
        
        cv2.rectangle(out_img, (win_xleft_low, win_y_low), (win_xleft_high, win_y_high), (0, 255, 0), 2)
        cv2.rectangle(out_img, (win_xright_low, win_y_low), (win_xright_high, win_y_high), (0, 255, 0), 2)
        
        good_left_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) & 
                          (nonzerox >= win_xleft_low) & (nonzerox < win_xleft_high)).nonzero()[0]
        good_right_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) & 
                           (nonzerox >= win_xright_low) & (nonzerox < win_xright_high)).nonzero()[0]
        
        left_lane_inds.append(good_left_inds)
        right_lane_inds.append(good_right_inds)
        
        if len(good_left_inds) > minpix: leftx_current = int(np.mean(nonzerox[good_left_inds]))
        if len(good_right_inds) > minpix: rightx_current = int(np.mean(nonzerox[good_right_inds]))
            
    left_lane_inds = np.concatenate(left_lane_inds) if len(left_lane_inds) > 0 else np.array([])
    right_lane_inds = np.concatenate(right_lane_inds) if len(right_lane_inds) > 0 else np.array([])
    
    out_img[nonzeroy[left_lane_inds], nonzerox[left_lane_inds]] = [0, 0, 255]
    out_img[nonzeroy[right_lane_inds], nonzerox[right_lane_inds]] = [255, 0, 0]
    
    leftx, lefty = nonzerox[left_lane_inds], nonzeroy[left_lane_inds]
    rightx, righty = nonzerox[right_lane_inds], nonzeroy[right_lane_inds]
    
    return leftx, lefty, rightx, righty, out_img

def fit_polynomial(img_height, leftx, lefty, rightx, righty, out_img):
    left_fit, right_fit = None, None
    left_fitx, right_fitx = None, None
    ploty = np.linspace(0, img_height - 1, img_height)

    if len(leftx) > 10:
        left_fit = np.polyfit(lefty, leftx, 2)
        left_fitx = left_fit[0]*ploty**2 + left_fit[1]*ploty + left_fit[2]
        pts_left = np.array([np.transpose(np.vstack([left_fitx, ploty]))], np.int32)
        cv2.polylines(out_img, pts_left, False, (0, 255, 255), 4)

    if len(rightx) > 10:
        right_fit = np.polyfit(righty, rightx, 2)
        right_fitx = right_fit[0]*ploty**2 + right_fit[1]*ploty + right_fit[2]
        pts_right = np.array([np.transpose(np.vstack([right_fitx, ploty]))], np.int32)
        cv2.polylines(out_img, pts_right, False, (0, 255, 255), 4)

    return left_fit, right_fit, left_fitx, right_fitx, ploty, out_img


if __name__ == "__main__":
    cap = cv2.VideoCapture('test6.mp4') 
    
    prev_vp = None
    view_mode = ord('6') # Mặc định mở ở Dashboard tổng hợp
    THRESHOLD_VALUE = 105 
    static_bottom_y = int(FRAME_HEIGHT * BOTTOM_Y_PERCENTAGE)

    print("🚀 ĐÃ KÍCH HOẠT HỆ THỐNG GIAO DIỆN FULL TÍNH NĂNG!")
    print("[1] Canny Edges (Viền Canny)")
    print("[2] Dynamic ROI (Vùng ROI động)")
    print("[3] Vanishing Point (Điểm tụ)")
    print("[4] Ảnh BEV (Bird's Eye View)")
    print("[5] Biểu đồ Histogram")
    print("[6] Dashboard (Histogram + Sliding Window + Polynomial)")

    while True:
        ret, frame = cap.read()
        if not ret: 
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        
        base_mask = get_base_mask(FRAME_WIDTH, FRAME_HEIGHT, static_bottom_y)
        final_mask, gamma_val, mean_bright = process_frame_pipeline(frame, threshold=THRESHOLD_VALUE)
        
        edges = cv2.Canny(final_mask, 50, 150)
        masked_edges = cv2.bitwise_and(edges, base_mask)
        lines = cv2.HoughLinesP(masked_edges, 1, np.pi/180, threshold=40, minLineLength=15, maxLineGap=40)
        left_lines, right_lines = classify(lines, FRAME_WIDTH)
        vp = find_vanishing_point(left_lines, right_lines, FRAME_WIDTH, FRAME_HEIGHT)
        
        if vp is not None:
            if prev_vp is None: prev_vp = vp
            else:
                dist = math.hypot(vp[0] - prev_vp[0], vp[1] - prev_vp[1])
                alpha = min(0.8, max(0.05, dist / 200.0))
                vp = (int(alpha * vp[0] + (1 - alpha) * prev_vp[0]), 
                      int(alpha * vp[1] + (1 - alpha) * prev_vp[1]))
                prev_vp = vp
        else:
            if prev_vp is not None: vp = prev_vp
                
        polygon = get_roi_polygon(FRAME_WIDTH, FRAME_HEIGHT, vp, static_bottom_y)
        
        # --- LUỒNG DỮ LIỆU NÂNG CAO ---
        clean_binary = cv2.bitwise_and(final_mask, base_mask)
        warped_mask, M, Minv = bird_eye_view(clean_binary)
        histogram, leftx_base, rightx_base = get_histogram_peaks(warped_mask)
        leftx, lefty, rightx, righty, sliding_window_img = sliding_window(warped_mask, leftx_base, rightx_base)
        
        left_fit, right_fit, left_fitx, right_fitx, ploty, poly_img = fit_polynomial(
            warped_mask.shape[0], leftx, lefty, rightx, righty, sliding_window_img)
        
        # ---------------------------------------------------------
        # CHUYỂN MẠCH GIAO DIỆN HIỂN THỊ
        # ---------------------------------------------------------
        display_frame = np.zeros_like(frame)

        if view_mode == ord('1'):
            display_frame = cv2.cvtColor(masked_edges, cv2.COLOR_GRAY2BGR)
            cv2.putText(display_frame, "1. Masked Canny Edges", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        elif view_mode == ord('2'):
            black_mask = np.zeros_like(frame)
            cv2.fillPoly(black_mask, [polygon], (255, 255, 255))
            display_frame = cv2.bitwise_and(frame, black_mask)
            cv2.polylines(display_frame, [polygon], True, (0, 255, 0), 2) 
            cv2.putText(display_frame, "2. Dynamic ROI", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        elif view_mode == ord('3'):
            display_frame = frame.copy()
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    if x1==x2: continue
                    m = (y2-y1)/(x2-x1)
                    if abs(m)<0.5 or abs(m)>2.5: continue
                    color = (255, 0, 0) if m < 0 else (0, 0, 255)
                    cv2.line(display_frame, (x1, y1), (x2, y2), color, 4)
                    if vp is not None:
                        cv2.line(display_frame, (x2, y2), vp, (0, 255, 0), 1)
            if vp is not None:
                cv2.circle(display_frame, vp, 10, (0, 255, 255), -1)
            cv2.putText(display_frame, "3. Vanishing Point & Hough Lines", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        elif view_mode == ord('4'):
            display_frame = cv2.cvtColor(warped_mask, cv2.COLOR_GRAY2BGR)
            cv2.putText(display_frame, "4. Bird's Eye View (BEV)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        elif view_mode == ord('5'):
            display_frame = draw_matplotlib_style_dashboard(warped_mask, histogram, leftx_base, rightx_base)

        elif view_mode == ord('6'):
            hist_visual = draw_matplotlib_style_dashboard(warped_mask, histogram, leftx_base, rightx_base)
            h_hist = hist_visual.shape[0]
            sw_resized = cv2.resize(poly_img, (int(h_hist * FRAME_WIDTH / FRAME_HEIGHT), h_hist))
            
            combined = np.hstack((hist_visual, sw_resized))
            display_frame = cv2.resize(combined, (1400, 700))
        # Thông số chung cho các chế độ không phải Dashboard
        if view_mode not in [ord('5'), ord('6')]: 
            info_text = f"Luma: {mean_bright:.1f} | Gamma: {gamma_val:.2f}"
            cv2.putText(display_frame, info_text, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow("Advanced LDW Pipeline", display_frame)

        key = cv2.waitKey(30) & 0xFF
        if key == ord('q'): 
            break
        elif key in [ord('1'), ord('2'), ord('3'), ord('4'), ord('5'), ord('6')]:
            view_mode = key 

    cap.release()
    cv2.destroyAllWindows()