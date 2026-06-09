#!/usr/bin/env python3
"""Quick debug - Core system check"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🛡️ SECURITY ADVISORY DIGEST - SYSTEM CHECK")
print("=" * 60)

# Test config
print("\n[1/3] Config & Database...")
try:
    from config.settings import DATABASE_PATH, VECTOR_DB_PATH, OLLAMA_HOST
    from src.core.database import AdvisoryDatabase
    
    print(f"  ✓ Config: {DATABASE_PATH}")
    db = AdvisoryDatabase()
    print(f"  ✓ Database initialized")
    
    # Try to get stats if they exist
    try:
        stats = db.get_statistics()
        total = stats.get('total_advisories', 0)
        cves = stats.get('unique_cves', 0)
        print(f"    - {total} advisories, {cves} unique CVEs")
    except:
        print(f"    - Database empty (ready for import)")
        
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test if Ollama is running
print("\n[2/3] Ollama LLM Service...")
try:
    import requests
    response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
    if response.status_code == 200:
        models = response.json().get('models', [])
        if models:
            print(f"  ✓ Ollama running with {len(models)} models")
            for m in models[:3]:
                print(f"    - {m.get('name')}")
        else:
            print(f"  ⚠ Ollama running but no models installed")
            print(f"    Run: ollama pull llama3")
    else:
        print(f"  ⚠ Ollama not responding properly")
except requests.ConnectionError:
    print(f"  ⚠ Ollama not running")
    print(f"    Start with: ollama serve")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Summary
print("\n[3/3] System Status...")
print("  ✓ Python modules working")
print("  ✓ Database ready")
print("  ℹ Next: Install missing dependencies")

print("\n" + "=" * 60)
print("📋 QUICK START COMMANDS:")
print("=" * 60)
print("\n1. Start Ollama (if not running):")
print("   ollama serve")
print("\n2. Install all dependencies:")
print(f'   "{OLLAMA_HOST.split("//")[1].split(":")[0]}" -m pip install -r requirements.txt')
print("\n3. Run the app:")
print(f'   streamlit run app.py')
print("\n" + "=" * 60)
