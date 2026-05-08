# Bidding AI Analyzer — 技术架构文档

## 系统概览

Bidding AI Analyzer 是一个全栈 Web 应用，采用前后端分离架构：

```
Browser (React SPA)
    │
    ├─ http://localhost:3000 ──► Next.js Frontend (SSR + CSR)
    │                                │
    │                          REST API (JSON)
    │                                │
    └─ http://localhost:8000 ──► FastAPI Backend
                                     │
                              ┌──────┼──────┐
                              ▼      ▼      ▼
                           Spider  Analyzer  TaskMgr
```

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端框架 | Next.js 16 (React) | App Router + TypeScript + Tailwind CSS |
| 后端框架 | FastAPI (Python 3.10+) | 异步 REST API + 后台任务 |
| 爬虫引擎 | requests + BeautifulSoup4 | 策略模式设计，可插拔信源 |
| AI 引擎 | DeepSeek Chat / Dify | 大模型结构化信息提取 |
| 数据处理 | pandas + openpyxl | Excel 导出与数据清洗 |
| 部署 | Docker Compose | 一键启动前后端服务 |

## 后端架构

### 分层设计

```
api/                    # FastAPI 接口层
├── main.py            # 应用入口、CORS、路由注册
├── models.py          # Pydantic 请求/响应模型
└── routes/
    ├── tasks.py       # POST/GET /api/tasks
    ├── results.py     # GET /api/results/{task_id}
    └── export.py      # GET /api/export/{task_id}/excel|/csv

task_manager.py         # 后台任务编排器
                        # 串联 Stage1(采集) + Stage2(分析)

spider/                 # 爬虫模块
├── base.py            # SpiderConfig, TenderItem, BaseSearchStrategy, TenderSpider
└── utils.py           # 缓存、URL工具

strategies/             # 信源策略（策略模式）
├── ccgp.py            # 中国政府采购网
└── other.py           # 其他平台（CTBPP、ChinaBidding）

analyzer/               # AI 分析模块
└── engine.py          # TenderAnalyzer + AnalyzerRunner（多线程并发）

config.py               # 环境变量配置管理
```

### 数据流

```
1. 用户创建任务
   POST /api/tasks {keyword, start_time, end_time}
        │
2. TaskManager 创建 Task 实例
        │
3. 后台线程启动流水线:
   ┌──────────────────────────────────────────┐
   │ Stage 1: Spider                           │
   │  SpiderConfig → Strategy → TenderSpider   │
   │  → data/spider_{id}.jsonl                │
   │  → 进度: 0% → 50%                        │
   ├──────────────────────────────────────────┤
   │ Stage 2: Analyze                          │
   │  TenderAnalyzer (抓取原文→AI分析)          │
   │  → data/analyzed_{id}.jsonl              │
   │  → 进度: 50% → 100%                      │
   └──────────────────────────────────────────┘
        │
4. 前端轮询 GET /api/tasks/{id} 获取进度
        │
5. 任务完成后查看/导出结果
```

### API 设计

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/tasks/` | 创建任务并启动 |
| GET | `/api/tasks/` | 获取所有任务列表 |
| GET | `/api/tasks/{id}` | 获取单个任务状态 |
| GET | `/api/results/{id}` | 获取分析结果（分页） |
| GET | `/api/export/{id}/excel` | 导出 Excel |
| GET | `/api/export/{id}/csv` | 导出 CSV |
| GET | `/api/health` | 健康检查 |

### 任务状态机

```
pending → spidering → analyzing → completed
                ↓           ↓
              failed      failed
```

## 前端架构

### 路由结构 (App Router)

```
/                       # 仪表盘首页
/tasks                  # 任务列表
/tasks/create           # 创建任务
/tasks/[id]             # 任务详情 + 分析结果
```

### 组件树

```
RootLayout
├── Sidebar (导航)
│   ├── 仪表盘 (/)
│   ├── 任务列表 (/tasks)
│   └── 创建任务 (/tasks/create)
├── Navbar (顶栏)
└── {children} (页面内容)

Page: /
├── StatusCard × 3 (后端服务/数据信源/AI引擎)
└── QuickActionCard × 2 (创建任务/查看历史)

Page: /tasks
└── TaskTable (状态/进度/操作)

Page: /tasks/create
└── TaskForm (关键词/日期/快速关键词)

Page: /tasks/[id]
├── TaskInfo (关键词/状态/进度/数据量)
├── ExportButtons (Excel/CSV)
└── ResultTable (标题/采购方/产品/预算/供应商)
```

### 数据流

```
useEffect → api.ts → fetch → FastAPI → JSON Response
    │
    ▼
useState → Re-render Components
    │
    ▼ (任务进行中)
useTaskPolling (3s interval) → getTask(id) → update state
    │
    ▼ (任务完成)
getTaskResults(id) → display table
```

## 安全考虑

- API 密钥通过环境变量注入，不出现在源码中
- `.env` 文件已加入 `.gitignore`
- CORS 仅允许前端开发服务器来源
- API 无认证（MVP阶段，后续可添加 API Key/Token）
- 爬虫遵守目标网站的 robots.txt 和反爬策略

## 部署

### Docker Compose（推荐）

```bash
cp backend/.env.example backend/.env
# 编辑 .env 填入 API Key
docker compose up -d
```

### 手动部署

```bash
# 后端
cd backend && pip install -e . && uvicorn bidding_ai_analyzer.api.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend && npm run build && npm start
```

## 扩展性

- **新信源接入**：实现 `BaseSearchStrategy` 接口，放置于 `strategies/` 即可
- **新分析字段**：修改 `analyzer/engine.py` 中的 `PROMPT` 和 `config.py`
- **新导出格式**：在 `api/routes/export.py` 添加新路由
- **前端新页面**：在 `app/` 下添加 `page.tsx` 即可自动路由
