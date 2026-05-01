# Business Suite Odoo 16

Hệ thống phân tích hóa đơn và quản lý sổ sách kế toán cho **Hộ kinh doanh (HKD)** tích hợp trên nền tảng Odoo.

---

## Mục lục

- [Tổng quan](#tổng-quan)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt](#cài-đặt)
- [Cấu hình](#cấu-hình)
- [Module HKD Dashboard](#module-hkd-dashboard)
- [Module HKD MRP](#module-hkd-mrp)
- [Module HKD Purchase](#module-hkd-purchase)
- [Module HKD Sales](#module-hkd-sales)
- [Module HKD Tax Policy](#module-hkd-tax-policy)
- [Module HKD Statements](#module-hkd-statements)
- [Hướng dẫn sử dụng](#hướng-dẫn-sử-dụng)
- [Cấu trúc dự án](#cấu-trúc-dự-án)

---

## Tổng quan

Business Suite Odoo 16 là hệ thống giúp hộ kinh doanh:

- Theo dõi doanh thu, chi phí theo kỳ
- Quản lý nhập/xuất/tồn kho vật tư hàng hoá
- Theo dõi tiền mặt và tiền gửi ngân hàng
- Tính thuế TNCN, GTGT tự động

---

## Yêu cầu hệ thống

| Thành phần | Phiên bản |
|---|---|
| Docker | >= 20.x |
| Docker Compose | >= 2.x |
| Odoo | 16.0 |
| PostgreSQL | 15 |
| Python | 3.10+ |

---

## Cài đặt

### 1. Clone repository
```bash
git clone https://github.com/Toan050704/odoo-16-business-suite.git
cd odoo-16-business-suite
```

### 2. Cấu hình biến môi trường
```bash
cp .env.example .env
```

Chỉnh sửa `.env` nếu cần:
```env
ODOO_DB=odoo
ODOO_USER=odoo
ODOO_PASSWORD=odoo
POSTGRES_PASSWORD=odoo
```

### 3. Khởi động hệ thống
```bash
docker compose up -d
```

Hệ thống sẽ khởi động 2 container:

| Container | Mô tả | Port |
|---|---|---|
| `odoo_web` | Odoo application | 10020 |
| `odoo_db` | PostgreSQL database | 5432 |

Truy cập: [http://localhost:10020](http://localhost:10020)

### 4. Dừng hệ thống
```bash
docker compose down
```

### 5. Xem logs
```bash
docker compose logs -f web
```

### 6. Upgrade module sau khi thay đổi code
```bash
docker compose restart web
```
Sau đó vào **Settings → Apps → HKD Statements → Upgrade**

---

## Docker

### Dùng image Odoo có sẵn *(mặc định)*

```yaml
services:
    web:
        image: odoo:16.0
        container_name: odoo_web
        ...
    db:
        image: postgres:15
        container_name: odoo_db
        ...
```

### Dùng Dockerfile custom *(nếu cần cài thêm packages)*

Tạo file `Dockerfile` trong thư mục gốc:

```dockerfile
FROM odoo:16.0

USER root
RUN pip3 install --break-system-packages \
    openai \
    anthropic

USER odoo
```

Rồi đổi trong `docker-compose.yml`:
```yaml
web:
    build: .        # thay vì image: odoo:16.0
```

Chạy lại:
```bash
docker compose up -d --build
```

---

## Cấu hình

Các bước bắt buộc phải thực hiện trước khi sử dụng:

### 1. Chart of Accounts (Hệ thống tài khoản)
```
Accounting → Configuration → Chart of Accounts
→ Cài đặt: Vietnamese Accounting (VN)
```

### 2. Journal (Sổ quỹ)
```
Accounting → Configuration → Journals
```
| Journal | Type |
|---|---|
| Tiền mặt | `Cash` |
| Ngân hàng | `Bank` |

### 3. Location (Kho hàng)
```
Inventory → Configuration → Locations
```
| Location | Usage |
|---|---|
| Kho nội bộ | `Internal` |
| Nhà cung cấp | `Vendor` |
| Khách hàng | `Customer` |

### 4. Automated Valuation
```
Inventory → Configuration → Settings
→ Valuation → Automated Valuation: Bật
```

### 5. Costing Method
```
Inventory → Configuration → Product Categories
→ Costing Method: Average Cost (AVCO)
```

### 6. Thuế TNCN
```
Accounting → Configuration → Taxes
→ Tạo thuế TNCN 1.5% cho HKD
```

---

## Module HKD Dashboard

Module `hkd_dashboard` là màn hình tổng quan điều hành của hệ thống HKD. Module này tập trung các số liệu quan trọng nhất để người dùng có thể theo dõi tình hình kinh doanh nhanh chóng ngay khi đăng nhập hệ thống.

### Chức năng chính
- Hiển thị dashboard tổng quan cho hoạt động kinh doanh
- Tập trung các chỉ số, biểu đồ và thông tin điều hành
- Hỗ trợ truy cập nhanh đến các phân hệ HKD khác

---

## Module HKD MRP

Module `hkd_mrp` phục vụ nghiệp vụ sản xuất cho hộ kinh doanh, đặc biệt phù hợp với các đơn vị có quy trình chế biến hoặc tạo ra thành phẩm từ nguyên vật liệu đầu vào. Module giúp quản lý xuyên suốt từ nguyên liệu, công đoạn sản xuất đến thành phẩm hoàn chỉnh.

### Chức năng chính
- Quản lý quy trình sản xuất và lệnh sản xuất
- Theo dõi nguyên vật liệu, bán thành phẩm và thành phẩm
- Hỗ trợ kiểm soát nhu cầu vật tư trong sản xuất

---

## Module HKD Purchase

Module `hkd_purchase` mở rộng nghiệp vụ mua hàng cho hộ kinh doanh, giúp quản lý quá trình đặt mua, nhận hàng và ghi nhận chi phí đầu vào một cách rõ ràng hơn. Module này hỗ trợ việc kiểm soát nguồn cung và phục vụ đối chiếu dữ liệu với kho, công nợ và kế toán.

### Chức năng chính
- Quản lý đơn mua hàng và nhà cung cấp
- Theo dõi nhập hàng, chi phí mua và tình trạng đơn hàng
- Hỗ trợ đồng bộ dữ liệu mua hàng cho các sổ kế toán liên quan

---

## Module HKD Sales

Module `hkd_sales` hỗ trợ nghiệp vụ bán hàng cho hộ kinh doanh, từ bước báo giá, tạo đơn bán đến ghi nhận hóa đơn và doanh thu. Module giúp chuẩn hoá quy trình bán hàng, hạn chế sai sót khi xử lý giao dịch và tổng hợp số liệu bán ra.

### Chức năng chính
- Quản lý báo giá, đơn bán và xác nhận giao dịch
- Theo dõi doanh số bán hàng theo kỳ
- Kết nối dữ liệu bán hàng với các phân hệ kế toán và thống kê

---

## Module HKD Tax Policy

Module `hkd_tax_policy` dùng để thiết lập và quản lý các chính sách thuế áp dụng cho hộ kinh doanh. Module này đóng vai trò chuẩn hoá các quy tắc liên quan đến thuế, giúp việc ghi nhận và tính toán trong toàn hệ thống được đồng nhất hơn.

### Chức năng chính
- Cấu hình chính sách thuế áp dụng cho HKD
- Hỗ trợ thiết lập quy tắc tính thuế theo nghiệp vụ
- Đảm bảo tính nhất quán khi dùng chung với các module kế toán và báo cáo

---

## Module HKD Statements

### Danh sách sổ

| Sổ | Tên | Nguồn dữ liệu | Mô tả |
|---|---|---|---|
| **S2B** | Sổ doanh thu | `account.move` (out_invoice) | Doanh thu bán hàng, thuế GTGT đầu ra |
| **S2C** | Sổ chi phí | `account.move` (in_invoice) | Chi phí hợp lý, chênh lệch, thuế TNCN |
| **S2D** | Sổ vật tư hàng hoá | `stock.move`, `stock.valuation.layer` | Nhập/xuất/tồn kho theo từng sản phẩm |
| **S2E** | Sổ tiền mặt & tiền gửi | `account.payment` | Thu/chi tiền mặt và tiền gửi ngân hàng |

### Sổ S2B — Doanh thu
- Tổng hợp doanh thu từ hóa đơn bán hàng
- Hiển thị thuế GTGT đầu ra
- Lọc theo kỳ báo cáo

### Sổ S2C — Chi phí
- Liệt kê chi tiết từng hóa đơn mua hàng
- Tính chênh lệch: Doanh thu - Chi phí
- Tự động tính thuế TNCN 1.5% trên phần lợi nhuận

### Sổ S2D — Vật tư hàng hoá
- Theo dõi từng sản phẩm riêng biệt
- Tính giá vốn theo phương pháp **bình quân gia quyền**
- Đơn giá nhập = `unit_cost` từ valuation layer
- Đơn giá xuất = `avg_price` tại thời điểm xuất
- Hiển thị: SL Nhập/Xuất/Tồn và Thành tiền tương ứng
- Dòng cộng phát sinh và tồn cuối kỳ

### Sổ S2E — Tiền mặt & Tiền gửi
- Tách biệt **tiền mặt** và **tiền gửi ngân hàng**
- Tính tồn đầu kỳ từ lịch sử thanh toán
- Công thức: `Tồn cuối = Tồn đầu + Tổng thu - Tổng chi`
- Hiển thị tổng thu/chi riêng từng loại

---

## Hướng dẫn sử dụng

### Truy cập sổ
```
Accounting → Statements → Sổ S2B / S2C / S2D / S2E
```

### Lọc dữ liệu
1. Bấm vào menu sổ cần xem → list view hiện ra
2. Bấm nút **Filter**
3. Chọn kỳ báo cáo:

| Loại kỳ | Thông tin cần chọn |
|---|---|
| Theo tháng | Tháng + Năm |
| Theo quý | Quý + Năm |
| Theo năm | Năm |
| Tuỳ chọn | Từ ngày / Đến ngày |

4. Với **S2D**: chọn thêm sản phẩm cần xem
5. Bấm **Xem sổ**

---

## Cấu trúc dự án

```text
invoice-analyzer/
├── docker-compose.yml
├── .env.example
├── .env
├── README.md
└── addons/
    ├── hkd_dashboard/
    ├── hkd_mrp/
    ├── hkd_purchase/
    ├── hkd_sales/
    ├── hkd_statements/
    └── hkd_tax_policy/
```

---

## Dependencies

```python
'depends': ['account', 'stock', 'purchase']
```

---

## Troubleshooting

### Menu không hiện
- Kiểm tra `__manifest__.py` — file wizard view phải load trước `menus.xml`
- Upgrade module và hard reload (`Ctrl+Shift+R`)

### Lỗi 500 khi bấm Filter
- Kiểm tra JS và XML phải là 2 file riêng biệt
- Kiểm tra `buttonTemplate` trong JS khớp với `t-name` trong XML

### Đơn giá = 0 trong S2D
- Kiểm tra **Automated Valuation** đã bật chưa
- Kiểm tra **Costing Method** của Product Category là `AVCO`

### Tiền mặt/Tiền gửi không phân loại được trong S2E
- Kiểm tra **Journal Type** đã set đúng `Cash`/`Bank` chưa