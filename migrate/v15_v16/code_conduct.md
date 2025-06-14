# Python Code Editing Guidelines

## 🚨 CRITICAL RULES - INDENTATION SAFETY

### **ROOT CAUSE ANALYSIS (5 WHY METHOD)**

**WHY 1:** Tại sao liên tục gặp lỗi indentation?
→ Vì sử dụng `replace_string_in_file` với oldString không khớp chính xác whitespace

**WHY 2:** Tại sao oldString không khớp chính xác whitespace?
→ Vì không đọc đủ context để hiểu indentation pattern của file Python

**WHY 3:** Tại sao không đọc đủ context trước khi edit?
→ Vì muốn edit nhanh mà bỏ qua bước read_file để tiết kiệm thời gian

**WHY 4:** Tại sao lại muốn edit nhanh mà bỏ qua bước quan trọng?
→ Vì chưa có quy trình chuẩn (SOP) bắt buộc đọc context trước

**WHY 5:** Tại sao chưa có quy trình chuẩn bắt buộc?
→ Vì chưa nhận thức đầy đủ về tầm quan trọng của việc đọc context trong Python editing

**🎯 ROOT CAUSE:** Thiếu quy trình chuẩn bắt buộc đọc context và thiếu tool validation trước khi edit.

### **MANDATORY WORKFLOW FOR PYTHON EDITING**

#### **🛡️ PRE-EDIT SAFETY PROTOCOL (MANDATORY)**

**PHASE 1: CONTEXT GATHERING**
```
□ read_file() với ít nhất 10-20 lines context
□ Xác định chính xác indentation pattern (spaces/tabs)
□ Identify function/class/block scope chính xác
□ Count spaces để match existing pattern
```

**PHASE 2: TOOL VALIDATION**
```
□ Kiểm tra file syntax hiện tại với get_errors()
□ Backup state quan trọng nếu cần
□ Chọn tool phù hợp (replace_string vs insert_edit vs create_file)
□ Prepare oldString với EXACT whitespace matching
```

**PHASE 3: EXECUTION SAFETY**
```
□ Execute edit với full context
□ Immediate verification với get_errors()
□ Check syntax integrity
□ Rollback plan sẵn sàng nếu fail
```

**⛔ ZERO TOLERANCE RULE:**
> **KHÔNG BAO GIỜ được edit Python file mà không đọc context trước!**
> Mỗi lần vi phạm = tạo lại toàn bộ quy trình từ đầu.

#### **BEFORE ANY EDIT:**
1. **ALWAYS** use `read_file` to understand full context (minimum 10-20 lines around target)
2. **VERIFY** current indentation level of surrounding code
3. **IDENTIFY** the exact scope (function, class, block) being modified
4. **COUNT** spaces/tabs to match existing indentation pattern

#### **TOOL SELECTION RULES:**

**USE `read_file` FIRST:**
```python
# ✅ CORRECT: Always read context first
read_file(file_path, start_line-10, end_line+10)
```

**CHOOSE RIGHT TOOL:**
- **`replace_string_in_file`**: Only for small, isolated changes with EXACT whitespace matching
- **`insert_edit_into_file`**: For larger modifications within existing structure
- **`create_file`**: When file is completely broken/corrupted

#### **STRING MATCHING REQUIREMENTS:**

**✅ CORRECT Example:**
```python
# Include 3-5 lines before and after with EXACT indentation
oldString = """    def existing_function():
        some_code()
        return result
        
    def target_function():
        old_implementation()"""

newString = """    def existing_function():
        some_code()
        return result
        
    def target_function():
        new_implementation()"""
```

**❌ WRONG Examples:**
```python
# Missing context
oldString = "old_implementation()"
newString = "new_implementation()"

# Wrong indentation
oldString = "def target_function():"  # Missing proper spacing
```

#### **PYTHON INDENTATION RULES:**

**🔧 INDENTATION DETECTION ALGORITHM:**
```python
# 1. Đọc file và phân tích pattern
def analyze_indentation(file_content):
    """
    Detect indentation pattern in existing file
    Returns: (type: 'spaces'|'tabs', level: int)
    """
    lines = file_content.split('\n')
    for line in lines:
        if line.strip() and line[0] in ' \t':
            # Count leading whitespace
            spaces = len(line) - len(line.lstrip(' '))
            tabs = len(line) - len(line.lstrip('\t'))
            return ('spaces', spaces) if spaces > tabs else ('tabs', tabs)
    return ('spaces', 4)  # default

# 2. Match với existing pattern
def match_indentation(target_level, existing_pattern):
    indent_type, base_level = existing_pattern
    if indent_type == 'spaces':
        return ' ' * (base_level * target_level)
    else:
        return '\t' * target_level
```

