# 用户密码管理工具

这个工具集提供了通过命令行管理TradingAgents-CN用户账户的功能，包括修改密码、创建用户、删除用户等操作。

## 文件说明

- `user_password_manager.py` - 核心Python脚本
- `user_manager.bat` - Windows批处理文件
- `user_manager.ps1` - PowerShell脚本

## 使用方法

### 1. 使用Python脚本（推荐）

```bash
# 列出所有用户
python scripts/user_password_manager.py list

# 修改用户密码
python scripts/user_password_manager.py change-password admin newpassword123

# 创建新用户
python scripts/user_password_manager.py create-user newuser password123 --role user

# 创建管理员用户
python scripts/user_password_manager.py create-user newadmin adminpass123 --role admin

# 删除用户
python scripts/user_password_manager.py delete-user olduser

# 重置为默认配置
python scripts/user_password_manager.py reset
```

### 2. 使用Windows批处理文件

```cmd
# 列出所有用户
scripts\user_manager.bat list

# 修改用户密码
scripts\user_manager.bat change-password admin newpassword123

# 创建新用户
scripts\user_manager.bat create-user newuser password123 user

# 删除用户
scripts\user_manager.bat delete-user olduser

# 重置为默认配置
scripts\user_manager.bat reset
```

### 3. 使用PowerShell脚本

```powershell
# 列出所有用户
.\scripts\user_manager.ps1 list

# 修改用户密码
.\scripts\user_manager.ps1 change-password admin newpassword123

# 创建新用户
.\scripts\user_manager.ps1 create-user newuser password123 user

# 删除用户
.\scripts\user_manager.ps1 delete-user olduser

# 重置为默认配置
.\scripts\user_manager.ps1 reset
```

## 功能详解

### 列出用户 (list)
显示所有用户的详细信息，包括用户名、角色、权限和创建时间。

### 修改密码 (change-password)
修改指定用户的密码。密码会自动进行SHA256哈希处理。

**语法**: `change-password <用户名> <新密码>`

### 创建用户 (create-user)
创建新的用户账户。

**语法**: `create-user <用户名> <密码> [--role <角色>] [--permissions <权限列表>]`

**参数**:
- `--role`: 用户角色，可选值为 `user` 或 `admin`，默认为 `user`
- `--permissions`: 权限列表，如不指定则根据角色自动分配

**默认权限**:
- `user` 角色: `["analysis"]`
- `admin` 角色: `["analysis", "config", "admin"]`

### 删除用户 (delete-user)
删除指定的用户账户。为了安全，不能删除最后一个管理员用户。

**语法**: `delete-user <用户名>`

### 重置配置 (reset)
将用户配置重置为默认设置，包含以下默认用户：
- `admin` / `admin123` (管理员)
- `user` / `user123` (普通用户)

## 安全注意事项

1. **密码安全**: 所有密码都使用SHA256进行哈希处理，不会以明文形式存储
2. **权限控制**: 管理员用户拥有所有权限，普通用户只能进行分析操作
3. **备份建议**: 在进行重置操作前，建议备份现有的用户配置文件
4. **访问控制**: 确保只有授权人员能够访问这些管理工具

## 配置文件位置

用户配置文件位于: `web/config/users.json`

## 故障排除

### 1. 找不到Python
确保Python已正确安装并添加到系统PATH环境变量中。

### 2. 权限错误
在Windows上，可能需要以管理员身份运行命令提示符或PowerShell。

### 3. 配置文件不存在
工具会自动创建默认的用户配置文件，如果仍有问题，请检查文件路径和权限。

### 4. PowerShell执行策略
如果PowerShell脚本无法执行，可能需要修改执行策略：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 示例场景

### 场景1: 首次部署后修改默认密码
```bash
# 修改管理员密码
python scripts/user_password_manager.py change-password admin your_secure_password

# 修改普通用户密码
python scripts/user_password_manager.py change-password user your_user_password
```

### 场景2: 为团队添加新用户
```bash
# 添加分析师用户
python scripts/user_password_manager.py create-user analyst analyst123 --role user

# 添加新管理员
python scripts/user_password_manager.py create-user manager manager123 --role admin
```

### 场景3: 清理不需要的用户
```bash
# 删除测试用户
python scripts/user_password_manager.py delete-user testuser

# 查看当前用户列表
python scripts/user_password_manager.py list
```