import time
import math
import matplotlib.pyplot as plt
from step7_pid_control import PIDController

def simulate_car_pid(Kp, Ki, Kd, speed_m_s=1.0, duration_sec=10.0, dt=0.05):
    """
    Giả lập xe chạy và điều khiển bám làn bằng PID
    """
    pid = PIDController(Kp=Kp, Ki=Ki, Kd=Kd)
    
    # Khởi tạo trạng thái của xe ảo
    car_offset = 0.5      # Cố tình đặt xe lệch 0.5 mét so với tâm làn
    car_heading = 0.0     # Góc lệch thân xe (Radian)
    wheelbase = 0.2       # Chiều dài cơ sở của xe mô hình (20cm)
    
    time_steps = []
    offsets = []
    steering_angles = []
    
    # Giả lập vòng lặp thời gian thực
    for step in range(int(duration_sec / dt)):
        current_time = step * dt
        
        # 1. Thuật toán "nhìn" thấy độ lệch và gọi PID
        # Vì xe đang nằm bên phải vạch (offset > 0), ta truyền "Right"
        direction = "Right" if car_offset > 0 else "Left"
        
        # Giả lập thời gian trôi qua cho khâu I và D
        pid.prev_time = time.time() - dt 
        
        # PID tính toán góc bẻ lái (Degree)
        servo_angle = pid.compute(abs(car_offset), direction)
        
        # 2. Quy đổi góc Servo sang góc bẻ bánh xe vật lý
        # Giả sử: Servo 90 độ -> bánh xe thẳng (0 rad)
        # Servo 60 độ -> bánh xe rẽ trái (-30 độ)
        steering_deg = servo_angle - 90
        steering_rad = math.radians(steering_deg)
        
        # 3. Phương trình Động học xe đạp (Kinematic Bicycle Model)
        # Cập nhật hướng xe (Heading) và Vị trí ngang (Offset)
        car_heading += (speed_m_s / wheelbase) * math.tan(steering_rad) * dt
        car_offset += speed_m_s * math.sin(car_heading) * dt
        
        # Lưu trữ dữ liệu để vẽ biểu đồ
        time_steps.append(current_time)
        offsets.append(car_offset)
        steering_angles.append(servo_angle)
        
    return time_steps, offsets, steering_angles

# ==========================================
# THỬ NGHIỆM TÌM THÔNG SỐ (HEURISTIC TUNING)
# ==========================================

# Kịch bản 1: Chỉ có Kp (Sẽ thấy xe lắc lư văng đuôi - hình sin)
t, off1, _ = simulate_car_pid(Kp=80, Ki=0, Kd=0)

# Kịch bản 2: Thêm Kd để giảm chấn (Sẽ thấy xe lướt mượt vào tâm)
t, off2, _ = simulate_car_pid(Kp=80, Ki=0, Kd=30)

# Kịch bản 3: Tối ưu thông số (Bám làn nhanh nhất)
t, off3, _ = simulate_car_pid(Kp=100, Ki=0, Kd=50)

t, off4, _ = simulate_car_pid(Kp=120, Ki=0, Kd=70)

# Vẽ biểu đồ Đánh giá
plt.figure(figsize=(10, 6))
plt.plot(t, off1, label='Kp=80, Kd=0', linestyle='--')
plt.plot(t, off2, label='Kp=80, Kd=30')
plt.plot(t, off3, label='Kp=100, Kd=50', linewidth=2)
plt.plot(t, off4, label='Kp=120, Kd=70')

plt.axhline(0, color='red', label='Tâm làn đường', linewidth=1)
plt.xlabel("Thời gian (s)")
plt.ylabel("Offset (mét)")
plt.legend()
plt.grid(True)
plt.show()