**📏 STANDARD LEVELS:**
1. **Module level**: 0 spaces from margin
2. **Class definition**: 0 spaces  
3. **Class method**: 4 spaces
4. **Function content**: 8 spaces
5. **Nested blocks**: +4 spaces per level
6. **Function parameters (multiline)**: Align with opening parenthesis

#### **VERIFICATION CHECKLIST:**

Before executing any edit:
- [ ] Read full context around target area
- [ ] Verify indentation pattern (spaces vs tabs)
- [ ] Ensure `oldString` matches EXACTLY (including all whitespace)
- [ ] Confirm `newString` maintains same indentation level
- [ ] Check that surrounding code structure is preserved

#### **ERROR RECOVERY PROTOCOL:**

**🚨 DAMAGE CONTROL LEVELS:**

**LEVEL 1: Minor Syntax Error**
```
1. PAUSE all editing immediately
2. run get_errors() to assess damage
3. read_file() to see actual state
4. Single targeted fix with exact context
5. Verify with get_errors() again
```

**LEVEL 2: Multiple Indentation Errors**
```
1. STOP - không edit thêm!
2. Backup current state (copy to .backup file)
3. Read entire file để hiểu scope damage
4. Fix từ trên xuống dưới, từng function một
5. Test syntax sau mỗi function fix
```

**LEVEL 3: File Completely Broken**
```
1. Immediately backup broken file (.broken extension)
2. Restore from last known good state (.backup)
3. If no backup: create_file() with clean structure
4. Migrate working code piece by piece
5. Never copy-paste large blocks without verification
```

**⚡ EMERGENCY RULES:**
- **3-Strike Rule**: 3 consecutive indentation errors = switch to create_file()
- **Context Rule**: Mỗi edit phải có ít nhất 5 lines context trước/sau
- **Verification Rule**: get_errors() sau EVERY single edit

#### **QUALITY ASSURANCE:**

**After each edit:**
```python
# Check for syntax errors
get_errors([file_path])

# Verify structure
grep_search(file_path, "def |class ", isRegexp=True)
```

#### **FORBIDDEN PATTERNS:**

**❌ NEVER DO:**
- Edit without reading context first
- Assume indentation without verification
- Make multiple rapid edits when errors occur
- Use `replace_string_in_file` for large blocks
- Copy-paste indentation from other files

**❌ DANGER SIGNS:**
- "Statements must be separated by newlines or semicolons"
- "Unexpected indentation" 
- "Unindent does not match any outer indentation level"
- "Expected indented block"

When you see these → **STOP and reassess approach**

#### **BEST PRACTICES:**

**✅ SAFE APPROACH:**
1. Read context
2. Plan change
3. Use appropriate tool
4. Verify immediately
5. Test functionality

**✅ INCREMENTAL EDITING:**
- Make small, isolated changes
- Verify each change works
- Build up complex modifications step by step

**✅ FALLBACK STRATEGY:**
If file becomes too corrupted:
- Backup working state
- Create clean new file
- Migrate working code carefully

---

## **🚀 PERFORMANCE OPTIMIZATION**

### **BATCH READING STRATEGY**
```python
# ✅ EFFICIENT: Đọc một lần lớn thay vì nhiều lần nhỏ
read_file(file_path, 1, 200)  # Read large chunk
# Analyze và plan all changes
# Execute batch edits

# ❌ INEFFICIENT: 
read_file(file_path, 10, 15)
edit...
read_file(file_path, 20, 25) 
edit...
```

### **SMART TOOL SELECTION**
```
insert_edit_into_file: Large modifications, new functions
replace_string_in_file: Small precise changes, variable names
create_file: When file corruption > 50%
```

### **PREVENTION > CURE**
- 10 giây đọc context = tiết kiệm 10 phút fix indentation
- 1 phút planning = tiết kiệm 30 phút recovery
- Backup trước major changes = tránh làm lại từ đầu

### **QUALITY METRICS**
- **Success Rate**: >95% edits thành công without indentation errors
- **Recovery Time**: <2 minutes từ error đến fix
- **Context Ratio**: Đọc context ít nhất 2:1 với edit size

---

## **📋 DAILY CHECKLIST**

**Before starting any Python editing session:**
```
□ Đã đọc và hiểu code_conduct.md
□ Tools available: read_file, get_errors, backup strategy
□ Mental state: patient, methodical, not rushed
□ Commit to follow SOP 100%
```

