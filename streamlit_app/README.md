# Streamlit 预约检查工具

这是一个基于 Streamlit 构建的 SuperC Termin Bot 子项目，用于可视化展示预约检查流程。

## 功能特性

- 🎯 **可视化流程**: 通过节点展示预约检查的每个步骤
- 🚀 **一键触发**: 点击按钮即可开始完整的预约检查流程
- 📊 **实时进度**: 显示每个步骤的执行状态和详细信息
- 🔧 **灵活配置**: 支持选择不同的预约地点 (SuperC/Infostelle)
- ⚠️ **安全检查**: 仅执行到步骤4，不进行实际预约

## 流程步骤

此工具实现了原始 appointment_checker.py 中的前4个步骤:

1. **步骤 1-2**: 获取初始页面 (Schritt 1 & 2)
2. **步骤 3**: 选择地点类型 (SuperC 或 Infostelle)
3. **步骤 3**: 获取位置信息 (Schritt 3)
4. **步骤 4**: 提交位置信息并检查可用性 (Schritt 4)

## 安装和运行

### 前提条件

确保已经安装了项目的基本依赖:

```bash
cd /path/to/superC-termin-bot
pip install -r requirements.txt
pip install streamlit
```

### 启动应用

```bash
# 在项目根目录下运行
streamlit run streamlit_app/app.py
```

### 访问应用

打开浏览器访问: `http://localhost:8501`

## 使用方法

1. **选择地点**: 在左侧边栏选择预约地点 (SuperC 或 Infostelle)
2. **开始检查**: 点击 "🚀 开始预约检查" 按钮
3. **查看进度**: 在右侧面板观察流程进度和步骤详情
4. **查看结果**: 检查完成后查看是否有可用预约时间

## 项目结构

```
streamlit_app/
├── __init__.py                 # 包初始化文件
├── app.py                     # 主 Streamlit 应用
├── appointment_workflow.py    # 预约流程核心逻辑
└── README.md                  # 本文档
```

## 技术实现

- **Streamlit**: 构建 Web 界面
- **requests + BeautifulSoup**: 网页请求和解析
- **原始项目代码**: 复用 config.py 中的配置

## 注意事项

- ⚠️ 此工具仅用于检查预约可用性，不会进行实际预约
- 🌐 需要网络连接访问 termine.staedteregion-aachen.de
- 🔒 遵循原项目的 User-Agent 设置避免被反爬虫检测
- 📊 所有步骤的详细信息都会在界面中展示

## 开发说明

如需修改或扩展功能:

1. 修改 `appointment_workflow.py` 来调整流程逻辑
2. 修改 `app.py` 来调整界面布局和交互
3. 确保与主项目的 `config.py` 保持兼容

## 故障排除

如果遇到问题:

1. 检查网络连接是否正常
2. 确认所有依赖包已正确安装
3. 查看终端输出的错误信息
4. 尝试重新启动 Streamlit 应用