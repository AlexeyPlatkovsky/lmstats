"""Command-line entry point for LM Speed Viewer."""

import argparse

import uvicorn

from .application import create_app


HOST = "127.0.0.1"
PORT = 8765


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser without performing any runtime work."""
    parser = argparse.ArgumentParser(description="Run the local LM Speed Viewer.")
    parser.add_argument("--host", default=HOST, help=f"bind address (default: {HOST})")
    parser.add_argument("--port", default=PORT, type=int, help=f"bind port (default: {PORT})")
    parser.add_argument("--db", metavar="PATH", help="SQLite history database path")
    return parser


def main(argv=None) -> None:
    """Run the viewer server with command-line configuration."""
    args = build_parser().parse_args(argv)
    options = {}
    if args.db:
        def db_path_resolver():
            return args.db

        options["db_path_resolver"] = db_path_resolver
    app = create_app(**options)
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="warning",
        timeout_graceful_shutdown=5,
    )