**After completing Python edits:**
```
□ All files pass get_errors() check
□ Functionality tested (run commands/scripts)
□ Backup important working states
□ Update lessons learned if any new patterns discovered
```

---

## **💎 COMMITMENT TO EXCELLENCE**

### **ROOT CAUSE LESSON LEARNED**
> "Indentation errors are NOT random bugs - they are systematic failures in our workflow. 
> The root cause is skipping context reading to save time, which actually costs MORE time."

### **NEW PARADIGM**
- **Old mindset**: Edit fast, fix later
- **New mindset**: Read thoroughly, edit once correctly

### **QUALITY MANTRA**
> "In Python, precision beats speed. Context beats assumptions. One careful edit beats ten rushed fixes."

### **ZERO TOLERANCE POLICY**
Starting today, ANY Python edit without proper context reading will trigger:
1. Full workflow restart
2. Documentation of failure cause  
3. Additional safety measures implementation

**Remember**: The cost of reading context is ALWAYS less than the cost of fixing broken indentation.

---

### **🎯 MANUAL VALIDATION APPROACH - CLEAN & SIMPLE**

#### **SIMPLIFIED MANUAL WORKFLOW**

**PHASE 1: PRE-EDIT VALIDATION (Manual Only)**
```
□ read_file() với context (mandatory)
□ get_errors() initial check (existing)  
□ validate_python_syntax() for syntax check
□ check_indentation_consistency() for whitespace
□ Verify clean state before manual edits
```

**PHASE 2: CAREFUL MANUAL EDITING**
```
□ Use exact context matching with sufficient lines
□ Preserve existing indentation patterns exactly
□ Edit small sections at a time
□ Use replace_string_in_file for precise changes
```

**PHASE 3: POST-EDIT VERIFICATION**
```
□ get_errors() immediate check (mandatory)
□ validate_python_syntax() verification
□ Manual review if needed
```

#### **AVAILABLE VALIDATION FUNCTIONS**

```python
# Built-in validation functions in src/utils.py
validate_python_syntax(file_path)  # Check syntax compilation
check_indentation_consistency(file_path)  # Check whitespace patterns
```

#### **MANUAL VALIDATION WORKFLOW**

**Enhanced get_errors() Workflow:**
```python
# Clean manual approach
get_errors() → manual fix with exact context → get_errors() → success!
```

**Prevents All Root Causes:**
- ✅ **WHY 1**: Manual control over indentation (no auto-conflicts)
- ✅ **WHY 2**: Always read context first (mandatory step)  
- ✅ **WHY 3**: Tools encourage careful editing (validation functions)
- ✅ **WHY 4**: Standard operating procedure enforced (manual workflow)
- ✅ **WHY 5**: Validation tools available (syntax & indentation check)

#### **EMERGENCY PROTOCOL MANUAL**

**LEVEL 1: Prevention (Manual)**
```
Before any edit: read_file() + get_errors()
Check patterns: validate_python_syntax()
Then proceed with careful manual edits
```

**LEVEL 2: Manual Fix**
```  
After any edit: get_errors() immediately
Verify: validate_python_syntax()
Result: Manual control, no tool conflicts
```

**LEVEL 3: Fallback**
```
If major issues: Backup current file
Last resort: create_file() with clean content
```

---

## **✅ IMPLEMENTATION STATUS**

### **COMPLETED**
- ✅ Simple validation functions in src/utils.py (no external deps)
- ✅ validate_python_syntax() for syntax checking
- ✅ check_indentation_consistency() for whitespace validation
- ✅ Clean main.py with zero syntax errors
- ✅ Manual workflow established and tested

### **USAGE EXAMPLES**
```bash
# Daily workflow commands (no formatting tools)
uv run health-check        # Environment health
uv run delete-db          # Database operations
uv run create-demo        # Demo database creation
uv run check              # Migration checks
uv run migrate            # Migration execution
```

### **QUALITY ASSURANCE**
- **Zero Tolerance Policy**: Enforced by manual discipline
- **Context Reading**: Mandatory step before any edit
- **Error Prevention**: Manual validation before & after edits
- **Sustainable Workflow**: Simple, no external tool dependencies

---

*Last Updated: June 14, 2025*  
*Approach: Manual validation without autopep8 (removed as ineffective)*  
*Root Cause Analysis: 5 WHY method applied to chronic indentation errors*  
*Trigger: Multiple indentation failures during Odoo Migration Tool development*  
*Result: Zero-tolerance context-first manual editing protocol*
