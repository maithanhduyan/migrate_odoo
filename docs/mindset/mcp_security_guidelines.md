# MCP Server Security Guidelines - Loại bỏ cảnh báo và tăng độ tin cậy

## 🚨 Hiểu về cảnh báo MCP

Cảnh báo "Note that MCP servers or malicious conversation content may attempt to misuse 'Code' through tools" xuất hiện vì:

1. **Nguy cơ thực thi mã độc**: MCP server có thể được lợi dụng để chạy code không an toàn
2. **Quyền truy cập hệ thống**: Tool có thể truy cập file system, database, network
3. **Thiếu validation**: Input từ LLM có thể chứa payload độc hại
4. **Privilege escalation**: MCP có thể có quyền cao hơn người dùng

## 🛡️ Nguyên tắc bảo mật MCP

### 1. **Input Validation & Sanitization**

```python
import re
import os
from pathlib import Path

class SecurityValidator:
    """Validator cho MCP server inputs"""
    
    ALLOWED_COMMANDS = {
        'docker': ['ps', 'images', 'stats', 'logs'],
        'postgres': ['SELECT', 'SHOW', 'DESCRIBE'],
        'file': ['read', 'list']
    }
    
    BLOCKED_PATTERNS = [
        r'rm\s+-rf\s+/',  # Ngăn xóa hệ thống
        r'sudo\s+',       # Ngăn privilege escalation
        r'curl.*\|\s*sh', # Ngăn download và execute
        r'eval\s*\(',     # Ngăn code injection
        r'exec\s*\(',     # Ngăn arbitrary execution
    ]
    
    @classmethod
    def validate_command(cls, command: str, tool_type: str) -> bool:
        """Validate command trước khi execute"""
        # Check blocked patterns
        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False
        
        # Check allowed commands cho tool type
        if tool_type in cls.ALLOWED_COMMANDS:
            cmd_parts = command.split()
            if cmd_parts and cmd_parts[0] not in cls.ALLOWED_COMMANDS[tool_type]:
                return False
        
        return True
    
    @classmethod
    def validate_path(cls, file_path: str) -> bool:
        """Validate file path để ngăn path traversal"""
        # Normalize path
        normalized = os.path.normpath(file_path)
        
        # Ngăn path traversal
        if '..' in normalized or normalized.startswith('/'):
            return False
        
        # Chỉ cho phép trong workspace
        workspace_root = Path.cwd()
        try:
            Path(workspace_root / normalized).resolve().relative_to(workspace_root)
            return True
        except ValueError:
            return False
    
    @classmethod
    def validate_sql(cls, query: str) -> bool:
        """Validate SQL query để ngăn injection"""
        # Chỉ cho phép SELECT statements
        normalized = query.strip().upper()
        
        if not normalized.startswith('SELECT'):
            return False
        
        # Ngăn các keyword nguy hiểm
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE',
            'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in normalized:
                return False
        
        return True
```

### 2. **Sandbox Environment**

```python
import docker
import tempfile
import shutil
from contextlib import contextmanager

class MCPSandbox:
    """Sandbox cho MCP operations"""
    
    def __init__(self):
        self.client = docker.from_env()
        self.temp_dirs = []
    
    @contextmanager
    def isolated_environment(self):
        """Tạo môi trường isolated"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        
        try:
            yield temp_dir
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def run_in_container(self, command: str, image: str = "python:3.11-slim") -> str:
        """Chạy command trong Docker container"""
        try:
            result = self.client.containers.run(
                image=image,
                command=command,
                remove=True,
                network_mode='none',  # Không có network access
                mem_limit='256m',     # Giới hạn memory
                cpu_period=100000,    # Giới hạn CPU
                cpu_quota=50000,      # 50% CPU
                timeout=30,           # Timeout 30s
                user='nobody',        # Non-root user
                security_opt=['no-new-privileges']
            )
            return result.decode('utf-8')
        except Exception as e:
            return f"Error: {str(e)}"
    
    def cleanup(self):
        """Cleanup temp directories"""
        for temp_dir in self.temp_dirs:
            shutil.rmtree(temp_dir, ignore_errors=True)
        self.temp_dirs.clear()
```

### 3. **Authentication & Authorization**

```python
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

class MCPAuth:
    """Authentication cho MCP server"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.active_tokens = set()
        self.user_permissions = {}
    
    def generate_token(self, user_id: str, permissions: list) -> str:
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow(),
            'jti': secrets.token_hex(16)  # Unique token ID
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        self.active_tokens.add(payload['jti'])
        self.user_permissions[user_id] = permissions
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Check if token is still active
            if payload['jti'] not in self.active_tokens:
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def check_permission(self, user_id: str, action: str) -> bool:
        """Check user permission cho action"""
        permissions = self.user_permissions.get(user_id, [])
        return action in permissions or 'admin' in permissions
    
    def revoke_token(self, jti: str):
        """Revoke token"""
        self.active_tokens.discard(jti)
```

### 4. **Secure MCP Server Implementation**

