# Bidding AI Analyzer — 高校AI招投标文件分析系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15+-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)

一个面向市场分析的招投标信息自动化采集与 AI 分析工具。专注于高校 AI 领域的招投标项目，支持多信源采集、智能筛选和 AI 结构化分析。

## 核心功能

- **多信源采集**：自动从中国政府采购网等平台爬取招投标公告
- **智能筛选**：基于关键词漏斗精准定位高校 AI 相关项目
- **AI 结构化分析**：调用大模型自动提取 12 个关键字段（采购方、预算、中标金额、产品详情等）
- **任务式操作台**：Web 界面管理采集分析任务，浏览和导出结果
- **多线程并发**：高效处理大量招投标文件

## 系统架构

```
┌─────────────────────────────────────────────┐
│                Frontend (Next.js)            │
│           Web 操作台 / 任务管理 / 数据可视化   │
└──────────────────┬──────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────┐
│               Backend (FastAPI)              │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │  Spider   │  │  Analyzer │  │  Task Mgr  │ │
│  │  采集引擎  │  │  AI分析   │  │  任务编排   │ │
│  └──────────┘  └──────────┘  └────────────┘ │
└─────────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 20+
- DeepSeek API Key（用于 AI 分析）

### 安装与运行

```bash
# 克隆项目
git clone https://github.com/your-username/bidding-ai-analyzer.git
cd bidding-ai-analyzer

# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入你的 API Key

# 安装后端依赖
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .

# 安装前端依赖
cd ../frontend
npm install

# 启动开发环境（需要两个终端）
# 终端1: 启动后端
cd backend && uvicorn bidding_ai_analyzer.api.main:app --reload --port 8000

# 终端2: 启动前端
cd frontend && npm run dev
```

访问 http://localhost:3000 打开 Web 操作台。
API 文档自动生成于 http://localhost:8000/docs。

### Docker 部署

```bash
docker compose up -d
```

## 项目结构

```
bidding-ai-analyzer/
├── backend/                   # Python FastAPI 后端
│   └── src/bidding_ai_analyzer/
│       ├── spider/            # 爬虫框架（策略模式）
│       ├── strategies/        # 各平台搜索策略
│       ├── analyzer/          # AI 分析引擎
│       ├── api/               # REST API 路由
│       └── task_manager.py    # 任务编排
├── frontend/                  # Next.js 前端
│   └── src/
│       ├── app/               # 页面路由
│       ├── components/        # UI 组件
│       └── lib/               # API 封装 & 类型
└── docs/                      # 项目文档
```

## 文档

- [产品需求文档 (PRD)](docs/PRD.md)
- [技术架构文档](docs/ARCHITECTURE.md)

## 开源协议

MIT License — 详见 [LICENSE](LICENSE) 文件。
