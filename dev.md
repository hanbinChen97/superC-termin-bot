# 开发计划

## 配置
.env

数据库根据，next.js 项目里的 [schema.ts](https://github.com/hanbinChen97/saas-starter/blob/main/app/lib/db/schema.ts) 来定义。
- next.js 通过 Drizzle ORM 来定义，操作数据库。

[database](db/models.py)


## 流程
读取第一个 profile。

程序改成不break，预约成功后直接读取下一个 profile。  
根据时间 选择用户 功能再 check