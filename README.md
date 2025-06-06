# Aachen Termin Bot

这是一个用于自动检查亚琛外管局（Ausländeramt）预约时间的机器人。

## 预约流程详情

### 初始请求
request
https://termine.staedteregion-aachen.de/auslaenderamt/select2?md=1

### 页面流程
1. 起始网站页面上有html 代码：
```
<h1> Schritt 2<span class="visuallyhidden"> von 6</span>: Aufenthaltsangelegenheiten - Auswahl des Anliegens </h1>
```
选择 RWTH Studenten，然后点击 weiter。

2. 下个步骤页面上有html 代码：
```
<h1> Schritt 3<span class="visuallyhidden"> von 6</span>: Terminvorschläge - Standortauswahl </h1>
```
继续点 weiter。

3. 刷新后的页面上有html 代码：
```
<h1> Schritt 4<span class="visuallyhidden"> von 6</span>: Terminvorschläge - Keine Zeiten verfügbar </h1>
```
一般就显示 Kein freier Termin verfügbar 了。

### 预约检查序列图

```mermaid
sequenceDiagram
    participant S as Scheduler
    participant A as Appointment Service
    participant SC as SuperC Service
    participant P as Playwright
    participant W as Website

    S->>A: check_aachen_termin()
    A->>SC: check_appointment_for_position(RWTH_EMPLOYEE)
    SC->>P: sync_playwright()
    P->>W: 访问初始页面
    W-->>P: 返回页面内容
    P->>P: 提取表单token
    P->>W: 提交服务选择表单
    W-->>P: 返回搜索结果页面
    P->>P: 解析预约数据
    P-->>SC: 返回预约状态
    SC-->>A: 返回预约结果
    A-->>S: 返回最终结果
```


## 安装

1. 克隆仓库：
```bash
git clone [repository-url]
cd aachen-termin-bot
```

2. 创建并激活虚拟环境：
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 运行

```bash
source .venv/bin/activate && nohup python app.py > app.log 2>&1 &
```

```bash
python3 infostelle.py
```

应用将在 8318 端口启动（可通过环境变量 PORT 修改）。