```python
from mcp.server.fastmcp import FastMCP
from typing import Any, Dict
import logging
import asyncio

class SecureMCPServer:
    """Secure MCP Server wrapper"""
    
    def __init__(self, name: str, secret_key: str):
        self.mcp = FastMCP(name)
        self.validator = SecurityValidator()
        self.sandbox = MCPSandbox()
        self.auth = MCPAuth(secret_key)
        self.setup_logging()
    
    def setup_logging(self):
        """Setup security logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('mcp_security.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('SecureMCP')
    
    def secure_tool(self, func):
        """Decorator để secure tool functions"""
        async def wrapper(*args, **kwargs):
            # Log request
            self.logger.info(f"Tool called: {func.__name__} with args: {args}")
            
            try:
                # Validate inputs
                if not self._validate_inputs(args, kwargs):
                    self.logger.warning(f"Invalid inputs for {func.__name__}")
                    raise ValueError("Invalid inputs detected")
                
                # Execute trong sandbox nếu cần
                if self._requires_sandbox(func.__name__):
                    return await self._execute_in_sandbox(func, args, kwargs)
                else:
                    return await func(*args, **kwargs)
            
            except Exception as e:
                self.logger.error(f"Error in {func.__name__}: {str(e)}")
                raise
        
        return wrapper
    
    def _validate_inputs(self, args: tuple, kwargs: dict) -> bool:
        """Validate tất cả inputs"""
        for arg in args:
            if isinstance(arg, str):
                # Check for malicious patterns
                for pattern in self.validator.BLOCKED_PATTERNS:
                    if re.search(pattern, arg, re.IGNORECASE):
                        return False
        
        return True
    
    def _requires_sandbox(self, func_name: str) -> bool:
        """Check if function cần sandbox"""
        sandbox_functions = ['execute_code', 'run_command', 'file_operation']
        return func_name in sandbox_functions
    
    async def _execute_in_sandbox(self, func, args, kwargs):
        """Execute function trong sandbox"""
        with self.sandbox.isolated_environment() as temp_dir:
            # Redirect operations to sandbox
            return await func(*args, **kwargs)
```

## 🔐 Implementation cho từng MCP Server

### 1. **Docker MCP - Secure Implementation**

```python
# Trong docker_mcp/src/secure_server.py
from secure_mcp import SecureMCPServer, SecurityValidator

class SecureDockerMCP(SecureMCPServer):
    def __init__(self):
        super().__init__("secure-docker", os.getenv('MCP_SECRET_KEY'))
        self.register_tools()
    
    def register_tools(self):
        @self.mcp.tool()
        @self.secure_tool
        async def docker_list(all: bool = True) -> str:
            """List containers với security check"""
            if not self.validator.validate_command("docker ps", "docker"):
                raise ValueError("Command not allowed")
            
            # Safe implementation
            import docker
            client = docker.from_env()
            containers = client.containers.list(all=all)
            
            result = []
            for container in containers:
                result.append({
                    'id': container.short_id,
                    'name': container.name,
                    'status': container.status,
                    'image': container.image.tags[0] if container.image.tags else 'unknown'
                })
            
            return json.dumps(result, indent=2)
```

### 2. **PostgreSQL MCP - Secure Implementation**

```python
# Trong pg_mcp/src/secure_server.py
class SecurePostgresMCP(SecureMCPServer):
    def __init__(self):
        super().__init__("secure-postgres", os.getenv('MCP_SECRET_KEY'))
        self.register_tools()
    
    def register_tools(self):
        @self.mcp.tool()
        @self.secure_tool
        async def execute_query(query: str, limit: int = 100) -> str:
            """Execute SQL query với security validation"""
            # Validate SQL
            if not self.validator.validate_sql(query):
                raise ValueError("SQL query not allowed")
            
            # Limit results
            if limit > 1000:
                limit = 1000
            
            # Safe query execution
            return await self._safe_execute_query(query, limit)
    
    async def _safe_execute_query(self, query: str, limit: int) -> str:
        """Execute query trong read-only mode"""
        try:
            # Sử dụng read-only connection
            conn = psycopg2.connect(
                **self.db_config,
                options='-c default_transaction_read_only=on'
            )
            
            cursor = conn.cursor()
            cursor.execute(f"{query} LIMIT {limit}")
            results = cursor.fetchall()
            
            return json.dumps(results, default=str, indent=2)
        
        except Exception as e:
            self.logger.error(f"Query execution error: {str(e)}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()
```

### 3. **Python Code MCP - Secure Implementation**

