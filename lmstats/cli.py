"""Command-line entry point for LM Stats Viewer."""

import argparse
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version as get_version

import uvicorn

from .application import create_app


HOST = "127.0.0.1"
PORT = 8765
PACKAGE_NAME = "lmstats"
NPM_PACKAGE = "lmstats"


def _version() -> str:
    """Return the installed package version, or 'unknown' if not installed."""
    try:
        return get_version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "unknown"


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser without performing any runtime work."""
    parser = argparse.ArgumentParser(prog="lmstats", description="Run the local LM Stats Viewer.")
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"{parser.prog} {_version()}",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help=f"update the globally-installed {NPM_PACKAGE} package via npm",
    )
    parser.add_argument("--host", default=HOST, help=f"bind address (default: {HOST})")
    parser.add_argument("--port", default=PORT, type=int, help=f"bind port (default: {PORT})")
    parser.add_argument("--db", metavar="PATH", help="SQLite history database path")
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command-line arguments."""
    return build_parser().parse_args(argv)


def update_app(prog: str = "lmstats") -> None:
    """Update the globally-installed package via npm."""
    npm = shutil.which("npm")
    if npm is None:
        print(
            "npm was not found on PATH. Install Node.js/npm, then run:\n"
            f"  npm install -g {NPM_PACKAGE}",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"Updating {NPM_PACKAGE} via npm...")
    result = subprocess.run([npm, "install", "-g", NPM_PACKAGE])
    if result.returncode != 0:
        print("Update failed.", file=sys.stderr)
        sys.exit(result.returncode)
    print(f"Update complete. Run `{prog}` to start the new version.")
    sys.exit(0)


def main(argv=None) -> None:
    """Run the viewer server or a CLI command."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.update:
        update_app(parser.prog)
        return
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
    