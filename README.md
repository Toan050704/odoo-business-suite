# Business Suite Odoo 16

## Thông tin dự án

- **Repository GitHub:** [https://github.com/Toan050704/odoo-business-suite.git](https://github.com/Toan050704/odoo-business-suite.git)
- **URL truy cập local:** [http://localhost:10020](http://localhost:10020)
- **Nền tảng:** Odoo 16
- **Mục tiêu:** Bộ addon phục vụ vận hành hộ kinh doanh (HKD), bao gồm bán hàng, mua hàng, sản xuất, thuế và báo cáo nghiệp vụ.


---

## Mục lục

- [Tổng quan](#tổng-quan)
- [Các module hiện có](#các-module-hiện-có)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt](#cài-đặt)
- [Cấu hình ban đầu](#cấu-hình-ban-đầu)
- [Mô tả từng module](#mô-tả-từng-module)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Troubleshooting](#troubleshooting)

---

## Tổng quan

`odoo-business-suite` là bộ addon tùy biến cho Odoo 16 nhằm phục vụ quy trình vận hành của hộ kinh doanh:

- Quản lý bán hàng và POS
- Quản lý mua hàng
- Quản lý sản xuất (MRP)
- Cấu hình chính sách thuế HKD
- Theo dõi các sổ báo cáo S2B, S2C, S2D, S2E
- Cung cấp dashboard tổng quan cho người dùng

---

## Các module hiện có

Các addon hiện đang có trong thư mục `addons/`:

| Module | Mô tả ngắn |
|---|---|
| `hkd_core` | Module nền tảng, chứa dữ liệu khởi tạo và các cấu hình dùng chung cho hệ thống HKD |
| `hkd_dashboard` | Dashboard tổng quan, hiển thị các chỉ số điều hành và báo cáo |
| `hkd_mrp` | Quản lý sản xuất, lệnh sản xuất và sản phẩm liên quan |
| `hkd_purchase` | Mở rộng nghiệp vụ mua hàng và nhà cung cấp |
| `hkd_sales` | Mở rộng bán hàng/POS, hỗ trợ tạo invoice và đồng bộ nghiệp vụ bán hàng |
| `hkd_statements` | Bộ sổ báo cáo HKD gồm S2B, S2C, S2D, S2E |
| `hkd_tax_policy` | Cấu hình chính sách thuế HKD và danh mục thuế dùng chung |
| `muk_web_theme` | Giao diện/theme bổ sung cho web client Odoo |

---

## Yêu cầu hệ thống

| Thành phần | Phiên bản |
|---|---|
| Odoo | 16.0 |
| PostgreSQL | 15+ |
| Python | 3.10+ |
| Docker | 20+ *(nếu chạy bằng Docker)* |
| Docker Compose | 2+ *(nếu chạy bằng Docker)* |

---

## Cài đặt

### 1. Clone source code

```bash
git clone https://github.com/Toan050704/odoo-business-suite.git
```

### 2. Cập nhật `addons_path`

Đảm bảo Odoo đã trỏ tới thư mục `addons/` của project này.

Ví dụ:

```ini
addons_path = /path/to/odoo/odoo/addons,/path/to/odoo-business-suite/addons
```

### 3. Khởi động Odoo / Docker

Nếu dùng Docker:

```bash
docker compose up -d
```

Nếu chạy Odoo trực tiếp, khởi động theo cấu hình môi trường của bạn.

### 4. Cập nhật danh sách Apps

Vào Odoo, bật chế độ developer nếu cần, sau đó:

```text
Apps → Update Apps List
```

### 5. Cài các module cần dùng

Tối thiểu nên cài theo thứ tự:

1. `hkd_tax_policy`
2. `hkd_sales`
3. `hkd_purchase`
4. `hkd_mrp` *(nếu dùng sản xuất)*
5. `hkd_dashboard`
6. `hkd_statements`
7. `hkd_core` *(module nền tảng, tùy cấu hình triển khai)*

> Lưu ý: `hkd_core` là module nền tảng có phụ thuộc chéo với các module HKD khác. Hãy cài theo luồng nghiệp vụ của hệ thống hiện tại.

---

## Cấu hình ban đầu

Trước khi dùng báo cáo và nghiệp vụ HKD, cần kiểm tra các cấu hình sau trong Odoo:

### 1. Chart of Accounts

```text
Accounting → Configuration → Chart of Accounts
```

### 2. Journals

```text
Accounting → Configuration → Journals
```

Khuyến nghị có ít nhất:

| Journal | Type |
|---|---|
| Tiền mặt | Cash |
| Ngân hàng | Bank |

### 3. Kho hàng và định giá tồn kho

```text
Inventory → Configuration → Settings
```

Nên bật:

- Automated Valuation
- Costing Method phù hợp, thường là `Average Cost (AVCO)`

### 4. Thuế và chính sách HKD

Cài `hkd_tax_policy` để có danh mục/chính sách thuế dùng chung cho bán hàng, mua hàng và sản phẩm.

---

## Mô tả từng module

### `hkd_core`

Module nền tảng của hệ thống HKD.

Chức năng chính:

- Menu gốc và cấu hình dùng chung
- Dữ liệu khởi tạo cho sản phẩm, UoM, danh mục, nguyên liệu
- View mở rộng cho sản phẩm, nhân sự, kho, MRP, mua hàng và hóa đơn

Phụ thuộc chính:

- `base_setup`
- `account`
- `sale_management`
- `point_of_sale`
- `product`
- `mrp`
- `stock`
- Các module HKD khác

---

### `hkd_dashboard`

Dashboard tổng quan báo cáo HKD.

Chức năng chính:

- Hiển thị số liệu điều hành tổng quan
- Biểu đồ và thông tin về doanh thu, chi phí, công nợ
- Tập trung dữ liệu từ các module HKD khác

Phụ thuộc chính:

- `account`
- `stock`
- `purchase`
- `hkd_tax_policy`

---

### `hkd_mrp`

Module sản xuất cho HKD.

Chức năng chính:

- Quản lý lệnh sản xuất
- Theo dõi nguyên vật liệu, bán thành phẩm và thành phẩm
- Hỗ trợ quy trình tạo thành phẩm từ nguyên liệu đầu vào

Phụ thuộc chính:

- `mrp`

---

### `hkd_purchase`

Module mở rộng nghiệp vụ mua hàng.

Chức năng chính:

- Quản lý đơn mua hàng và nhà cung cấp
- Theo dõi nhập hàng và chi phí đầu vào
- Phục vụ đối chiếu kho, công nợ và kế toán

Phụ thuộc chính:

- `purchase`

---

### `hkd_sales`

Module mở rộng nghiệp vụ bán hàng và POS.

Chức năng chính:

- Tạo invoice ngay khi thanh toán POS
- Quản lý bán hàng và dữ liệu liên quan đến đơn hàng
- Tích hợp dữ liệu bán hàng với kế toán và kho

Phụ thuộc chính:

- `point_of_sale`
- `account`
- `sale_management`
- `sale_stock`
- `stock`
- `hkd_tax_policy`

---

### `hkd_tax_policy`

Module chính sách thuế HKD.

Chức năng chính:

- Danh mục chính sách thuế cha–con
- Cấu hình thuế cho sản phẩm, mua hàng và bán hàng
- Đồng bộ logic thuế cho toàn hệ thống

Phụ thuộc chính:

- `account`
- `sale_management`
- `point_of_sale`
- `product`
- `purchase`
- `l10n_vn`

---

### `hkd_statements`

Module các sổ báo cáo HKD.

Các sổ hiện có:

| Sổ | Tên | Nguồn dữ liệu |
|---|---|---|
| S2B | Sổ doanh thu | `account.move` |
| S2C | Sổ chi phí | `account.move` |
| S2D | Sổ vật tư hàng hoá | `stock.move`, `stock.valuation.layer` |
| S2E | Sổ tiền mặt & tiền gửi | `account.payment` |

Chức năng chính:

- Lọc dữ liệu theo kỳ báo cáo
- Xem doanh thu, chi phí, tồn kho và tiền mặt/ngân hàng
- Hỗ trợ giao diện lọc bằng nút trên backend

Phụ thuộc chính:

- `base`
- `account`

---

## Cấu trúc thư mục

```text
odoo-business-suite/
├── README.md
├── addons/
│   ├── hkd_core/
│   ├── hkd_dashboard/
│   ├── hkd_mrp/
│   ├── hkd_purchase/
│   ├── hkd_sales/
│   ├── hkd_statements/
│   ├── hkd_tax_policy/
│   └── muk_web_theme/
```

---

## Troubleshooting

### 1. Không thấy module trong Apps

- Kiểm tra `addons_path`
- Bật Developer Mode
- Update Apps List
- Kiểm tra file `__manifest__.py` của module có hợp lệ không

### 2. Module không cài được do lỗi phụ thuộc

- Kiểm tra module phụ thuộc đã được cài chưa
- Kiểm tra tên addon trong `depends` có đúng với tên thư mục module không

### 3. Báo cáo S2D / S2E hiển thị sai dữ liệu

- Kiểm tra cấu hình kho và valuation
- Kiểm tra journal loại `Cash` / `Bank`
- Kiểm tra dữ liệu phát sinh có đúng kỳ báo cáo không

### 4. POS / Sales không ra invoice đúng như mong đợi

- Kiểm tra `hkd_sales` đã được cài
- Kiểm tra cấu hình POS, stock và tax policy
- Xem lại các file JS/XML assets nếu có thay đổi giao diện

---

## Ghi chú

Nếu bạn đã xoá bớt file trong `addons/`, hãy luôn cập nhật lại:

- Mục mô tả module
- Cây thư mục
- Phần `depends` trong từng module
- Hướng dẫn cài đặt và cấu hình
