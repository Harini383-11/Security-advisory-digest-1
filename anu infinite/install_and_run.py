#!/usr/bin/env python3
"""Install dependencies and run the Security Advisory Digest app."""

import subprocess
import sys
import time

packages = [
    "streamlit",
    "pandas",
    "requests", 
    "chromadb",
    "pydantic",
    "loguru",
    "python-dotenv",
    "plotly",
    "feedparser",
    "ollama",
    "pytest",
]

print("🛡️ Installing Security Advisory Digest dependencies...")
print(f"Installing {len(packages)} packages...\n")

for i, package in enumerate(packages, 1):
    print(f"[{i}/{len(packages)}] Installing {package}...", end="", flush=True)
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package])
        print(" ✓")
    except Exception as e:
        print(f" ✗ ({e})")

print("\n✓ All dependencies installed!\n")
print("🚀 Starting Security Advisory Digest dashboard...\n")

time.sleep(2)
subprocess.call([sys.executable, "-m", "streamlit", "run", "app.py"])
