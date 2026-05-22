# Bidding AI Analyzer —— 技术架构文档

## 系统概览

Bidding AI Analyzer 是一个全栈 Web 应用，采用前后端分离架构，通过 REST API + WebSocket 实现实时通信。

```
Browser (Next.js SPA)
    │
    ├─ http://localhost:3000 ──► Next.js 16 Frontend (App Router)
    │                                │
    │                  REST API (JSON) + WebSocket
    │                                │
    └─ http://localhost:8000 ──► FastAPI Backend
                                     │
                              ┌──────┼──────┐
                              ▼      ▼      ▼
                           Spider  Analyzer  TaskMgr
                            (策略模式) (多线程)  (两阶段编排)
```

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端框架 | Next.js 16 + React 19 | App Router + TypeScript + Tailwind CSS 4 |
| 后端框架 | FastAPI (Python 3.10+) | 异步 REST API + WebSocket + 后台线程 |
| 爬虫引擎 | requests + BeautifulSoup4 | 策略模式设计，可插拔信源 |
| AI 引擎 | DeepSeek Chat API | 大模型结构化信息提取（13 字段） |
| 数据处理 | pandas + openpyxl | Excel / CSV 导出与数据清洗 |
| 部署 | Docker Compose | 一键启动前后端服务 |

## 后端架构

### 分层设计

```
api/                         # FastAPI 接口层
├── main.py                  # 应用入口、CORS、WebSocket、路由注册
├── models.py                # Pydantic 请求/响应模型
└── routes/
    ├── tasks.py             # 任务 CRUD + Stage 2 触发
    ├── results.py           # 分析结果查询（分页）
    ├── export.py            # Excel / CSV 导出
    └── keywords.py          # 关键词预设 CRUD

task_manager.py              # 后台任务编排器（单例模式）
                             # 两阶段流水线：Spider → AwaitDecision → Analyzer

spider/                      # 爬虫模块
├── base.py                  # SpiderConfig, TenderItem, BaseSearchStrategy, TenderSpider
└── utils.py                 # 缓存、URL 工具函数

strategies/                  # 信源策略（策略模式）
├── ccgp.py                  # 中国政府采购网 (search.ccgp.gov.cn)
└── other.py                 # 其他平台扩展（CTBPP、ChinaBidding 等）

analyzer/                    # AI 分析模块
└── engine.py                # TenderAnalyzer（单条分析）+ AnalyzerRunner（多线程批量）

config.py                    # 环境变量配置管理 + 默认关键词
```

### 两阶段流水线

```
用户创建任务
  │ POST /api/tasks {keyword, start_time, end_time, filter_keywords}
  │
  ▼
TaskManager.create_task() → Task (status=pending)
  │
  ▼
后台线程: run_pipeline()
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ Stage 1: Spider（爬虫采集）                               │
│  SpiderConfig → CCGPSearchStrategy → TenderSpider.run()  │
│  - 分页爬取搜索结果                                        │
│  - 关键词过滤                                             │
│  - 去重 + 增量缓存                                        │
│  - 进度: 0% → 50%                                        │
│  - 实时写入 spider_results 供前端展示                      │
│  - 输出: data/spider_{id}.jsonl                          │
│                                                         │
│  状态: spidering → awaiting_decision                     │
└─────────────────────────────────────────────────────────┘
  │
  │ （用户在前端查看采集结果，筛选后手动触发 Stage 2）
  │ POST /api/tasks/{id}/start-analysis {selected_indices?}
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ Stage 2: Analyze（AI 分析）                                │
│  AnalyzerRunner(max_workers=10, request_delay=1.5s)       │
│  - ThreadPoolExecutor 多线程并发                          │
│  - TenderAnalyzer.fetch_url_content() 抓取原文             │
│  - TenderAnalyzer.analyze_tender() 调用 DeepSeek API      │
│  - 增量写入结果（线程安全）                                 │
│  - 进度: 50% → 100%                                       │
│  - 输出: data/analyzed_{id}.jsonl                         │
│                                                         │
│  状态: analyzing → completed                             │
└─────────────────────────────────────────────────────────┘
```

### 任务状态机

```
pending ──► spidering ──► awaiting_decision ──► analyzing ──► completed
                │                │                    │
                ▼                ▼                    ▼
              failed           failed               failed
```

- **pending**: 任务已创建，等待启动
- **spidering**: Stage 1 进行中，爬虫正在采集数据
- **awaiting_decision**: Stage 1 完成，等待用户查看结果并决定触发分析
- **analyzing**: Stage 2 进行中，AI 正在批量分析
- **completed**: 全流程完成
- **failed**: 任意阶段出错

