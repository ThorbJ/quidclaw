# QuidClaw

零门槛私人 CFO。

**本地优先。隐私至上。你的数据永远不会离开你的电脑。**

## 这是什么

QuidClaw 是一个 AI 驱动的个人财务管理工具，基于 Beancount V3 记账引擎，所有数据以纯文本存储在你的本地。它不绑定任何 AI 平台——Claude Code、Gemini CLI、OpenAI Codex、Cursor，或者任何能执行 Shell 命令的 AI 工具都能用。对开发者零成本：用户自带 AI 订阅即可。

你不需要懂复式记账，不需要学 Beancount 语法。用自然语言说一句话，AI 就帮你搞定：

```
你：午饭花了45，微信付的
AI：已记录 — 2026-03-20 午餐 ¥45.00（微信 → 餐饮）
```

## 为什么选 QuidClaw

- **隐私优先** — 所有数据存本地纯文本文件，没有云服务、没有遥测、没有数据外传
- **数据自主** — 标准 Beancount 格式，可以用 git 版本管理，随时迁移
- **零门槛** — 不需要学任何记账概念，自然语言交互
- **不绑定平台** — 任何 AI 工具都能用，换工具不丢数据
- **开发者友好** — CLI 接口，JSON 输出，方便集成

## 工作原理

```
你 → 任何 AI 工具 → 读 CLAUDE.md → 调用 quidclaw CLI → Beancount 引擎 → 本地文件
```

当你运行 `quidclaw init`，它会在当前目录生成一个完整的财务项目，包括 `CLAUDE.md` 指导文件和工作流指南。任何能读取项目指令的 AI 编程工具都能立即理解如何管理你的财务——记账、导入账单、生成报表、检测异常，全部自动化。AI 用 `quidclaw` CLI 处理账务操作，用自身的文件工具直接管理笔记、文档和收件箱。

## 功能一览

- 自然语言记账 — 说话就能记录交易
- 账单导入 — 扔进 inbox/ 文件夹，AI 自动解析入账
- 财务报表 — 月度总结、分类支出、环比对比
- 异常检测 — 重复扣费、订阅识别、异常大额、未知商户
- 对账校验 — 余额断言，确保数据准确
- 财务知识库 — AI 管理的笔记系统，记录你的财务决策和上下文
- 文档归档 — 自动整理收据、账单到按年月分类的目录
- BQL 查询 — 灵活的 Beancount 查询语言，想查什么查什么
- 多币种支持 — 人民币、美元、港币……随意混用
- 邮箱集成 — 把账单转发到专属邮箱，QuidClaw 自动同步处理
- 审计追踪 — 每笔交易都能追溯到来源文件，处理日志记录提取和确认的完整过程
- 可扩展数据源 — 支持邮箱（AgentMail）接入，架构上为未来的银行 API、券商集成预留扩展空间

## 快速开始

```bash
pip install quidclaw
mkdir ~/my-finances && cd ~/my-finances
quidclaw init
claude    # 或 gemini、codex、cursor——任何 AI 工具
```

就这样。AI 会读取生成的 `CLAUDE.md`，理解项目结构，然后开始管理你的财务。

## 支持的 AI 工具

| 工具 | 读取文件 | 状态 |
|------|----------|------|
| Claude Code / Coworker | `CLAUDE.md` | 已支持 |
| Gemini CLI | `GEMINI.md` | 计划中 |
| OpenAI Codex | `AGENTS.md` | 计划中 |
| 任何能跑 Bash 的工具 | `CLAUDE.md` | 可用 |

## 使用示例

以下是用中文和 AI 交互的真实场景：

```
你：上个月一共花了多少？

AI：2026年2月支出总结：
    总支出：¥12,847.30
    餐饮：¥3,200.50（24.9%）
    房租：¥4,500.00（35.0%）
    交通：¥1,285.00（10.0%）
    ...
    比1月多花了 ¥1,200（+10.3%）
```

```
你：帮我把 inbox 里的招商银行账单导进去

AI：找到 inbox/CMB-Statement-2026-02.csv
    解析了 47 笔交易
    全部记录到 ledger/2026/2026-02.bean
    原文件已归档到 documents/2026/02/CMB-Statement-2026-02.csv
```

```
你：查查有没有重复扣款

AI：检测到 2 个可疑项：
    1. 爱奇艺 ¥25.00 — 2月19日和2月20日各扣一次
    2. 美团外卖 ¥32.50 — 同一天同一金额出现两次
    需要我标记处理吗？
```

## 数据目录结构

```
my-finances/
├── CLAUDE.md                # AI 指导文件（自动生成）
├── .quidclaw/workflows/     # AI 工作流指南
├── ledger/                  # Beancount 账本（结构化、已验证数据）
│   ├── main.bean            #   主文件，include 所有子文件
│   ├── accounts.bean        #   账户开关指令
│   ├── prices.bean          #   价格指令
│   └── YYYY/YYYY-MM.bean   #   按月分类的交易
├── sources/                 # 外部数据源同步数据
│   └── my-email/            #   邮箱数据
├── logs/                    # 处理审计日志
├── inbox/                   # 收件箱 — 扔文件进来等 AI 处理
├── documents/               # 归档文件（按年月整理）
│   └── YYYY/MM/             #   AI 自动归档
├── notes/                   # 财务知识库（AI 管理）
│   ├── profile.md           #   用户画像（持续更新）
│   ├── calendar.md          #   还款日历（持续更新）
│   ├── assets/              #   资产记录
│   ├── liabilities/         #   负债记录
│   ├── insurance/           #   保险详情
│   ├── accounts/            #   银行卡/账户详情
│   ├── subscriptions/       #   订阅服务
│   ├── income/              #   收入来源
│   ├── decisions/           #   财务决策日志（只增不删）
│   └── journal/             #   对话摘要（只增不删）
└── reports/                 # 生成的报表
```