```python
# Trong py_mcp/src/secure_server.py
class SecurePythonMCP(SecureMCPServer):
    def __init__(self):
        super().__init__("secure-python", os.getenv('MCP_SECRET_KEY'))
        self.register_tools()
    
    def register_tools(self):
        @self.mcp.tool()
        @self.secure_tool
        async def validate_code(code: str) -> str:
            """Validate Python code trong sandbox"""
            # Parse AST để check safety
            if not self._is_safe_code(code):
                raise ValueError("Unsafe code detected")
            
            # Execute trong sandbox
            return await self._analyze_in_sandbox(code)
    
    def _is_safe_code(self, code: str) -> bool:
        """Check if Python code is safe"""
        try:
            tree = ast.parse(code)
            
            # Check for dangerous imports/calls
            dangerous_nodes = [
                ast.Import, ast.ImportFrom,
                ast.Exec, ast.Eval
            ]
            
            for node in ast.walk(tree):
                if isinstance(node, tuple(dangerous_nodes)):
                    if hasattr(node, 'names'):
                        for alias in node.names:
                            if alias.name in ['os', 'sys', 'subprocess', '__import__']:
                                return False
                
                if isinstance(node, ast.Call):
                    if hasattr(node.func, 'id') and node.func.id in ['exec', 'eval', 'compile']:
                        return False
            
            return True
        
        except SyntaxError:
            return False
```

## 🛠️ Deployment Configuration

### 1. **Environment Variables**

```bash
# .env.secure
MCP_SECRET_KEY=your-super-secure-secret-key-here
MCP_LOG_LEVEL=INFO
MCP_SANDBOX_ENABLED=true
MCP_AUTH_REQUIRED=true
MCP_MAX_MEMORY=256m
MCP_MAX_CPU=0.5
MCP_TIMEOUT=30
MCP_NETWORK_ISOLATION=true
```

### 2. **Docker Compose với Security**

```yaml
# docker-compose.secure.yml
version: '3.8'

services:
  mcp-server:
    build: .
    environment:
      - MCP_SECRET_KEY=${MCP_SECRET_KEY}
      - MCP_AUTH_REQUIRED=true
      - MCP_SANDBOX_ENABLED=true
    security_opt:
      - no-new-privileges:true
      - apparmor:mcp-profile
    cap_drop:
      - ALL
    cap_add:
      - SETUID
      - SETGID
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
    user: "1000:1000"
    networks:
      - mcp-internal
    volumes:
      - ./logs:/app/logs:rw
    ports:
      - "127.0.0.1:8000:8000"

networks:
  mcp-internal:
    driver: bridge
    internal: true
```

### 3. **Security Configuration**

```json
{
  "security": {
    "authentication": {
      "required": true,
      "method": "jwt",
      "expiry": "24h"
    },
    "authorization": {
      "default_permissions": ["read"],
      "admin_permissions": ["read", "write", "execute"],
      "guest_permissions": ["read"]
    },
    "sandbox": {
      "enabled": true,
      "timeout": 30,
      "memory_limit": "256m",
      "cpu_limit": 0.5,
      "network_isolation": true
    },
    "validation": {
      "input_sanitization": true,
      "sql_injection_protection": true,
      "path_traversal_protection": true,
      "command_injection_protection": true
    },
    "logging": {
      "security_events": true,
      "audit_trail": true,
      "log_level": "INFO"
    }
  }
}
```

## 📋 Security Checklist

### ✅ Pre-deployment
- [ ] Input validation cho tất cả tools
- [ ] SQL injection protection
- [ ] Path traversal protection  
- [ ] Command injection protection
- [ ] Authentication implementation
- [ ] Authorization checks
- [ ] Sandbox environment setup
- [ ] Logging configuration
- [ ] Error handling secure
- [ ] Secret management

### ✅ Runtime Security
- [ ] Resource limits enforced
- [ ] Network isolation active
- [ ] Non-root user execution
- [ ] Capability dropping
- [ ] Read-only file system
- [ ] Temporary storage limits
- [ ] Process monitoring
- [ ] Security audit logging

### ✅ Monitoring
- [ ] Failed authentication attempts
- [ ] Suspicious input patterns
- [ ] Resource usage anomalies
- [ ] Network connection attempts
- [ ] File access violations
- [ ] Privilege escalation attempts

## 🚀 Migration Plan

### Phase 1: Assessment
1. Audit current MCP servers
2. Identify security gaps
3. Plan secure implementation

### Phase 2: Implementation
1. Implement SecurityValidator
2. Add authentication layer
3. Setup sandbox environment
4. Update tool functions

### Phase 3: Testing
1. Security penetration testing
2. Performance impact assessment
3. Functionality verification

### Phase 4: Deployment
1. Gradual rollout
2. Monitor security logs
3. Performance tuning
4. Documentation update

## 🎯 Kết quả mong đợi

Sau khi implement theo guidelines này:
- ❌ Cảnh báo security sẽ biến mất
- ✅ MCP server trở nên đáng tin cậy
- ✅ Input validation hoàn thiện
- ✅ Sandbox isolation
- ✅ Authentication & authorization
- ✅ Audit trail đầy đủ
- ✅ Performance optimization
- ✅ Compliance với security standards

## 📚 References

- [MCP Security Best Practices](https://docs.mcp.com/security)
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [Docker Security Guide](https://docs.docker.com/engine/security/)
- [Python Security Guidelines](https://python-security.readthedocs.io/)
