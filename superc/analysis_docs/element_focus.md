# 关注的 HTML 元素说明

## 项目背景
本文档描述在 Aachen Termin Bot 中需要重点关注和分析的 HTML 元素类型，用于结构化解析工作流的 AI 分析阶段。

## 主要关注元素

### 表单相关元素
- **`form`**: 主要的预约表单容器
- **`input`**: 用户输入字段（姓名、邮箱、电话等）
- **`select`**: 下拉选择框（日期、时间选择）
- **`button`**: 提交按钮和操作按钮
- **`textarea`**: 多行文本输入框

### 导航和交互元素
- **`a`**: 链接元素，特别是步骤导航链接
- **`button`**: 各种操作按钮（继续、返回、确认）
- **`nav`**: 导航菜单和面包屑

### 内容展示元素
- **`h1, h2, h3`**: 页面标题和章节标题
- **`div`**: 内容容器，特别是预约信息显示区域
- **`span`**: 行内内容，如状态标示
- **`p`**: 文本段落，包含重要说明信息

### 验证码相关元素
- **`img`**: 验证码图片
- **`input[name="captcha"]`**: 验证码输入框
- **`label`**: 验证码相关的标签

### 错误和状态元素
- **`div.error`**: 错误消息容器
- **`span.status`**: 状态指示器
- **`div.alert`**: 警告和通知信息

## 关注原因

### 预约流程关键节点
1. **表单识别**: `form` 元素包含所有用户需要填写的信息
2. **字段映射**: `input`, `select` 等元素需要与用户数据库字段对应
3. **验证码处理**: `img` 和相关 `input` 用于自动验证码识别
4. **状态监控**: 错误和状态元素用于判断操作是否成功

### 数据提取需求
- **预约时间**: 从时间选择元素中提取可用时间段
- **表单字段**: 识别所有需要填写的字段类型和名称
- **验证要求**: 识别表单验证规则和必填字段
- **错误信息**: 捕获和解析错误消息以便重试

## 典型示例

### 预约表单示例
```html
<!-- 主表单容器 -->
<form id="appointment-form" method="post" action="/submit">
  <!-- 个人信息字段 -->
  <input type="text" name="vorname" placeholder="Vorname" required>
  <input type="text" name="nachname" placeholder="Nachname" required>
  <input type="email" name="email" placeholder="E-Mail" required>
  
  <!-- 生日日期选择 -->
  <select name="geburtsdatumDay">
    <option value="1">1</option>
    <!-- ... -->
  </select>
  
  <!-- 验证码 -->
  <img src="/captcha.png" alt="Captcha" id="captcha-image">
  <input type="text" name="captcha_code" placeholder="验证码">
  
  <!-- 提交按钮 -->
  <button type="submit" class="btn-primary">Reservieren</button>
</form>
```

### 时间选择示例
```html
<!-- 可用时间列表 -->
<div class="available-times">
  <h2>Verfügbare Termine</h2>
  <div class="time-slot" data-time="2024-01-15T10:00">
    <span class="date">15.01.2024</span>
    <span class="time">10:00</span>
    <button class="select-time">Auswählen</button>
  </div>
</div>
```

### 错误处理示例
```html
<!-- 错误消息显示 -->
<div class="error-message" style="display: block;">
  <span class="error-text">Bitte füllen Sie alle Pflichtfelder aus.</span>
</div>

<!-- 验证码错误 -->
<div id="error_captcha" class="error-text">
  Der eingegebene Code ist falsch.
</div>
```

## AI 分析指导原则

### 优先级排序
1. **高优先级**: form, input, button, select - 直接影响预约功能
2. **中优先级**: img (验证码), div.error - 影响成功率
3. **低优先级**: nav, h1-h3 - 用于页面状态判断

### 属性重要性
- **name**: 最重要，用于字段映射
- **id**: 次重要，用于元素定位
- **class**: 用于样式和功能判断
- **type**: 用于确定输入类型
- **required**: 用于验证必填字段

### 文本内容分析
- **按钮文本**: 用于确定操作类型（"Weiter", "Zurück", "Reservieren"）
- **错误文本**: 用于判断错误类型和原因
- **标签文本**: 用于理解字段含义

## 输出格式要求

AI 分析结果应包含以下信息：
```json
{
  "elements": [
    {
      "id": 123,
      "tag": "input",
      "text": "",
      "attrs": {
        "name": "vorname",
        "type": "text",
        "required": true
      },
      "reason": "用户姓名输入字段，必填项"
    }
  ]
}
```

## 更新记录
- 2024-01-01: 初始版本，基于现有预约系统需求
- 待更新: 根据实际测试结果优化关注点