## CLI 命令（26 个）

大部分命令支持 `--json` 参数输出结构化数据。

### 初始化与配置

| 命令 | 说明 |
|------|------|
| `quidclaw init` | 在当前目录初始化财务项目 |
| `quidclaw upgrade` | 升级工作流和指导文件到最新版 |
| `quidclaw set-config KEY VALUE` | 设置配置项 |
| `quidclaw get-config [KEY]` | 查看配置项 |
| `quidclaw setup` | 交互式配置向导 |

### 账本操作

| 命令 | 说明 |
|------|------|
| `quidclaw add-account NAME` | 开户 |
| `quidclaw close-account NAME` | 销户 |
| `quidclaw list-accounts` | 列出所有账户（--type 过滤，--json 输出） |
| `quidclaw add-txn` | 记录交易（--date, --payee, --posting） |
| `quidclaw balance` | 查询余额（--account 指定账户，--json 输出） |
| `quidclaw balance-check ACCOUNT EXPECTED` | 对账断言 |
| `quidclaw query "SELECT ..."` | 执行 BQL 查询（--json 输出） |
| `quidclaw report income\|balance_sheet` | 生成财务报表（--period 筛选） |

### 分析与洞察

| 命令 | 说明 |
|------|------|
| `quidclaw monthly-summary YYYY MM` | 月度收支总结（--json 输出） |
| `quidclaw spending-by-category YYYY MM` | 分类支出排行（--json 输出） |
| `quidclaw month-comparison YYYY MM` | 环比变化（带百分比） |
| `quidclaw largest-txns YYYY MM` | 最大支出 Top N（--limit 设数量） |
| `quidclaw detect-anomalies` | 异常检测：重复、订阅、异常值（--json 输出） |

### 数据管理

| 命令 | 说明 |
|------|------|
| `quidclaw data-status` | 数据状态：收件箱数量、最后更新时间（--json 输出） |
| `quidclaw add-commodity NAME --source SOURCE` | 注册商品/资产用于价格追踪 |
| `quidclaw fetch-prices [COMMODITIES...]` | 获取并记录资产价格 |

### 数据源

| 命令 | 说明 |
|------|------|
| `quidclaw add-source NAME --provider PROVIDER` | 配置外部数据源 |
| `quidclaw list-sources` | 列出已配置的数据源 |
| `quidclaw remove-source NAME --confirm` | 删除数据源 |
| `quidclaw sync [SOURCE]` | 从外部数据源同步数据 |
| `quidclaw mark-processed SOURCE DIR` | 标记已处理的邮件批次 |

## 工作流（9 个）

初始化后自动安装到 `.quidclaw/workflows/`，AI 按需读取执行：

| 工作流 | 触发时机 | 说明 |
|--------|----------|------|
| `onboarding.md` | 新用户首次对话 | 问答式了解用户财务状况，内容记入笔记，不入账本 |
| `import-bills.md` | 用户上传文件或把文件放入 inbox | 解析银行流水/收据，去重，入账，归档原始文件 |
| `reconcile.md` | 生成报表前 | 检查数据完整性，执行余额断言，标记异常 |
| `monthly-review.md` | 用户要求月度总结或回顾 | 生成白话财务报告，含趋势、异常和可操作建议 |
| `detect-anomalies.md` | 用户要求检查或主动触发 | 扫描重复扣费、订阅变价、异常大额、未知商户 |
| `organize-documents.md` | inbox 积累了文件 | 把文件归档到 documents/YYYY/MM/，按规则命名 |
| `financial-memory.md` | 用户分享非交易类财务信息 | 把保险、贷款、薪资变动、财务决策记入笔记 |
| `check-email.md` | 同步触发新邮件 | 检查邮箱数据源，处理附件，带可追溯元数据入账 |
| `daily-routine.md` | 用户发起日常检查或定时触发 | 汇聚所有数据源，处理新内容，检查提醒，异常扫描 |

## 开发

```bash
git clone https://github.com/ThorbJ/quidclaw.git
cd quidclaw
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest                            # 全部测试
pytest tests/core/                # 核心逻辑测试
pytest tests/test_cli.py          # CLI 适配层测试
pytest tests/test_integration.py  # 集成测试
pytest tests/e2e/ -v -m e2e      # 端到端测试（慢，调用 AI API）
```

### 技术栈

- Python 3.10 – 3.13
- Beancount V3 — 记账引擎
- beanquery — BQL 查询
- Click — CLI 框架
- PyYAML — YAML 解析
- agentmail — 邮箱集成（可选）

## 许可证

GPL-2.0

## 作者

Yue Jiang
