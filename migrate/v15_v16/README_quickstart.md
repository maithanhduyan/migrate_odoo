# 🚀 Odoo Migration v15 → v16 - Quick Start

## Setup nhanh

### 1. Cài đặt môi trường
```bash
# Di chuyển vào thư mục
cd migrate\v15_v16

# Tạo và kích hoạt môi trường ảo
uv venv ..\.venv
..\.venv\Scripts\activate

# Cài đặt dependencies
uv pip install -r requirements.txt
```

### 2. Kiểm tra môi trường
```bash
# Health check cơ bản
python main.py health-check

# Health check chi tiết + auto fix
python main.py health-check --detailed --fix
```

### 3. Xem trạng thái
```bash
# Trạng thái tổng quan
python main.py status

# Thông tin cấu hình
python main.py info
```

## CLI Commands

| Command | Mô tả |
|---------|-------|
| `python main.py health-check` | Kiểm tra sức khỏe môi trường |
| `python main.py health-check --detailed` | Kiểm tra chi tiết |
| `python main.py health-check --fix` | Kiểm tra + tự động sửa |
| `python main.py status` | Hiển thị trạng thái |
| `python main.py info` | Hiển thị thông tin cấu hình |

## Cấu hình (config.json)

Tất cả cấu hình được quản lý trong file `config.json`:
- Container names và ports
- Database credentials  
- Network settings
- Migration phases

## Troubleshooting

### Docker không kết nối được
```bash
docker --version
docker ps
```

### Dependencies lỗi
```bash
uv pip install -r requirements.txt --force-reinstall
```

### Container không start
```bash
python main.py health-check --fix
```

## Tài liệu chi tiết

Xem [migration_guide.md](./migration_guide.md) để biết thêm chi tiết về:
- Health check đầy đủ
- Cấu hình chi tiết
- Troubleshooting
- Migration workflow

## Health Score

- 🟢 **90-100%:** Sẵn sàng migration
- 🟡 **75-89%:** Cần xử lý vài vấn đề nhỏ  
- 🟠 **50-74%:** Nhiều vấn đề cần xử lý
- 🔴 **<50%:** Vấn đề nghiêm trọng

## Next Steps

1. ✅ Health Check → `python main.py health-check --fix`
2. 🗄️ Database Setup → `python main.py setup-db` (Coming Soon)
3. 📊 Database Analysis → `python main.py analyze-db` (Coming Soon)
4. 🚀 Migration → `python main.py migrate` (Coming Soon)
