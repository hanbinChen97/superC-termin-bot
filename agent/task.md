# 细节
现在schritt 5 的时候，有时候表单填写失败，导致无法继续。
需要在从失败的后的保存的 html，debug 然后修复程序。

# debug 过程
读取 /home/hbchen/Projects/superC-termin-bot/data/pages/。
读取 dir，获取所有文件。然后能写 python，能运行 python。读取 log，output。
通过解析 dom，通过 llm，发现问题。

## 修复
先通过保存的 HTML 进行调试，找到表单填写失败的原因。
然后 进行 主程序 修复。
然后现在 html 上测试。因为上线测试，要等网站触发我们程序才行，可能要等很久。


## 回答
claude code 已经是这样的 工具了。
我只需要定义pipeline，claude code就是 agent 会自动完成其他工作。