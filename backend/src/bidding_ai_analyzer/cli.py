"""CLI entry point for bidding-ai-analyzer."""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Bidding AI Analyzer - 高校AI招投标分析系统"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # spider command
    spider_parser = subparsers.add_parser("spider", help="Run data collection spider")
    spider_parser.add_argument("--keyword", "-k", required=True, help="Search keyword (e.g. AI, 人工智能)")
    spider_parser.add_argument("--start-time", help="Start date (YYYY-MM-DD)")
    spider_parser.add_argument("--end-time", help="End date (YYYY-MM-DD)")
    spider_parser.add_argument("--max-pages", type=int, default=100, help="Max pages to crawl")
    spider_parser.add_argument("--output", "-o", default="data/spider_output.jsonl", help="Output file path")

    # analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Run AI analysis on collected data")
    analyze_parser.add_argument("--input", "-i", required=True, help="Input JSONL file from spider")
    analyze_parser.add_argument("--output", "-o", default="data/analyzed_results.jsonl", help="Output file path")
    analyze_parser.add_argument("--max-workers", type=int, default=10, help="Concurrent worker threads")
    analyze_parser.add_argument("--max-records", type=int, default=None, help="Max records to process")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start FastAPI server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    serve_parser.add_argument("--port", type=int, default=8000, help="Bind port")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    if args.command == "spider":
        from .spider.base import SpiderConfig, TenderSpider
        from .strategies.ccgp import CCGPSearchStrategy

        config = SpiderConfig(
            keyword=args.keyword,
            start_time=args.start_time,
            end_time=args.end_time,
            filter_keywords=['大学', '学院', '高职', '职业技术', '职业学院', '师范', '理工', '经贸', '学校'],
            max_pages=args.max_pages,
        )
        strategy = CCGPSearchStrategy(config)
        spider = TenderSpider(strategy, config)
        spider.run()
        spider.save_to_jsonl(args.output)
        print(f"Done. Output saved to {args.output}")

    elif args.command == "analyze":
        from .analyzer.engine import AnalyzerRunner
        runner = AnalyzerRunner(
            max_workers=args.max_workers,
            request_delay=1.5,
        )
        runner.run(args.input, args.output, max_records=args.max_records)

    elif args.command == "serve":
        import uvicorn
        uvicorn.run(
            "bidding_ai_analyzer.api.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
        )

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
