#!/usr/bin/env python3
"""Compatibility wrapper.

This repo previously used `difficulty/plot_difficulty.py` for plotting.

The maintained script is now `difficulty/summarize_difficulty.py`.
This wrapper keeps old commands working.
"""

from difficulty.summarize_difficulty import main


if __name__ == "__main__":
    raise SystemExit(main())
