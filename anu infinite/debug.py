#!/usr/bin/env python3
"""Quick debug script - test core functionality without Streamlit"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🛡️ SECURITY ADVISORY DIGEST - QUICK DEBUG")
print("=" * 60)

# Test 1: Import core modules
print("\n[1/5] Testing module imports...")
try:
    from config.settings import DATABASE_PATH, VECTOR_DB_PATH, OLLAMA_HOST
    print("  ✓ Config loaded")
    print(f"    - DATABASE_PATH: {DATABASE_PATH}")
    print(f"    - VECTOR_DB_PATH: {VECTOR_DB_PATH}")
    print(f"    - OLLAMA_HOST: {OLLAMA_HOST}")
except Exception as e:
    print(f"  ✗ Config import failed: {e}")
    sys.exit(1)

try:
    from src.core.database import AdvisoryDatabase
    print("  ✓ Database module imported")
except Exception as e:
    print(f"  ✗ Database import failed: {e}")
    sys.exit(1)

try:
    from src.modules.ingest import Ingester
    print("  ✓ Ingestion module imported")
except Exception as e:
    print(f"  ✗ Ingestion import failed: {e}")
    sys.exit(1)

try:
    from src.modules.dedup import Deduplicator
    print("  ✓ Deduplication module imported")
except Exception as e:
    print(f"  ✗ Dedup import failed: {e}")
    sys.exit(1)

try:
    from src.modules.rag import RAGEngine
    print("  ✓ RAG module imported")
except Exception as e:
    print(f"  ✗ RAG import failed: {e}")
    sys.exit(1)

try:
    from src.modules.llm_service import LLMService
    print("  ✓ LLM module imported")
except Exception as e:
    print(f"  ✗ LLM import failed: {e}")
    sys.exit(1)

try:
    from src.modules.agent import Agent
    print("  ✓ Agent module imported")
except Exception as e:
    print(f"  ✗ Agent import failed: {e}")
    sys.exit(1)

# Test 2: Initialize database
print("\n[2/5] Testing database initialization...")
try:
    db = AdvisoryDatabase()
    stats = db.get_statistics()
    print(f"  ✓ Database initialized")
    print(f"    - Total advisories: {stats.get('total_advisories', 0)}")
    print(f"    - Unique CVEs: {stats.get('unique_cves', 0)}")
except Exception as e:
    print(f"  ✗ Database init failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Check Ollama
print("\n[3/5] Testing Ollama LLM service...")
try:
    llm = LLMService()
    health = llm.health_check()
    if health.get('status') == 'healthy':
        print(f"  ✓ Ollama is running")
        print(f"    - Model: {health.get('model')}")
        print(f"    - Version: {health.get('version')}")
    else:
        print(f"  ⚠ Ollama status: {health.get('status')}")
        print(f"    - Note: Ollama not running yet (start with: ollama serve)")
except Exception as e:
    print(f"  ⚠ Ollama check failed: {e}")
    print(f"    - Install Ollama: https://ollama.ai")
    print(f"    - Then run: ollama pull llama3")

# Test 4: Check ChromaDB
print("\n[4/5] Testing ChromaDB vector database...")
try:
    rag = RAGEngine()
    stats = rag.get_collection_stats()
    print(f"  ✓ ChromaDB initialized")
    print(f"    - Documents in collection: {stats.get('count', 0)}")
except Exception as e:
    print(f"  ✗ ChromaDB init failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Test agent initialization
print("\n[5/5] Testing AI Agent...")
try:
    agent = Agent()
    print(f"  ✓ Agent initialized")
    print(f"    - Ready for queries")
except Exception as e:
    print(f"  ✗ Agent init failed: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 60)
print("✓ SYSTEM CHECK COMPLETE")
print("=" * 60)
print("\n📋 NEXT STEPS:")
print("  1. Start Ollama: ollama serve")
print("  2. Run Streamlit: streamlit run app.py")
print("  3. Access dashboard at: http://localhost:8501")
print("\n" + "=" * 60)
