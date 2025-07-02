#!/usr/bin/env python3
"""
LinguistWrapper demonstration script.

Usage:
    python test.py project.zip           # Use local gem
    python test.py --docker project.zip  # Use Docker image
"""

import argparse
import json
import sys
from pathlib import Path

from linguist_wrapper import LinguistWrapper


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Analyze programming languages in ZIP archive")
    parser.add_argument(
        "--docker",
        action="store_true",
        help="Use Docker image instead of local linguist gem"
    )
    parser.add_argument(
        "archive",
        help="Path to ZIP archive containing project"
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    zip_path = Path(args.archive).expanduser().resolve()

    wrapper = LinguistWrapper(use_docker=args.docker)
    stats = wrapper.analyze_zip(zip_path)

    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        sys.stderr.write(f"Error: {error}\n")
        sys.exit(1)