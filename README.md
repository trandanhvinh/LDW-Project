# 🚗 Hệ Thống Cảnh Báo Lệch Làn Đường (LDW - Lane Departure Warning)

![Demo Output](img/output.gif)

Dự án xây dựng hệ thống Cảnh báo lệch làn đường (Lane Departure Warning - LDW) theo thời gian thực sử dụng các thuật toán xử lý ảnh truyền thống (Computer Vision), được tối ưu hóa để hoạt động mượt trên cả máy tính cá nhân (PC) và máy tính nhúng Raspberry Pi theo kiến trúc đa luồng.

---

## Tính năng

* Thích nghi trên nhiều điều kiện ánh sáng: Tự động đo độ sáng của mặt đường (Luma) và nội suy hệ số Adaptive Gamma Correction, kết hợp cân bằng sáng cục bộ CLAHE trên không gian màu LAB và lọc hình thái học (Morphological Filtering).
* Vùng quan tâm động (Dynamic ROI): Tự động phát hiện và masking ra vùng hình thang trước mũi xe co giãn bám theo Điểm tụ (Vanishing Point) bằng phép biến đổi Hough và bộ lọc làm mượt, giúp vùng ROI tự động xoay/nghiêng theo khúc cua hoặc độ dốc mặt đường.
* Góc nhìn chim bay từ trên xuống (Bird's Eye View - BEV): Áp dụng biến đổi phối cảnh đưa làn đường về dạng 2D song song để đo đạc hình học chính xác.
* Nội suy và kẻ vạch làn đường: 
  * Kết hợp thuật toán Spatial Histogram, Sliding Window và Polynomial Fitting dựa trên phương trình căn thức bậc 2 để tăng tốc độ trích xuất điểm ảnh.
  * Sử dụng thuật toán RANSAC (Random Sample Consensus) kết hợp lấy mẫu thưa để tìm đa thức bậc 2 chuẩn xác, loại bỏ đi các điểm nhiễu từ vệt nắng, bóng cây, mũi tên chỉ đường trên làn.
  * Bộ đệm LaneTracker làm mượt đường cong qua nhiều khung hình và tự động phát hiện trạng thái chuyển làn.
* UI cảnh báo: Tính toán bán kính cong thực tế - R (mét), độ lệch tâm xe so với giữa làn - offset (mét) và duy trì cảnh báo trên màn hình khi phát hiện xe đè vạch.
* Tối ưu hóa cho hệ thống nhúng (Raspberry Pi): Kiến trúc 3 luồng độc lập chia thành 3 tác vụ chính là đọc video, xử lý pipeline thuật toán Computer Vision và ghi video/log CSV ra bộ nhớ của máy, giúp giảm đi hiện tượng nghẽn cổ chai I/O.

---

## Quy trình thuật toán (Pipeline Architecture)

Hệ thống được chia thành 6 bước xử lý tuần tự trong thư mục `pipeline/`:

1. `step1_preprocessing.py`: Chuyển đổi ảnh đầu vào (640x360), tự động chỉnh sáng Gamma vùng mặt đường, tách kênh L (LAB), tăng độ tương phản CLAHE, phân ngưỡng thích nghi (Adaptive Threshold) và khử nhiễu ngang/dọc bằng Morphology.
2. `step2_dynamic_roi.py`: Lọc biên Canny trong vùng mặt nạ cơ sở, tìm đoạn thẳng bằng `HoughLinesP`, phân loại vạch trái/phải theo độ dốc để tìm giao điểm (Vanishing Point) và dựng hình thang Dynamic ROI.
3. `step3_birdseye_view.py`: Chuyển đổi vùng Dynamic ROI sang mặt phẳng 2D nhìn từ trên xuống (BEV) và lưu lại ma trận nghịch đảo `Minv`.
4. `step4_5_lane_detection.py`: Quét cửa sổ trượt hoặc tìm kiếm quanh đa thức cũ, vẽ đường cong bậc hai bằng RANSAC khớp với làn đường và làm mượt thông qua `LaneTracker`.
5. `step6_display.py`: Quy đổi từ đơn vị pixel sang mét thực tế, tính bán kính cong R, khoảng cách lệch tâm offset và hiển thị ngược vùng làn đường về góc nhìn camera gốc.

---

## Yêu cầu về môi trường
1. **Clone repository về máy:**
   ```bash
   git clone https://github.com/trandanhvinh/LDW-Project
   cd <ten-repo>
![Requirements](requirements.txt)

2. **Tạo môi trường ảo**
    ```bash
    python -m venv venv
    # Kích hoạt trên Windows:
    venv\Scripts\activate
    # Kích hoạt trên Linux / macOS / Raspberry Pi:
    source venv/bin/activate

2. **Cài đặt các thư viện**
    ```bash
    pip install numpy opencv-python-headless
    pip install -r requirements.txt

---
Cần thêm các video để test, hãy truy cập vào link sau: https://drive.google.com/drive/u/0/folders/1UWewQTCyxKDvsnVRkl_zQIcmTD8WyAzz
