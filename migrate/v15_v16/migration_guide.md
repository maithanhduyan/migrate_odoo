# 🚀 Hướng dẫn Migration Odoo v15 → v16

## 📋 Tổng quan

Tài liệu này hướng dẫn chi tiết quá trình migration từ Odoo v15 lên Odoo v16, bao gồm kiểm tra môi trường, phân tích database và triển khai migration theo từng phase. **Tất cả được thực hiện bằng Python**.

---

## �️ Setup môi trường

### Yêu cầu hệ thống
- Python 3.8+
- Docker và Docker Compose
- `uv` package manager
- Môi trường ảo tại `migrate\.venv`

### 1. Khởi tạo môi trường ảo

```bash
# Tạo môi trường ảo bằng uv
cd migrate\v15_v16
uv venv ..\.venv

# Kích hoạt môi trường ảo (Windows)
..\.venv\Scripts\activate

# Hoặc sử dụng PowerShell
..\.venv\Scripts\Activate.ps1
```

### 2. Cài đặt dependencies

```bash
# Cài đặt dependencies với uv
uv pip install -r requirements.txt

# Hoặc cài đặt project với uv
uv pip install -e .
```

### 3. Kiểm tra cài đặt

```bash
# Kiểm tra CLI tool
python main.py --help
```

---

## 🔍 Phase 1: Kiểm tra môi trường (Environment Health Check)

### 1.1 Sử dụng CLI tool

```bash
# Health check cơ bản
python main.py health-check

# Health check chi tiết
python main.py health-check --detailed

# Health check với auto-fix
python main.py health-check --detailed --fix
```

### 1.2 Sử dụng trực tiếp module

```bash
# Chạy trực tiếp health check module
python -m src.health_check --detailed --fix
```

### 1.3 Các kiểm tra được thực hiện

#### ✅ Docker Environment Check
- Kiểm tra Docker daemon
- Kiểm tra Docker Compose
- Kiểm tra quyền truy cập Docker API

#### ✅ Network Check
- Kiểm tra network `odoo_net` tồn tại
- Tự động tạo network nếu thiếu (với `--fix`)

#### ✅ Container Health Check
- **PostgreSQL container:** `postgresql`
- **Odoo v15 container:** `odoo_15`
- **Odoo v16 container:** `odoo_16`
- Kiểm tra trạng thái: running/stopped/not found
- Tự động start containers nếu thiếu (với `--fix`)

#### ✅ Database Connectivity Check
- PostgreSQL readiness (`pg_isready`)
- Database connection từ Odoo v15
- Database connection từ Odoo v16
- Kiểm tra credentials và permissions

#### ✅ Web Service Check
- Odoo v15 web interface: http://localhost:8069
- Odoo v16 web interface: http://localhost:8016
- HTTP response status check

#### ✅ Network Connectivity Check
- Container-to-container connectivity
- Ping test từ Odoo containers đến PostgreSQL

#### ✅ Port Availability Check
- Ports: 5432 (PostgreSQL), 8069 (v15), 8016 (v16), 8172 (v15 longpolling), 8272 (v16 longpolling)

#### ✅ Configuration Validation (với `--detailed`)
- Kiểm tra file config tồn tại
- Validate cấu hình database trong odoo.conf
- So sánh cấu hình giữa v15 và v16

---

## 📊 Cấu hình hiện tại (config.json)

```json
{
  "project": {
    "name": "Odoo Migration v15 to v16",
    "version": "1.0.0",
    "workspace_root": "../../"
  },
  "environment": {
    "docker_network": "odoo_net",
    "health_check_timeout": 30,
    "web_request_timeout": 10,
    "log_level": "INFO"
  },
  "postgresql": {
    "container_name": "postgresql",
    "host": "postgresql",
    "port": 5432,
    "database": "postgres",
    "user": "odoo",
    "password": "odoo@pwd"
  },
  "odoo_v15": {
    "container_name": "odoo_15",
    "image": "odoo:15.0",
    "web_port": 8069,
    "web_url": "http://localhost:8069"
  },
  "odoo_v16": {
    "container_name": "odoo_16", 
    "image": "odoo:16.0",
    "web_port": 8016,
    "web_url": "http://localhost:8016"
  }
}
```

---

## �️ CLI Commands

