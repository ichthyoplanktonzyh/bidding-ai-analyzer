# Bidding AI Analyzer — University AI Procurement Analysis System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-16+-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)

An automated bidding intelligence gathering and AI analysis tool for market research. Focused on university AI procurement projects, featuring automated data collection from China's government procurement platform, intelligent keyword filtering, and structured analysis powered by DeepSeek LLM.

## Core Features

- **Government Procurement Crawling**: Automatically crawl bidding announcements from the China Government Procurement Network (CCGP) with keyword search and date range filtering
- **Smart Filtering**: Configurable keyword funnel for precise targeting of university AI-related projects, with support for custom keyword presets
- **Two-Stage Pipeline**: Stage 1 (spider collection) → user review & selection → Stage 2 (batch AI analysis), with selective analysis support
- **AI Structured Extraction**: Leverages DeepSeek LLM to automatically extract 13 key fields (purchaser, budget, winning bid amount, product details, etc.)
- **Real-Time Status Push**: WebSocket-based real-time task progress updates — no manual refresh needed
- **Multi-Threaded Concurrency**: ThreadPoolExecutor-based parallel analysis for high-throughput batch processing
- **Data Export**: Excel and CSV export for analysis results
- **Keyword Presets Management**: Built-in university keyword library with full CRUD for custom presets

## System Architecture

```
┌─────────────────────────────────────────────────┐
│              Frontend (Next.js 16)               │
│   Dashboard / Task Management / Live Progress    │
│             / Data Export                        │
│                                                  │
│  REST API + WebSocket                            │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│               Backend (FastAPI)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │  Spider   │ │ Analyzer │ │   Task Manager   │ │
│  │  Strategy │ │Multi-Thread│ │ Two-Stage Pipeline│
│  └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────────────────────────────────────────┐ │
│  │         DeepSeek API (LLM Analysis)           │ │
│  └──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 20+
- DeepSeek API Key (for AI analysis)

### Installation & Running

```bash
# Clone the repository
git clone https://github.com/ichthyoplanktonzyh/bidding-ai-analyzer.git
cd bidding-ai-analyzer

# One-command dependency setup
bash scripts/setup.sh

# Edit backend/.env and fill in your DeepSeek API Key
vim backend/.env

# One-command start (backend :8000 + frontend :3000)
bash scripts/dev.sh
```

> You can also set up and start manually — see the script contents for step-by-step instructions.

Open http://localhost:3000 for the web dashboard.
Auto-generated API docs at http://localhost:8000/docs.

### Docker Deployment

```bash
docker compose up -d
```

## Project Structure

```
bidding-ai-analyzer/
├── backend/                          # Python FastAPI backend
│   ├── .env.example                  # Environment variable template
│   ├── pyproject.toml                # Project config & dependencies
│   └── src/bidding_ai_analyzer/
│       ├── spider/                   # Spider framework (strategy pattern)
│       │   ├── base.py               # SpiderConfig / TenderSpider / BaseSearchStrategy
│       │   └── utils.py              # Cache & utility functions
│       ├── strategies/               # Platform search strategies
│       │   ├── ccgp.py               # China Government Procurement Network
│       │   └── other.py              # Other platform extensions
│       ├── analyzer/                 # AI analysis engine
│       │   └── engine.py             # TenderAnalyzer + AnalyzerRunner (multi-threaded)
│       ├── api/                      # REST API + WebSocket
│       │   ├── main.py               # App entry, CORS, WebSocket, route registration
│       │   ├── models.py             # Pydantic request/response models
│       │   └── routes/               # Route modules
│       │       ├── tasks.py          # Task CRUD + two-stage control
│       │       ├── results.py        # Analysis result queries (paginated)
│       │       ├── export.py         # Excel / CSV export
│       │       └── keywords.py       # Keyword preset management
│       ├── task_manager.py           # Background task orchestrator (singleton)
│       ├── config.py                 # Environment variable configuration
│       └── cli.py                    # CLI entry point
├── frontend/                         # Next.js 16 frontend
│   └── src/
│       ├── app/                      # App Router pages
│       │   ├── page.tsx              # Dashboard homepage
│       │   └── tasks/                # Task management
│       │       ├── page.tsx          # Task list
│       │       ├── create/page.tsx   # Create task
│       │       └── [id]/page.tsx     # Task detail + results view
│       ├── components/layout/        # Layout components (Navbar, Sidebar)
│       ├── hooks/                    # useApi / useTaskPolling
│       └── lib/                      # API client / type definitions
├── docs/                             # Documentation
│   ├── PRD.md                        # Product Requirements Document
│   └── ARCHITECTURE.md               # Technical Architecture Document
├── scripts/                          # Development helper scripts
├── docker-compose.yml                # Docker orchestration
└── LICENSE
```

## API Overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/tasks/` | Create task & start Stage 1 |
| GET | `/api/tasks/` | List all tasks |
| GET | `/api/tasks/{id}` | Get task status & progress |
| GET | `/api/tasks/{id}/spider-results` | Get Stage 1 spider results |
| POST | `/api/tasks/{id}/start-analysis` | Manually trigger Stage 2 AI analysis |
| GET | `/api/results/{id}` | Get analysis results (paginated) |
| GET | `/api/export/{id}/excel` | Export as Excel |
| GET | `/api/export/{id}/csv` | Export as CSV |
| GET | `/api/keywords/defaults` | Get default keywords |
| GET/POST/PUT/DELETE | `/api/keywords/presets` | Keyword presets CRUD |
| WS | `/ws/tasks/{id}` | Real-time status via WebSocket |

### Task State Machine

```
pending → spidering → awaiting_decision → analyzing → completed
                ↓              ↓                ↓
              failed         failed           failed
```

After Stage 1 (spider) completes, the task enters `awaiting_decision` status, allowing the user to review and select items before manually triggering Stage 2 (AI analysis).

## Documentation

- [Product Requirements Document (PRD)](docs/PRD.md) — Chinese
- [Technical Architecture Document](docs/ARCHITECTURE.md) — Chinese

## License

MIT License — see [LICENSE](LICENSE) for details.
