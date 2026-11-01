# Sổ Tay Quy Trình Làm Việc Studio & Retoucher - NenAI Studio v8.1 PRO
> **Hướng dẫn chuẩn hóa quy trình chụp ảnh phông trắng và cẩm nang hậu kỳ Photoshop dành cho thợ ảnh & chuyên viên Retouch chuyên nghiệp**

---

## 1. Chuẩn Hóa Khâu Chụp Ảnh Phông Trắng / Phông Xám Tại Studio

Để AI trích xuất chi tiết dâu rể sắc nét từng sợi tóc và tái tạo ánh sáng chân thực nhất:

| Yếu tố | Hướng dẫn chuẩn Studio | Những điều TUYỆT ĐỐI NÊN TRÁNH |
| :--- | :--- | :--- |
| **Phông nền** | Sử dụng phông giấy trắng không nhăn (*Seamless White*) hoặc phông xám trung tính (*Neutral Grey 18%*). | Tránh phông bị rách, nhăn nhúm nặng hoặc dơ bẩn đen kịt sát chân váy cưới. |
| **Khoảng cách** | Đặt Dâu – Rể cách phông nền tối thiểu **1.8m – 2.5m**. | Tránh đứng quá sát phông khiến ánh sáng đèn nền đánh ngược vào làm "cháy" viền áo vest chú rể. |
| **Khăn voan** | Trải nhẹ tà voan tự nhiên sang hai bên vai hoặc thả dài phía sau, tạo độ phồng nhẹ. | Tránh để voan bị vón cục dày đặc hoặc xếp quá nhiều nếp đè chồng lên nhau. |
| **Ánh sáng chụp** | Sử dụng Softbox lớn (Octabox 120cm hoặc 150cm) đánh sáng tản mềm dịu, tỷ lệ tương phản nhẹ nhàng. | Tránh dùng đèn gắt (hard light chóa trần) tạo bóng đen kịt ngay dưới hốc mắt và mũi cô dâu. |
| **Mặt sàn tiếp đất** | Cho tà váy cô dâu tiếp đất êm ái trên sàn; chú rể đứng vững hai chân thẳng trục ống kính. | Tránh chụp góc xiên quá cao từ trên xuống làm ngắn chân dâu rể. |

---

## 2. Tiêu Chuẩn Phân Loại Theo Cự Ly Chụp (Framing Intelligence)

NenAI v8.1 PRO tự động điều chỉnh thuật toán xử lý theo 3 cự ly chụp trên bảng điều khiển:

```text
┌────────────────────────────────────────────────────────────────────────┐
│  [1] TOÀN THÂN (Full-body)                                             │
│  - Giữ nguyên mặt sàn tiếp đất, tự động kích hoạt Bóng Tiếp Xúc Sàn    │
│    (3-Tier Contact Shadow) và Phản xạ bóng gương mờ (Specular Floor).  │
│  - Bố trí khóm hoa tiền cảnh ôm hai bên mép váy.                       │
├────────────────────────────────────────────────────────────────────────┤
│  [2] BÁN THÂN (Half-body)                                              │
│  - Tự động lược bỏ mặt sàn, tập trung vào lưng tường và hoa ngang eo.  │
│  - Xóa phông quang học nhẹ (f/2.0 Depth of Field), quầng sáng viền vai.│
├────────────────────────────────────────────────────────────────────────┤
│  [3] CHÂN DUNG CẬN CẢNH (Close-up Portrait)                            │
│  - TUYỆT ĐỐI KHÔNG mô tả cảnh vật/sàn rườm rà gây rối mắt.             │
│  - Tự động chuyển nền thành Bokeh tản nhuyễn hoặc Phông loang mỹ thuật │
│    (Fine-art Mottled Canvas) màu be/xám kem chuẩn Hàn Quốc.            │
│  - Tập trung 100% Beauty Lighting: Tôn mịn da và Catchlight mắt.       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Khai Thác Kho Lưu Trữ Bối Cảnh Ghép Sẵn (Studio Vault)

### 3.1. Danh mục 4 bối cảnh chuẩn Studio tích hợp sẵn
1. **Hàn Quốc Botanical Sunlight (`korean_baby_flowers_01`):** Nắng xiên cửa sổ Gobo ấm áp, hoa rum trắng và lá khuynh diệp ôm sát tà váy, sàn màu be kem thanh lịch.
2. **Vòm Hoa Cẩm Thạch Luxury (`palace_gold_02`):** Sàn đá cẩm thạch bóng phản chiếu bóng gương đế giày, vòm lan hồ điệp cao 2.4m phong cách sang trọng.
3. **Sảnh Nắng Cổ Điển (`fineart_mottled_03`):** Cửa vòm kính đón nắng chiều vàng kem, kiến trúc đối xứng tôn vinh trang phục cưới hoàng gia.
4. **Sảnh Cung Điện Châu Âu (`sanh_cung_dien_chau_au_04`):** Kiến trúc vòm cổ điển trang nhã, ánh sáng khuếch tán dịu nhẹ.

### 3.2. Quy trình lưu mẫu mới vào kho
- Khi bạn tải lên một ảnh nền đẹp từ Pinterest/TikTok hoặc tự chụp:
- Bấm nút **`💾 Lưu Bối Cảnh Vào Kho`** trên bảng điều khiển Panel $\rightarrow$ Nhập tên mẫu (ví dụ: `Hàn Quốc Hoa Baby Studio`).
- Hệ thống sẽ tự động bóc tách màu sàn, màu tường, hướng sáng và tạo ảnh thumbnail lưu vào kho.
- Với các cặp đôi tiếp theo, bạn chỉ việc chọn mẫu này $\rightarrow$ **Kết xuất hoàn thiện chỉ trong 2 – 3 giây!**

---

## 4. Quản Lý & Tinh Chỉnh Cấu Trúc 5 Layer Trong Adobe Photoshop 2026

Khi bạn bấm **`⚡ ĐẨY BẢN MASTER 33MP VÀO PHOTOSHOP (1-CLICK)`**, NenAI sẽ tự động nạp cấu trúc layer chuyên nghiệp vào file PSD đang làm việc:

```text
📁 [NenAI v3.0 - Studio Wedding 33MP]
│
├── 👁️ [Layer 1] [Tiền Cảnh] Cành Hoa Ôm Mép Váy (Normal 100%)
│    └── Tác dụng: Tạo chiều sâu không gian 3D (Hoa tiền cảnh che nhẹ lên tà váy cưới).
│
├── 👁️ [Layer 2] [Ánh Sáng] Light Wrap Kem Ấm (Soft Light 38%)
│    └── Tác dụng: Quầng sáng viền tự nhiên ôm lấy bờ vai, tóc mai và lớp ren váy cưới.
│
├── 👁️ [Layer 3] [33MP Gốc] Dâu Rể & Voan Cưới (Pixel-Lock) (Normal 100%)
│    └── Tác dụng: Chủ thể Dâu Rể đã tách nền bằng BiRefNet, giữ 100% độ sắc nét ống kính gốc.
│
├── 👁️ [Layer 4] [Bóng Thật] Bóng Gấu Váy Gốc (Multiply) (Multiply 100%)
│    └── Tác dụng: Lớp bóng tiếp xúc sàn 3 tầng chân thực, váy bám chắc mặt đất không lơ lửng.
│
├── 👁️ [Layer 5] [AI Nền] Bối Cảnh Hoa & Nắng Gobo 33MP (Normal 100%)
│    └── Tác dụng: Tấm nền bối cảnh nguyên bản độ phân giải cao đã được chỉnh phối cảnh.
│
└── 🔒 [Layer 0] [Bản Gộp Master] Hoàn Thiện 33MP (Normal 100% - Đang ẩn)
     └── Bản xem trước gộp sẵn dự phòng đối chiếu hoặc xuất nhanh cho khách duyệt.
