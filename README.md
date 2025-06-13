# Odoo Migration Workspace

Công cụ migration Odoo đa phiên bản với PostgreSQL MCP server.

## 🚀 Cài đặt

```cmd
# Cài đặt dependencies
uv sync
```

## 📋 Sử dụng

```cmd
# Migration tool v15→v16
migrate-v15-v16 --help
migrate-v15-v16 health      # Check system health
migrate-v15-v16 status      # Show migration status
migrate-v15-v16 setup       # Setup databases
migrate-v15-v16 migrate     # Run migration

# PostgreSQL MCP server
postgres-mcp
```

## 🛠 Development

```cmd
# Format code
uv run black .

# Type checking  
uv run mypy .

# Run tests
uv run pytest
```

## 📂 Cấu trúc

- `migrate/v15_v16/` - Migration tools v15→v16
- `pg_mcp/` - PostgreSQL MCP server
- `odoo_v*/` - Odoo instances
- `postgresql/` - PostgreSQL database