### API 设计

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/tasks/` | 创建任务并启动 Stage 1 |
| GET | `/api/tasks/` | 获取所有任务列表 |
| GET | `/api/tasks/{id}` | 获取单个任务状态与进度 |
| GET | `/api/tasks/{id}/spider-results` | 获取 Stage 1 采集结果 |
| POST | `/api/tasks/{id}/start-analysis` | 手动触发 Stage 2（可选 selected_indices） |
| GET | `/api/results/{id}` | 获取分析结果（分页: offset/limit） |
| GET | `/api/export/{id}/excel` | 导出 Excel（StreamingResponse） |
| GET | `/api/export/{id}/csv` | 导出 CSV（StreamingResponse） |
| GET | `/api/keywords/defaults` | 获取系统默认推荐关键词 |
| GET | `/api/keywords/presets` | 列出所有关键词预设 |
| POST | `/api/keywords/presets` | 创建关键词预设 |
| PUT | `/api/keywords/presets/{id}` | 更新关键词预设 |
| DELETE | `/api/keywords/presets/{id}` | 删除关键词预设 |

### WebSocket

```
WS /ws/tasks/{task_id}
```

实时推送任务状态更新，每秒轮询一次任务状态并推送：

```json
{
  "type": "status_update",
  "task_id": "abc123",
  "status": "spidering",
  "progress": 35,
  "total_items": 120,
  "analyzed_items": 0,
  "spider_item_count": 45,
  "error": null,
  "timestamp": 1715872000.0
}
```

任务完成或失败时发送 `pipeline_complete` 事件并关闭连接。

### AI 分析 Prompt 设计

分析引擎通过精心设计的 System Prompt 引导 DeepSeek 模型提取 13 个结构化字段：

| 字段 | 说明 |
|------|------|
| `project_status` | 项目状态（招标中/已中标/已废标等） |
| `tender_release_date` | 招标公告发布日期 |
| `bid_award_date` | 中标公告日期 |
| `purchasing_entity` | 采购方（通常为高校名称） |
| `project_name` | 项目正式名称 |
| `purchaser_info` | 采购方联系方式 |
| `product_type` | 产品/服务详情（重点关注 AI 相关） |
| `budget_amount` | 预算金额 |
| `winning_bid_amount` | 中标金额 |
| `supplier_name` | 中标供应商 |
| `procurement_type` | 采购类型（公开招标/竞争性谈判等） |
| `tender_notice_url` | 公告链接 |
| `procurement_documents` | 采购文件信息 |

模型 temperature 设置为 0.1 以保证提取结果的稳定性和一致性。

## 前端架构

### 路由结构 (App Router)

```
/                       # 仪表盘首页
/tasks                  # 任务列表
/tasks/create           # 创建任务（关键词、日期、筛选条件）
/tasks/[id]             # 任务详情（实时进度 + 采集结果 + 分析结果）
```

### 组件树

```
RootLayout
├── Sidebar（导航菜单）
│   ├── 仪表盘 (/)
│   ├── 任务列表 (/tasks)
│   └── 创建任务 (/tasks/create)
├── Navbar（顶部导航栏）
└── {children}（页面内容）

Page: /（仪表盘）
├── 系统状态卡片（后端/AI 引擎）
└── 快捷操作入口

Page: /tasks（任务列表）
└── 任务表格（状态标签/进度条/操作按钮）

Page: /tasks/create（创建任务）
├── 关键词输入
├── 日期范围选择
├── 筛选关键词预设选择/自定义
└── 提交按钮

Page: /tasks/[id]（任务详情）
├── 任务信息卡片（关键词/状态/进度）
├── Stage 1 采集结果列表（用户可筛选）
├── Stage 2 触发按钮
├── 分析结果表格（13 字段展示）
└── 导出按钮（Excel/CSV）
```

### 数据流

```
                    ┌── WebSocket（实时状态推送）──┐
                    │                             │
useEffect → api.ts → fetch → FastAPI → JSON Response
    │                                              │
    ▼                                              ▼
useState → Re-render Components          useTaskPolling（降级方案，3s 轮询）
    │
    ▼（任务完成后）
getTaskResults(id) → 渲染结果表格
```

前端通过 WebSocket 获取实时进度更新，当 WebSocket 不可用时自动降级为 HTTP 轮询（`useTaskPolling` hook，每 3 秒请求一次 GET `/api/tasks/{id}`）。

### 自定义 Hooks

| Hook | 用途 |
|------|------|
| `useApi` | 通用 API 请求封装，管理 loading/error/data 状态 |
| `useTaskPolling` | 任务进度轮询，WebSocket 优先 + HTTP 降级 |

## 扩展性

- **新信源接入**：实现 `BaseSearchStrategy` 抽象类（6 个方法），放置于 `strategies/` 即可
- **新分析字段**：修改 `analyzer/engine.py` 中的 `PROMPT` 和 `config.py` 默认值
- **新导出格式**：在 `api/routes/export.py` 添加新路由
- **前端新页面**：在 `app/` 下添加 `page.tsx` 即可自动路由

## 安全考虑

- API 密钥通过 `.env` 环境变量注入，`backend/.env` 已加入 `.gitignore`
- CORS 仅允许前端开发服务器来源（localhost:3000/3001）
- API 无认证（MVP 阶段，后续可添加 API Key / Token）
- 爬虫遵守反爬策略（请求间隔 3-8s 随机延迟、重试机制、反爬检测）

## 部署

### Docker Compose（推荐）

```bash
cp backend/.env.example backend/.env
# 编辑 .env 填入 DeepSeek API Key
docker compose up -d
```

### 手动部署

```bash
# 后端
cd backend && pip install -e . && uvicorn bidding_ai_analyzer.api.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend && npm run build && npm start
```