```

---

## 5. Mẹo Hậu Kỳ Chuyên Sâu Dành Cho Retoucher (Pro Tips)

### Mẹo 1: Nắn dáng Liquify & Làm mịn da không làm méo nền
- Chọn **`[Layer 3] [33MP Gốc] Dâu Rể & Voan Cưới`**.
- Mở menu **Filter $\rightarrow$ Liquify** để bóp eo cô dâu, chỉnh vai chú rể hoặc chạy plugin làm mịn da (Portraiture / Retouch4me).
- 👉 *Lợi ích:* Vì chủ thể nằm ở một Layer riêng biệt, bạn có thể nắn dáng thoải mái mà **hoàn toàn không làm cong vênh các đường thẳng phào chỉ tường hay hoa ở nền phía sau!**

### Mẹo 2: Điều chỉnh cường độ nắng viền (Light-Wrap)
- Chọn **`[Layer 2] [Ánh Sáng] Light Wrap Kem Ấm`**.
- Thay đổi thanh trượt **Opacity**:
  - Đặt **25% – 35%**: Ánh sáng dịu nhẹ phong cách trong trẻo Hàn Quốc.
  - Đặt **45% – 60%**: Nắng viền rực rỡ phong cách điện ảnh hoàng hôn.

### Mẹo 3: Điều chỉnh bóng đổ sàn theo chất liệu sàn
- Chọn **`[Layer 4] [Bóng Thật] Bóng Gấu Váy Gốc (Multiply)`**.
- Với sàn gỗ tối màu: Giữ nguyên Opacity 100%.
- Với sàn đá trắng tinh hoặc gạch men bóng sáng: Hạ Opacity xuống **70% – 80%** để bóng mờ nhẹ nhàng, thanh thoát hơn.

### Mẹo 4: Tạo chiều sâu 3D đa lớp bằng cọ Brush
- Chọn Layer Mask của **`[Layer 1] [Tiền Cảnh] Cành Hoa Ôm Mép Váy`**.
- Dùng cọ mềm màu đen (Opacity 30%) quét nhẹ ở những cành hoa bạn muốn ẩn đi để lộ thêm tà váy cưới, hoặc tô cọ trắng để khóm hoa che thêm lên chân váy.
- Bức ảnh sẽ ngay lập tức đạt chiều sâu quang học 3 lớp tiêu chuẩn: **Hoa tiền cảnh $\rightarrow$ Váy cưới $\rightarrow$ Hoa hậu cảnh $\rightarrow$ Vách tường**.

---

## 6. Xử Lý Sự Cố Thường Gặp (Troubleshooting)

1. **Panel báo "Chưa kết nối Photoshop":**
   - Đảm bảo bạn đã mở sẵn một tài liệu ảnh cưới trong Photoshop 2026.
   - Bấm vào biểu tượng chữ **`N`** màu vàng ở góc trên bên trái Panel để làm mới kết nối.
2. **Giao diện Panel cần cập nhật mới:**
   - NenAI hỗ trợ cơ chế Live Hot-Reload. Bạn chỉ cần bấm vào chữ **`N`** (Gold Brand Icon), Panel sẽ tự nạp lại mã HTML/CSS mới tức thì mà không cần đóng Photoshop.
3. **Server Backend chưa chạy:**
   - Nhấp đúp vào file `NenAI_Studio.command` trên màn hình Desktop hoặc chạy `./run_app.sh` trong Terminal.
