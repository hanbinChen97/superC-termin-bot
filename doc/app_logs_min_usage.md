# App Logs Min 表管理说明

## 概述

`app_logs_min` 表专用管理脚本，支持表的创建、更新、删除和状态检查。不使用 Alembic，直接通过 DDL 语句管理表结构。

## 文件结构

```
db/
├── models.py              # SQLAlchemy 模型定义
├── ddl_app_logs_min.py   # DDL 语句定义
├── migrate.py            # 迁移脚本
└── utils.py              # 数据库工具函数
```

## 表结构

```sql
CREATE TABLE public.app_logs_min (
    id BIGSERIAL NOT NULL,
    log_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    level TEXT NOT NULL,
    schritt TEXT NOT NULL DEFAULT '-',
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT app_logs_min_pkey PRIMARY KEY (id),
    CONSTRAINT app_logs_min_level_check CHECK (
        level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    )
);

-- 索引
CREATE INDEX idx_app_logs_min_timestamp ON app_logs_min (log_timestamp DESC);
CREATE INDEX idx_app_logs_min_level ON app_logs_min (level);
```

### 升级已有表

如果之前已创建过没有 `schritt` 列的版本，可执行以下命令进行升级：

```sql
ALTER TABLE public.app_logs_min
    ADD COLUMN IF NOT EXISTS schritt TEXT NOT NULL DEFAULT '-';
```

## SQLAlchemy 模型

```python
from db.models import AppLogsMin

# 创建日志条目
log_entry = AppLogsMin(
    log_timestamp=datetime.now(timezone.utc),
    level="INFO",
    schritt="Schritt 2",
    message="这是一条日志消息"
)
```

## 使用方法

### 1. 管理表结构

```bash
# 检查表状态和结构
python -m db.migrate --check

# 创建 app_logs_min 表（如果不存在）
python -m db.migrate

# 更新表结构（执行 UPDATE_DDL_STATEMENTS 中的语句）
python -m db.migrate --update

# 删除表
python -m db.migrate --rollback
```

### 2. 添加表结构更新

当需要修改表结构时，编辑 `db/ddl_app_logs_min.py` 文件：

```python
# 在 UPDATE_DDL_STATEMENTS 中添加 DDL 语句
UPDATE_DDL_STATEMENTS = [
    # 添加新列
    "ALTER TABLE app_logs_min ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'application';",
    "ALTER TABLE app_logs_min ADD COLUMN IF NOT EXISTS trace_id TEXT;",
    
    # 修改列属性
    "ALTER TABLE app_logs_min ALTER COLUMN level SET NOT NULL;",
    
    # 创建新索引
    "CREATE INDEX IF NOT EXISTS idx_app_logs_min_source ON app_logs_min (source);",
    
    # 删除旧索引
    "DROP INDEX IF EXISTS idx_old_index;",
]
```

然后执行更新：

```bash
python -m db.migrate --update
```

### 3. 写入日志

```python
from db.utils import write_log

# 写入格式化日志（自动解析时间戳和级别）
write_log("2025-01-01 12:00:00,123 - INFO - Schritt 1 - 开始检查预约")

# 写入简单消息（使用当前时间和 INFO 级别）
write_log("这是一个简单的日志消息")
```

### 4. 直接使用模型

```python
from db.utils import SessionLocal
from db.models import AppLogsMin
from datetime import datetime, timezone

session = SessionLocal()
try:
    # 插入日志
    log = AppLogsMin(
        log_timestamp=datetime.now(timezone.utc),
        level="ERROR",
        schritt="Schritt 4",
        message="发生了一个错误"
    )
    session.add(log)
    session.commit()
    
    # 查询日志
    recent_logs = session.query(AppLogsMin)\
                         .order_by(AppLogsMin.log_timestamp.desc())\
                         .limit(10)\
                         .all()
    
    for log in recent_logs:
        print(f"[{log.level}] {log.log_timestamp} - {log.message}")
        
finally:
    session.close()
```

## 级别约束

系统支持以下日志级别：
- `DEBUG`
- `INFO` 
- `WARNING`
- `ERROR`
- `CRITICAL`

尝试插入其他级别会触发数据库约束错误。

## 索引优化

表包含两个索引：
1. `idx_app_logs_min_timestamp` - 按时间戳降序，用于快速查询最新日志
2. `idx_app_logs_min_level` - 按级别，用于按严重程度过滤日志

## 测试

运行测试脚本验证功能：

```bash
python test_app_logs_min.py
```

这将测试：
- 模型的基本 CRUD 操作
- 约束检查
- `write_log` 函数
- 日志解析功能

## 与现有代码集成

`write_log` 函数已经在 `db/utils.py` 中实现，可以直接在现有代码中使用，替代原来的文件日志或其他日志方案。
