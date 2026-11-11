import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import glob

# =================================================================
# CẤU HÌNH GIAO DIỆN ĐỒ THỊ CHUẨN BÁO CÁO KHOA HỌC
# =================================================================
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13

def draw_detailed_groups(target_csv_file):
    log_name = os.path.splitext(target_csv_file)[0].upper()
    print(f"\n📊 Đang xử lý dòng thời gian cho file: {target_csv_file}...")
    
    # Đọc dữ liệu từ file log chỉ định
    df = pd.read_csv(target_csv_file)
    
    # -------------------------------------------------------------
    # NHÓM 1: ĐỒ THỊ TỐC ĐỘ XỬ LÝ (FPS) TỐI GIẢN (Đã bỏ Latency)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 4.5))
    
    # Vẽ đồ thị FPS tức thời
    ax.plot(df['Frame_ID'], df['Instant_FPS'], color='#1f77b4', alpha=0.7, linewidth=1.5, label='FPS tức thời')
    avg_fps = df['Instant_FPS'].mean()
    ax.axhline(avg_fps, color='#d62728', linestyle='--', linewidth=2, label=f'FPS trung bình ({avg_fps:.1f})')
    
    ax.set_xlabel('Khung hình (Frame ID)', labelpad=8)
    ax.set_ylabel('Tốc độ xử lý (FPS)', labelpad=8)
    ax.set_title(f'NHÓM 1: ĐỒ THỊ BIẾN THIÊN TỐC ĐỘ XỬ LÝ FPS - {log_name}', fontweight='bold', pad=12)
    ax.legend(loc='upper right')
    ax.grid(True, linestyle=':', alpha=0.5)
    
    fig.tight_layout()
    fig.savefig(f'{target_csv_file.replace(".csv", "")}_nhom1_fps.png', dpi=300)
    plt.close(fig)
    print(f"  ✔️ Đã lưu đồ thị Nhóm 1: {target_csv_file.replace('.csv', '')}_nhom1_fps.png")

    # -------------------------------------------------------------
    # NHÓM 3: ĐỒ THỊ GIÁM SÁT SỬ DỤNG TÀI NGUYÊN PHẦN CỨNG (CPU & RAM)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(df['Frame_ID'], df['CPU_Usage(%)'], color='#e377c2', linewidth=1.5, label='Chiếm dụng CPU (%)')
    ax.plot(df['Frame_ID'], df['RAM_Usage(%)'], color='#7f7f7f', linewidth=2, label='Chiếm dụng RAM (%)')
    
    avg_cpu = df['CPU_Usage(%)'].mean()
    avg_ram = df['RAM_Usage(%)'].mean()
    ax.axhline(avg_cpu, color='#e377c2', linestyle=':', linewidth=2, label=f"CPU trung bình ({avg_cpu:.1f}%)")
    ax.axhline(avg_ram, color='#7f7f7f', linestyle=':', linewidth=2, label=f"RAM trung bình ({avg_ram:.1f}%)")
    
    ax.set_title(f'NHÓM 3: MỨC TIÊU THỤ TÀI NGUYÊN PHẦN CỨNG RASPBERRY PI 4 - {log_name}', fontweight='bold', pad=12)
    ax.set_xlabel('Khung hình (Frame ID)')
    ax.set_ylabel('Tỷ lệ chiếm dụng tài nguyên (%)')
    ax.set_ylim(0, 100)
    ax.legend(loc='lower left')
    ax.grid(True, linestyle=':', alpha=0.5)
    
    fig.tight_layout()
    fig.savefig(f'{target_csv_file.replace(".csv", "")}_nhom3_hardware.png', dpi=300)
    plt.close(fig)
    print(f"  ✔️ Đã lưu đồ thị Nhóm 3: {target_csv_file.replace('.csv', '')}_nhom3_hardware.png")


