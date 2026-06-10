#!/usr/bin/env python3
"""
Security Advisory Digest - Setup Verification and Demo Script
"""
import sys
import os
from pathlib import Path

def check_python_version():
    """Check Python version."""
    print("🔍 Checking Python version...")
    version_info = sys.version_info
    if version_info.major == 3 and version_info.minor >= 11:
        print(f"   ✓ Python {version_info.major}.{version_info.minor}.{version_info.micro} - OK")
        return True
    else:
        print(f"   ✗ Python {version_info.major}.{version_info.minor} - REQUIRES 3.11+")
        return False


def check_dependencies():
    """Check required dependencies."""
    print("\n🔍 Checking dependencies...")
    dependencies = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "feedparser",
        "requests",
        "pytest"
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"   ✓ {dep} installed")
        except ImportError:
            print(f"   ✗ {dep} NOT installed")
            missing.append(dep)
    
    if missing:
        print(f"\n   Install missing dependencies with:")
        print(f"   pip install -r requirements.txt")
        return False
    return True


def check_ollama():
    """Check Ollama installation."""
    print("\n🔍 Checking Ollama...")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"   ✓ Ollama is running")
            print(f"   ✓ Found {len(models)} models")
            
            # Check for llama3
            model_names = [m["name"] for m in models]
            if any("llama3" in m for m in model_names):
                print(f"   ✓ llama3 model available")
                return True
            else:
                print(f"   ✗ llama3 model not found")
                print(f"   Install with: ollama pull llama3")
                return False
    except Exception as e:
        print(f"   ✗ Ollama not accessible: {e}")
        print(f"   Start Ollama with: ollama serve")
        return False


def check_inventory_file():
    """Check inventory file."""
    print("\n🔍 Checking inventory file...")
    inventory_path = Path("data/inventory.csv")
    if inventory_path.exists():
        with open(inventory_path) as f:
            lines = f.readlines()
        print(f"   ✓ Inventory file found")
        print(f"   ✓ Contains {len(lines) - 1} items")
        return True
    else:
        print(f"   ✗ Inventory file not found at {inventory_path}")
        return False


def check_database():
    """Check database."""
    print("\n🔍 Checking database...")
    from db.sqlite import Database
    try:
        db = Database()
        advisories = db.get_all_advisories()
        inventory = db.get_all_inventory()
        matches = db.get_all_matches()
        
        print(f"   ✓ Database initialized")
        print(f"   ✓ Advisories: {len(advisories)}")
        print(f"   ✓ Inventory items: {len(inventory)}")
        print(f"   ✓ Matches: {len(matches)}")
        
        db.close()
        return True
    except Exception as e:
        print(f"   ✗ Database error: {e}")
        return False


def run_verification():
    """Run all verification checks."""
    print("=" * 70)
    print("Security Advisory Digest - Setup Verification")
    print("=" * 70)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Ollama Service", check_ollama),
        ("Inventory File", check_inventory_file),
        ("Database", check_database),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"   ✗ Check failed: {e}")
            results[name] = False
    
    print("\n" + "=" * 70)
    print("Verification Summary")
    print("=" * 70)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✓ All checks passed! System is ready.")
        print("\nStart the server with:")
        print("  uvicorn app:app --reload --host 0.0.0.0 --port 8000")
        print("\nAPI will be available at:")
        print("  http://localhost:8000")
        print("  http://localhost:8000/docs (API Documentation)")
    else:
        print("\n✗ Some checks failed. Please review the errors above.")
        print("\nFor help, see README.md - Troubleshooting section")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_verification())
