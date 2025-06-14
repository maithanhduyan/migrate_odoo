# Python Code Conduct & Standards

## 🎯 Mục tiêu
Đảm bảo code Python trong dự án này tuân thủ các nguyên tắc **Elon Musk** và best practices, giúp MCP Server hoạt động hiệu quả.

## 🏗️ Nguyên tắc thiết kế cốt lõi

### 1. **Loại bỏ không cần thiết**
```python
# ❌ KHÔNG làm như thế này
class ComplexMCPServerWithManyFeatures:
    def __init__(self):
        self.advanced_logging_system = AdvancedLogger()
        self.complex_configuration_manager = ConfigManager()
        self.database_connection_pool = DBPool()
        # ... 20 dòng setup khác

# ✅ LÀM như thế này
class SimpleMCPServer:
    def __init__(self):
        self.tools = {"check": self._check_syntax}
```

### 2. **Đơn giản hóa triệt để**
```python
# ❌ KHÔNG - Quá phức tạp
def validate_python_code_with_advanced_ast_parsing_and_error_recovery(code_string):
    try:
        parser = AdvancedPythonParser()
        ast_tree = parser.parse_with_error_recovery(code_string)
        validation_result = ComplexValidator().validate(ast_tree)
        return validation_result.to_json()
    except Exception as e:
        return ErrorHandler().handle_complex_error(e)

# ✅ LÀM - Đơn giản, hiệu quả
def check_syntax(code: str) -> dict:
    try:
        compile(code, '<string>', 'exec')
        return {"valid": True}
    except SyntaxError as e:
        return {"valid": False, "error": str(e)}
```

### 3. **Tối ưu sau khi vận hành**
- Implement basic functionality FIRST
- Measure performance với real data
- Optimize chỉ khi có bottleneck thực tế

## 📝 Coding Standards

### PEP8 (Python Enhancement Proposal 8)
- **Indentation:** 4 spaces, không dùng tab
- **Line length:** tối đa 79 ký tự (hoặc 88 nếu dùng black)
- **Naming:**
  - Biến, hàm: snake_case
  - Class: PascalCase
  - Hằng số: UPPER_CASE
- **Import:** Tách nhóm (chuẩn lib, third-party, local), mỗi nhóm cách nhau 1 dòng trắng
- **Khoảng trắng:** Không thừa trước/giữa dấu phẩy, toán tử, sau dấu hai chấm
- **Docstring:** Dùng triple quotes, mô tả ngắn gọn chức năng
- **File end:** Luôn kết thúc bằng 1 dòng trắng

> **Khuyến nghị:**
> - Sử dụng tool tự động như `black`, `flake8` để kiểm tra và format code.
> - Có thể dùng `isort` để sắp xếp import.

```python
# Ví dụ PEP8 chuẩn
import os
import sys

import requests

from .utils import helper

def get_data(path: str) -> str:
    """Lấy dữ liệu từ file"""
    with open(path, 'r') as f:
        return f.read()
```

### Import Organization
```python
# Standard library imports
import json
import sys
import ast

# Third-party imports
import asyncio

# Local imports
from .utils import helper_function
```

### Function Design
```python
def function_name(param: type) -> return_type:
    """
    Mô tả ngắn gọn function làm gì
    
    Args:
        param: Mô tả parameter
        
    Returns:
        Mô tả return value
        
    Raises:
        Exception: Khi nào raise exception
    """
    # Implementation đơn giản nhất có thể
    pass
```

### Error Handling
```python
# ✅ Simple & Effective
try:
    result = risky_operation()
    return {"success": True, "data": result}
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    return {"success": False, "error": str(e)}
```

### Class Design
```python
class MCPTool:
    """
    Một class chỉ làm một việc, làm tốt việc đó
    """
    
    def __init__(self, essential_param: str):
        # Chỉ initialize những gì thực sự cần
        self.param = essential_param
    
    def do_one_thing_well(self) -> str:
        """Làm một việc, làm tốt"""
        return f"Result: {self.param}"
```

