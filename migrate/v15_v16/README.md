# 🚀 Odoo v15 → v16 Migration Project

## 🎯 Mục tiêu cốt lõi

Triển khai workflow migration hoàn chỉnh từ Odoo v15 lên v16 bằng **Python** với các bước:

1. **Health Check môi trường:** PostgreSQL, Odoo v15, Odoo v16
   - Kiểm tra: `postgresql\compose.yml`, `odoo_v15\compose.yml`, `odoo_v16\compose.yml`
   - Validate cấu hình: `odoo_v15\conf\odoo.conf`, `odoo_v16\conf\odoo.conf`

2. **Khởi tạo databases:** Tạo demo databases cho cả 2 phiên bản

3. **Phân tích cấu trúc:** So sánh database structures và tạo reports

4. **Lập kế hoạch migration:** Tạo blueprint.md và checklist chi tiết

5. **Triển khai migration:** Thực hiện theo phases với Python modules

## 🛠️ Setup & Usage

### Quick Start
```bash
cd migrate\v15_v16

# Setup môi trường ảo với uv  
uv venv ..\.venv
..\.venv\Scripts\activate
uv pip install -r requirements.txt

# Health check
python main.py health-check --detailed --fix
```

### Commands chính
```bash
# Kiểm tra môi trường
uv run --project migrate/v15_v16 migrate health-check

# Trạng thái tổng quan  


# Thông tin cấu hình
uv run --project migrate/v15_v16 migrate info

# Quản lý Database
uv run --project migrate/v15_v16 create-demo 
uv run --project migrate/v15_v16 delete-db 

# Quản lý Module/App  
python main.py install-app --db-name demo_test_v15 --modules sale,purchase,crm --version 15
python main.py uninstall-app --db-name demo_test_v15 --modules sale --version 15
python main.py list-apps --db-name demo_test_v15 --version 15

# Phân tích database (Coming Soon)  
python main.py analyze-db
```

## 📁 Cấu trúc Project

```
migrate/v15_v16/
├── main.py                    # 🎯 CLI entry point chính
├── config.json               # ⚙️ Cấu hình tập trung
├── requirements.txt          # 📦 Python dependencies  
├── pyproject.toml            # 🔧 UV project config
├── migration_guide.md        # 📖 Tài liệu chi tiết
├── README_quickstart.md      # 🚀 Hướng dẫn nhanh
├── src/
│   ├── __init__.py           # 📦 Package init
│   ├── config.py             # ⚙️ Configuration management
│   ├── utils.py              # 🛠️ Utilities & helpers  
│   ├── health_check.py       # 🔍 Health check module
│   ├── database_setup.py     # 🗄️ Database setup (TODO)
│   └── database_analyzer.py  # 📊 Database analysis (TODO)
├── log/                      # 📝 Log files
└── tests/                    # 🧪 Test cases
```

## 🎯 Nguyên tắc thiết kế (Elon Musk Principles)

1. **Loại bỏ không cần thiết:** Thay thế PowerShell bằng Python tool duy nhất
2. **Đơn giản hóa triệt để:** CLI interface trực quan, config tập trung  
3. **Tối ưu hóa sau khi vận hành:** Health check trước, migration sau
4. **Tích hợp & giảm điểm hỏng:** Single codebase, integrated error handling
5. **Tốc độ là chìa khóa:** Fast feedback, immediate fixes với `--fix`
6. **Tự động hóa là bước cuối:** Manual → Auto health check → Auto migration

## 📊 Cấu hình hiện tại

### Services
- **PostgreSQL:** `postgresql:17` on port `5432`
- **Odoo v15:** `odoo:15.0` on port `8069` (container: `odoo_15`)  
- **Odoo v16:** `odoo:16.0` on port `8016` (container: `odoo_16`)

### Network
- **Docker Network:** `odoo_net`
- **Database:** `postgres` với user `odoo/odoo@pwd`

## 🔍 Health Check Features

- ✅ Docker environment validation
- ✅ Container health monitoring  
- ✅ Database connectivity testing
- ✅ Web service accessibility
- ✅ Network connectivity between containers
- ✅ Port availability checking
- ✅ Configuration file validation
- ✅ Auto-fix common issues với `--fix` flag

## 📈 Health Score

- 🟢 **90-100%:** EXCELLENT - Sẵn sàng migration!
- 🟡 **75-89%:** GOOD - Vài vấn đề nhỏ cần xử lý
- 🟠 **50-74%:** FAIR - Nhiều vấn đề cần attention  
- 🔴 **<50%:** POOR - Vấn đề nghiêm trọng phải resolve

## 🚀 Migration Phases

1. ✅ **Health Check** - Environment validation
2. 🚧 **Database Setup** - Demo databases creation
3. 🚧 **Structure Analysis** - Schema comparison & reporting  
4. 🚧 **Migration Planning** - Blueprint generation
5. 🚧 **Data Migration** - Actual migration execution
6. 🚧 **Validation** - Post-migration verification

## 📚 Tài liệu

- [📖 Migration Guide](./migration_guide.md) - Hướng dẫn chi tiết
- [🚀 Quick Start](./README_quickstart.md) - Setup nhanh
- [⚙️ Configuration](./config.json) - Cấu hình project

## 🔧 Requirements

- **Python 3.8+**
- **Docker & Docker Compose** 
- **UV package manager**
- **Môi trường ảo tại:** `migrate\.venv`

## 🛠️ Troubleshooting

### ⚠️ Registry Issues sau khi cài Module

**Vấn đề:** Lỗi `KeyError: 'model_name'` trên web sau khi cài module qua CLI
```
KeyError: 'crm.team'
KeyError: 'payment.transaction'
```

**Nguyên nhân:** 
- Odoo registry không được refresh sau khi cài module via CLI
- Container Odoo cần restart để load lại registry với các model mới
- Đây là limitation của việc cài module qua `-i` thay vì web interface

**Giải pháp:**
```bash
# 1. Restart container Odoo để load lại registry
docker restart odoo_15

# 2. Chờ container khởi động hoàn tất (30-60s)
docker logs odoo_15 --tail 20

# 3. Xác nhận registry đã được load: 
# Log sẽ hiển thị: "Registry loaded in X.XXXs"
```

**Tự động hóa:**
CLI commands đã được cập nhật để tự động restart container sau khi cài module:
```bash
python main.py install-app --db-name demo_test_v15 --modules crm --version 15
# ✅ Tự động restart container sau khi cài
```

### 🔍 Debug Registry Issues

```bash
# Kiểm tra model có tồn tại trong database
docker exec postgresql psql -U odoo -d odoo_demo_v15 -c "SELECT model FROM ir_model WHERE model = 'crm.team';"

# Kiểm tra bảng có tồn tại
docker exec postgresql psql -U odoo -d odoo_demo_v15 -c "\dt crm_team"

# Kiểm tra trạng thái module
docker exec postgresql psql -U odoo -d odoo_demo_v15 -c "SELECT name, state FROM ir_module_module WHERE name = 'crm';"

# Kiểm tra log container
docker logs odoo_15 --tail 50
```