# 集成测试说明

本项目已配置集成测试，可以自动运行 `db/utils.py` 的 `main()` 函数和 `superc.py` 的主要逻辑测试。

## 前提条件

1. **环境变量配置**: 确保项目根目录有 `.env` 文件，包含以下变量：
   ```
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=your_db_host
   DB_PORT=your_db_port
   DB_NAME=your_db_name
   ```

2. **Python 依赖**: 确保安装了所有必要的依赖：
   ```bash
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

## 测试结构

```
tests/
├── integration/
│   ├── test_database_integration.py    # 数据库集成测试 (包装 db/utils.py main())
│   └── test_superc_integration.py      # SuperC 主程序集成测试
├── run_integration_tests.py            # 专门的集成测试运行器
└── run_tests.py                        # 主测试运行器（支持多种模式）
```

## 运行测试

### 0. 快速验证（推荐第一次运行）
```bash
# 快速验证所有组件是否正常工作
python tests/quick_test.py
```

### 1. 检查环境配置
```bash
python tests/run_integration_tests.py --check-env
```

### 2. 运行集成测试

#### 运行所有集成测试
```bash
python tests/run_integration_tests.py
```

#### 只运行数据库集成测试 (db/utils.py main())
```bash
python tests/run_integration_tests.py --database-only
```

#### 只运行 SuperC 集成测试
```bash
python tests/run_integration_tests.py --superc-only
```

### 3. 使用主测试运行器

#### 运行所有测试（单元测试 + 集成测试）
```bash
python tests/run_tests.py --all
```

#### 只运行集成测试
```bash
python tests/run_tests.py --integration
```

#### 只运行单元测试（默认）
```bash
python tests/run_tests.py
# 或
python tests/run_tests.py --unit
```

### 4. 直接运行单个测试文件

#### 数据库集成测试
```bash
python tests/integration/test_database_integration.py
```

#### SuperC 集成测试
```bash
python tests/integration/test_superc_integration.py
```

## 测试内容

### 数据库集成测试 (`test_database_integration.py`)
- **包装原有功能**: 直接调用 `db/utils.py` 的 `main()` 函数
- **验证连接**: 检查数据库连接是否成功
- **验证输出**: 确保输出包含预期的信息
- **等待队列功能**: 测试等待队列相关函数

### SuperC 集成测试 (`test_superc_integration.py`)
- **模拟测试**: 使用 mock 模拟 SuperC 主逻辑
- **组件测试**: 验证各组件能正确导入和配置
- **数据库集成**: 测试与数据库的集成
- **时间检查**: 验证22点退出机制

## 输出示例

成功的测试输出会显示：
```
============================================================
运行数据库集成测试
============================================================
✓ 环境变量检查通过
test_database_connection_only ... ✓ 数据库连接测试通过
ok
test_database_utils_main_function ... ✓ 数据库 main() 函数测试通过
ok
test_waiting_queue_functions ... ✓ 等待队列功能测试通过 (当前队列长度: 2)
ok

----------------------------------------------------------------------
Ran 3 tests in 0.123s

OK
```

## 故障排除

### 1. 环境变量问题
如果看到 "缺少必要的环境变量" 错误：
- 检查 `.env` 文件是否存在于项目根目录
- 确认所有必要的数据库变量都已设置

### 2. 导入错误
如果看到 "无法导入" 错误：
- 确保在正确的虚拟环境中运行
- 检查 Python 路径是否正确

### 3. 数据库连接失败
如果数据库测试失败：
- 检查数据库服务是否运行
- 验证 `.env` 中的数据库连接信息是否正确
- 确认网络连接

## 自动化建议

可以将这些测试集成到 CI/CD 流程中：

```yaml
# GitHub Actions 示例
- name: Run Integration Tests
  run: |
    source .venv/bin/activate
    python tests/run_integration_tests.py --check-env
    python tests/run_tests.py --all
```

## 扩展测试

要添加新的集成测试：
1. 在 `tests/integration/` 目录下创建新的测试文件
2. 遵循现有的命名约定 (`test_*_integration.py`)
3. 更新相应的运行器以包含新测试 