### Thông tin tổng quan
```bash
# Hiển thị trạng thái tổng quan
python main.py status

# Hiển thị thông tin cấu hình
python main.py info

# Hiển thị help
python main.py --help
```

### Health Check Commands
```bash
# Health check cơ bản
python main.py health-check

# Health check chi tiết với logs
python main.py health-check --detailed

# Health check và auto-fix issues
python main.py health-check --fix

# Sử dụng custom config file
python main.py --config custom_config.json health-check
```

### Database Commands (Coming Soon)
```bash
# Setup demo databases
python main.py setup-db

# Phân tích database structure
python main.py analyze-db

# Tạo migration plan
python main.py plan-migration
```

### Migration Commands (Coming Soon)
```bash
# Thực hiện migration
python main.py migrate

# Validate migration results
python main.py validate
```

---

## 📈 Health Score và Recommendations

### Health Score Levels
- **90-100%:** 🟢 EXCELLENT - Ready for migration!
- **75-89%:** 🟡 GOOD - Minor issues to address
- **50-74%:** 🟠 FAIR - Several issues need attention
- **<50%:** 🔴 POOR - Major issues must be resolved

### Auto-fix Features (với `--fix`)
- Tạo Docker network `odoo_net` nếu thiếu
- Start các containers bị stop
- Rebuild containers nếu cần thiết

---

## 🚨 Troubleshooting

### Problem: Import errors
```bash
# Đảm bảo môi trường ảo được kích hoạt
..\.venv\Scripts\activate

# Reinstall dependencies
uv pip install -r requirements.txt --force-reinstall
```

### Problem: Docker connection failed
```bash
# Kiểm tra Docker daemon
docker --version
docker ps

# Restart Docker service nếu cần
```

### Problem: Container connection issues
```bash
# Kiểm tra network
docker network ls | findstr odoo_net

# Recreate network
docker network rm odoo_net
docker network create odoo_net

# Restart tất cả containers
python main.py health-check --fix
```

### Problem: Permission denied
```bash
# Chạy với quyền admin (nếu cần)
# Hoặc thêm user vào Docker group (Linux/Mac)
```

---

## 📁 Cấu trúc Project

```
migrate/v15_v16/
├── main.py                 # CLI entry point chính
├── config.json            # Cấu hình project
├── requirements.txt       # Python dependencies
├── pyproject.toml         # UV project config
├── migration_guide.md     # Tài liệu này
├── src/
│   ├── __init__.py        # Package init
│   ├── config.py          # Configuration management
│   ├── utils.py           # Utilities và helpers
│   ├── health_check.py    # Health check module
│   ├── database_setup.py  # Database setup (TODO)
│   └── database_analyzer.py # Database analysis (TODO)
├── log/                   # Log files
└── tests/                 # Test cases
```

---

## � Workflow Migration

### Phase 1: Health Check ✅
```bash
python main.py health-check --detailed --fix
```

### Phase 2: Database Setup (Coming Soon)
```bash
python main.py setup-db
```

### Phase 3: Database Analysis (Coming Soon)
```bash
python main.py analyze-db
```

### Phase 4: Migration Planning (Coming Soon)
```bash
python main.py plan-migration
```

### Phase 5: Migration Execution (Coming Soon)
```bash
python main.py migrate
```

### Phase 6: Validation (Coming Soon)
```bash
python main.py validate
```

---

## 🎯 Nguyên tắc Elon Musk được áp dụng

1. **Loại bỏ không cần thiết:** 
   - Không dùng PowerShell scripts phức tạp
   - Single Python tool cho tất cả operations

2. **Đơn giản hóa triệt để:**
   - CLI interface đơn giản và intuitive
   - Configuration tập trung trong config.json

3. **Tối ưu hóa sau khi vận hành:**
   - Health check trước, optimize sau
   - Validation-first approach

4. **Tích hợp & giảm điểm hỏng:**
   - Single codebase cho toàn bộ migration
   - Integrated error handling và auto-fix

5. **Tốc độ là chìa khóa:**
   - Fast health checks với parallel operations
   - Quick feedback và immediate fixes

6. **Tự động hóa là bước cuối cùng:**
   - Manual health check → Auto health check → Auto migration

---

**Tiếp theo:** [Phase 2: Database Setup](./phase2_database_setup.md)
