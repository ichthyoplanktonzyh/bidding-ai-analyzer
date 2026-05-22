# Bidding AI Analyzer —— 高校AI招投标文件分析系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-16+-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)

面向市场分析的招投标信息自动化采集与 AI 分析工具。专注于高校 AI 领域的招投标项目，支持中国政府采购网数据采集、关键词智能筛选和 DeepSeek 大模型结构化分析。

## 核心功能

- **政府采购网采集**：自动从中国政府采购网爬取招投标公告，支持关键词搜索和日期范围过滤
- **智能筛选**：基于可配置关键词漏斗精准定位高校 AI 相关项目，支持自定义关键词预设
- **两阶段流水线**：Stage 1 爬虫采集 → 用户筛选 → Stage 2 AI 批量分析，支持选择性分析
- **AI 结构化提取**：调用 DeepSeek 大模型自动提取 12 个关键字段（采购方、预算、中标金额、产品详情等）
- **实时状态推送**：WebSocket 实时推送任务进度，无需手动刷新
- **多线程并发**：ThreadPoolExecutor 并发分析，大幅提升大批量数据处理效率
- **数据导出**：支持 Excel / CSV 格式导出分析结果
- **关键词预设管理**：内置高校关键词词库，支持自定义预设的增删改查

## 系统架构

```
┌─────────────────────────────────────────────────┐
│              Frontend (Next.js 16)               │
│     Web 操作台 / 任务管理 / 实时进度 / 数据导出     │
│                                                  │
│  REST API + WebSocket                            │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│               Backend (FastAPI)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │  Spider   │ │ Analyzer │ │   Task Manager   │ │
│  │  策略模式  │ │ 多线程AI  │ │  两阶段流水线编排  │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────────────────────────────────────────┐ │
│  │         DeepSeek API (大模型分析)              │ │
│  └──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 20+
- DeepSeek API Key（用于 AI 分析）

### 安装与运行

```bash
# 克隆项目
git clone https://github.com/ichthyoplanktonzyh/bidding-ai-analyzer.git
cd bidding-ai-analyzer

# 一键安装依赖
bash scripts/setup.sh

# 编辑 backend/.env，填入你的 DeepSeek API Key
vim backend/.env

# 一键启动开发环境（后端 :8000 + 前端 :3000）
bash scripts/dev.sh
```

> 也可手动逐步安装和启动，详见上方脚本内容。

访问 http://localhost:3000 打开 Web 操作台。
API 文档自动生成于 http://localhost:8000/docs。

### Docker 部署

```bash
docker compose up -d
```

## 项目结构

```
bidding-ai-analyzer/
├── backend/                          # Python FastAPI 后端
│   ├── .env.example                  # 环境变量模板
│   ├── pyproject.toml                # 项目配置与依赖
│   └── src/bidding_ai_analyzer/
│       ├── spider/                   # 爬虫框架（策略模式）
│       │   ├── base.py               # SpiderConfig / TenderSpider / BaseSearchStrategy
│       │   └── utils.py              # 缓存与工具函数
│       ├── strategies/               # 平台搜索策略
│       │   ├── ccgp.py               # 中国政府采购网
│       │   └── other.py              # 其他平台扩展
│       ├── analyzer/                 # AI 分析引擎
│       │   └── engine.py             # TenderAnalyzer + AnalyzerRunner（多线程）
│       ├── api/                      # REST API + WebSocket
│       │   ├── main.py               # 应用入口、CORS、WebSocket
│       │   ├── models.py             # Pydantic 模型
│       │   └── routes/               # 路由模块
│       │       ├── tasks.py          # 任务 CRUD + 两阶段控制
│       │       ├── results.py        # 分析结果查询（分页）
│       │       ├── export.py         # Excel / CSV 导出
│       │       └── keywords.py       # 关键词预设管理
│       ├── task_manager.py           # 后台任务编排（单例）
│       ├── config.py                 # 环境变量配置
│       └── cli.py                    # 命令行入口
├── frontend/                         # Next.js 16 前端
│   └── src/
│       ├── app/                      # App Router 页面
│       │   ├── page.tsx              # 仪表盘首页
│       │   └── tasks/                # 任务管理
│       │       ├── page.tsx          # 任务列表
│       │       ├── create/page.tsx   # 创建任务
│       │       └── [id]/page.tsx     # 任务详情 + 结果查看
│       ├── components/layout/        # 布局组件
│       ├── hooks/                    # useApi / useTaskPolling
│       └── lib/                      # API 封装 / 类型定义
├── docs/                             # 项目文档
│   ├── PRD.md                        # 产品需求文档
│   └── ARCHITECTURE.md               # 技术架构文档
├── scripts/                          # 开发辅助脚本
├── docker-compose.yml                # Docker 编排
└── LICENSE
```

## API 概览

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/tasks/` | 创建任务并启动 Stage 1 |
| GET | `/api/tasks/` | 获取所有任务列表 |
| GET | `/api/tasks/{id}` | 获取任务状态与进度 |
| GET | `/api/tasks/{id}/spider-results` | 获取 Stage 1 采集结果 |
| POST | `/api/tasks/{id}/start-analysis` | 手动触发 Stage 2 AI 分析 |
| GET | `/api/results/{id}` | 获取分析结果（分页） |
| GET | `/api/export/{id}/excel` | 导出 Excel |
| GET | `/api/export/{id}/csv` | 导出 CSV |
| GET | `/api/keywords/defaults` | 获取默认关键词 |
| GET/POST/PUT/DELETE | `/api/keywords/presets` | 关键词预设 CRUD |
| WS | `/ws/tasks/{id}` | WebSocket 实时状态推送 |

### 任务状态机

```
pending → spidering → awaiting_decision → analyzing → completed
                ↓              ↓                ↓
              failed         failed           failed
```

Stage 1（爬虫采集）完成后进入 `awaiting_decision` 状态，用户可筛选数据后手动触发 Stage 2（AI 分析）。

## 文档

- [产品需求文档 (PRD)](docs/PRD.md)
- [技术架构文档](docs/ARCHITECTURE.md)

## 开源协议

MIT License —— 详见 [LICENSE](LICENSE) 文件。
