#!/bin/bash
# For Docker: watchdog is PID 1, runs main.py as child
exec python core/watchdog.py