def draw_group2_stacked_bar_comparison():
    # Tự động tìm tất cả các file dữ liệu thực nghiệm của Pi trong thư mục
    log_files = sorted(glob.glob("pi_adas_log*.csv"))
    if not log_files:
        print("❌ Lỗi: Không tìm thấy file dữ liệu pi_adas_log nào để lập biểu đồ gộp!")
        return

    print("\n📊 Đang xử lý tính toán đồ thị gộp Nhóm 2 so sánh cả 5 lượt thử nghiệm...")
    avg_data = []
    log_names = []
    
    for f in log_files:
        df = pd.read_csv(f)
        name = os.path.splitext(f)[0].upper().replace("PI_ADAS_", "")
        log_names.append(name)
        avg_data.append([
            df['PreProcess_ms'].mean(),
            df['ROI_BEV_ms'].mean(),
            df['RANSAC_ms'].mean(),
            df['HUD_ms'].mean()
        ])

    df_avg = pd.DataFrame(avg_data, columns=['PreProcess', 'ROI_BEV', 'RANSAC', 'HUD'], index=log_names)

    # Khởi tạo bản vẽ cột chồng Nhóm 2 tổng hợp
    fig, ax = plt.subplots(figsize=(10, 6.5))
    df_avg.plot(kind='bar', stacked=True, ax=ax, color=['#2ca02c', '#d62728', '#9467bd', '#8c564b'], width=0.55)
    
    ax.set_title('NHÓM 2: SO SÁNH PHÂN BỔ THỜI GIAN ĐỘ TRỄ TRUNG BÌNH GIỮA CÁC LƯỢT CHẠY', fontweight='bold', pad=15)
    ax.set_xlabel('Lượt chạy thử nghiệm hệ thống (Log File)', labelpad=10)
    ax.set_ylabel('Thời gian xử lý trung bình của từng Frame (ms)', labelpad=10)
    ax.set_xticklabels(log_names, rotation=0)
    ax.grid(True, axis='y', linestyle=':', alpha=0.5)

    # Ghi chữ thông số mili-giây đè lên từng phân khúc màu của cột
    for i, (idx, row) in enumerate(df_avg.iterrows()):
        cumulative = 0
        for col in df_avg.columns:
            val = row[col]
            if val > 0.5:
                ax.text(i, cumulative + val/2, f"{val:.1f} ms", ha='center', va='center', color='white', fontweight='bold', fontsize=9)
            cumulative += val
        # In tổng thời gian chu kỳ máy ở đỉnh mỗi cột
        ax.text(i, cumulative + 2, f"Tổng:\n{cumulative:.1f} ms", ha='center', va='bottom', fontweight='bold', fontsize=9.5, color='black')

    # Đã sửa: Nới rộng trục Y lên 1.35 lần tổng chiều cao của cột lớn nhất để tạo khoảng không chứa Legend
    ax.set_ylim(0, max(df_avg.sum(axis=1)) * 1.35)

    # Hiển thị bảng chú thích
    ax.legend(labels=['1. Tiền xử lý ảnh', '2. Tìm Điểm tụ & BEV', '3. Cửa sổ trượt & RANSAC', '4. HUD & Giao diện đồ họa'], loc='upper right')
    
    fig.tight_layout()
    fig.savefig('nhom2_stacked_bar_comparison.png', dpi=300)
    plt.close(fig)
    print("  ✔️ Đã xuất thành công biểu đồ gộp Nhóm 2: nhom2_stacked_bar_comparison.png\n")


# =================================================================
# KHU VỰC THỰC THI CHƯƠNG TRÌNH
# =================================================================
if __name__ == "__main__":
    # 1. Đo chi tiết dòng thời gian cho file chạy cụ thể (Nhóm 1 & Nhóm 3)
    draw_detailed_groups(target_csv_file="pi_adas_log3.csv")
    
    # 2. Tạo biểu đồ cột chồng Nhóm 2 gộp phân bổ thời gian của cả 5 file chạy thử nghiệm
    draw_group2_stacked_bar_comparison()
    
    print("🚀 HOÀN THÀNH XUẤT ĐỒ THỊ CẬP NHẬT CHUẨN ĐỒ ÁN!")