## 🚀 Performance Guidelines

### 1. **Speed is Key**
```python
# ✅ Fast iteration
def quick_syntax_check(code: str) -> bool:
    """Quick check - optimize later if needed"""
    try:
        compile(code, '<string>', 'exec')
        return True
    except:
        return False

# ❌ Premature optimization
def over_engineered_syntax_check(code: str) -> ComplexResult:
    """Don't do this until you have data proving it's needed"""
    pass
```

### 2. **Memory Efficiency**
```python
# ✅ Generator for large data
def process_large_code_files():
    for line in file:
        yield process_line(line)

# ❌ Loading everything into memory
def load_all_files():
    return [process_file(f) for f in all_files]  # Memory killer
```

## 🔧 Tool Implementation Standards

### MCP Tool Structure
```python
async def tool_name(self, params: Dict[str, Any]) -> Any:
    """
    Standard MCP tool implementation
    """
    try:
        # 1. Extract parameters - simple validation
        required_param = params.get("required_param")
        if not required_param:
            raise ValueError("Missing required parameter")
        
        # 2. Do the work - focus on core functionality
        result = self._do_core_work(required_param)
        
        # 3. Return simple result
        return result
        
    except Exception as e:
        # 4. Simple error handling
        raise ValueError(f"Tool failed: {str(e)}")
```

## 🧪 Testing Philosophy

### Test Essential Functionality Only
```python
def test_syntax_checker():
    """Test only what matters"""
    # Valid code
    assert check_syntax("print('hello')")["valid"] == True
    
    # Invalid code  
    assert check_syntax("print('hello'")["valid"] == False
    
    # Edge case
    assert check_syntax("")["valid"] == True
```

### No Over-Testing
```python
# ❌ Don't test implementation details
def test_internal_parser_state():
    parser = CodeParser()
    parser.parse("code")
    assert parser._internal_state == "expected"  # Bad!

# ✅ Test behavior only
def test_parser_output():
    assert parse_code("valid code") == {"errors": []}
```

## 📊 Code Quality Metrics

### What We Measure
1. **Functionality**: Does it work?
2. **Simplicity**: Lines of code per feature
3. **Performance**: Response time for real use cases
4. **Reliability**: Error rate in production

### What We DON'T Measure (initially)
- Cyclomatic complexity 
- Test coverage percentage
- Advanced metrics

## 🚫 Anti-Patterns to Avoid

### 1. Framework Fever
```python
# ❌ Don't use heavy frameworks for simple tasks
from complex_web_framework import App, Router, Middleware

# ✅ Use simple solutions
import json
```

### 2. Configuration Overload
```python
# ❌ Too many configuration options
config = {
    "parser_mode": "advanced",
    "error_recovery": True,
    "optimization_level": 3,
    "cache_strategy": "lru",
    # ... 50 more options
}

# ✅ Sensible defaults, minimal config
config = {"debug": False}
```

### 3. Premature Abstraction
```python
# ❌ Don't create interfaces before you need them
class AbstractCodeValidator(ABC):
    @abstractmethod
    def validate(self, code: str) -> ValidationResult:
        pass

# ✅ Start concrete, abstract later if needed
def validate_code(code: str) -> bool:
    # Simple implementation
    pass
```

## 🎯 Success Criteria

### Code is successful when:
1. **It works** - Solves the real problem
2. **It's fast** - Quick to write, quick to run
3. **It's simple** - Easy to understand and modify
4. **It's reliable** - Handles errors gracefully

### Code fails when:
1. Over-engineered for the problem size
2. Takes too long to implement
3. Hard to debug or modify
4. Performance issues in real usage

## 🔄 Iteration Process

1. **Build minimal working version**
2. **Test with real data**
3. **Identify actual bottlenecks** 
4. **Optimize specific pain points**
5. **Repeat**

Remember: **"The best part is no part, the best process is no process"** - Build only what you need, when you need it.
