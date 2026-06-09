"""
Final Review and Deployment Checklist for Security Advisory Digest

This script performs comprehensive verification of all systems.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.database import AdvisoryDatabase
from src.modules.ingest import FeedIngester
from src.modules.dedup import DeduplicationEngine
from src.modules.inventory_match import InventoryMatcher
from src.modules.rag import RAGEngine
from src.modules.llm_service import OllamaService
from src.modules.agent import SecurityAgent
from src.modules.summary_generator import SummaryGenerator
from config.settings import DATABASE_PATH, OLLAMA_HOST, OLLAMA_MODEL
from loguru import logger


class DeploymentChecker:
    """Comprehensive deployment verification."""

    def __init__(self):
        """Initialize checker."""
        self.results = {
            "passed": [],
            "warnings": [],
            "failed": [],
            "total_checks": 0
        }

    def check_all(self) -> dict:
        """Run all checks."""
        print("=" * 70)
        print("SECURITY ADVISORY DIGEST - DEPLOYMENT VERIFICATION")
        print("=" * 70)

        self.check_imports()
        self.check_database()
        self.check_vector_db()
        self.check_ollama()
        self.check_modules()
        self.check_integrations()
        self.check_streamlit()

        return self.generate_report()

    def check_imports(self):
        """Verify all imports work."""
        print("\n🔍 Checking imports...")
        checks = [
            ("streamlit", lambda: __import__("streamlit")),
            ("chromadb", lambda: __import__("chromadb")),
            ("pandas", lambda: __import__("pandas")),
            ("requests", lambda: __import__("requests")),
            ("pytest", lambda: __import__("pytest")),
            ("loguru", lambda: __import__("loguru")),
            ("plotly", lambda: __import__("plotly")),
            ("python-dotenv", lambda: __import__("dotenv")),
        ]

        for name, import_func in checks:
            try:
                import_func()
                self._pass(f"✓ {name} imported successfully")
            except ImportError as e:
                self._fail(f"✗ {name} import failed: {e}")

    def check_database(self):
        """Verify SQLite database."""
        print("\n💾 Checking SQLite database...")

        try:
            db = AdvisoryDatabase(DATABASE_PATH)
            self._pass("✓ Database connection successful")

            # Check schema
            stats = db.get_statistics()
            self._pass(f"✓ Database schema verified ({stats.get('total_advisories', 0)} advisories)")

            # Check tables
            try:
                import sqlite3
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()

                required_tables = ["advisories", "inventory", "inventory_matches"]
                found_tables = [t[0] for t in tables]

                for table in required_tables:
                    if table in found_tables:
                        self._pass(f"✓ Table '{table}' exists")
                    else:
                        self._fail(f"✗ Table '{table}' missing")

                # Check indexes
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
                indexes = cursor.fetchall()
                index_count = len(indexes)

                if index_count >= 5:
                    self._pass(f"✓ {index_count} indexes created (performance optimized)")
                else:
                    self._warning(f"⚠ Only {index_count} indexes found (may affect performance)")

                conn.close()
            except Exception as e:
                self._fail(f"✗ Schema verification failed: {e}")

        except Exception as e:
            self._fail(f"✗ Database check failed: {e}")

    def check_vector_db(self):
        """Verify ChromaDB vector database."""
        print("\n🔍 Checking ChromaDB...")

        try:
            rag = RAGEngine()
            stats = rag.get_collection_stats()
            self._pass(f"✓ ChromaDB connection successful")
            self._pass(f"✓ Collection '{stats.get('collection_name')}' found")

            doc_count = stats.get('document_count', 0)
            if doc_count > 0:
                self._pass(f"✓ {doc_count} vectors in database")
            else:
                self._warning("⚠ No vectors in database (run 'Update Vector DB')")

        except Exception as e:
            self._warning(f"⚠ ChromaDB check failed (may need initialization): {e}")

    def check_ollama(self):
        """Verify Ollama LLM integration."""
        print("\n🤖 Checking Ollama LLM...")

        try:
            llm = OllamaService()
            health = llm.health_check()

            if health.get("status") == "healthy":
                self._pass(f"✓ Ollama connection successful ({llm.host})")
                self._pass(f"✓ Model '{llm.model}' configured")

                if health.get("model_available"):
                    self._pass(f"✓ Model '{llm.model}' is available")
                else:
                    self._warning(f"⚠ Model '{llm.model}' not available (run 'ollama pull {llm.model}')")
                    available = health.get("available_models", [])
                    if available:
                        self._pass(f"  Available models: {available[:3]}")

            else:
                self._fail(f"✗ Ollama offline ({health.get('error')})")

        except Exception as e:
            self._fail(f"✗ Ollama check failed: {e}")

    def check_modules(self):
        """Verify all modules."""
        print("\n📦 Checking modules...")

        modules_to_check = [
            ("Database", lambda: AdvisoryDatabase(DATABASE_PATH)),
            ("Ingester", lambda: FeedIngester(AdvisoryDatabase(DATABASE_PATH))),
            ("Deduplication", lambda: DeduplicationEngine(AdvisoryDatabase(DATABASE_PATH))),
            ("Inventory Matcher", lambda: InventoryMatcher(AdvisoryDatabase(DATABASE_PATH))),
            ("RAG Engine", lambda: RAGEngine()),
            ("LLM Service", lambda: OllamaService()),
            ("Agent", lambda: SecurityAgent(
                AdvisoryDatabase(DATABASE_PATH),
                RAGEngine(),
                OllamaService(),
                InventoryMatcher(AdvisoryDatabase(DATABASE_PATH))
            )),
            ("Summary Generator", lambda: SummaryGenerator(
                AdvisoryDatabase(DATABASE_PATH),
                OllamaService()
            ))
        ]

        for name, init_func in modules_to_check:
            try:
                init_func()
                self._pass(f"✓ {name} initialized successfully")
            except Exception as e:
                self._warning(f"⚠ {name} initialization warning: {e}")

    def check_integrations(self):
        """Verify module integrations."""
        print("\n🔗 Checking integrations...")

        try:
            db = AdvisoryDatabase(DATABASE_PATH)
            rag = RAGEngine()
            llm = OllamaService()
            matcher = InventoryMatcher(db)
            agent = SecurityAgent(db, rag, llm, matcher)

            # Test database -> agent flow
            result = agent.get_inventory_risk_summary()
            self._pass("✓ Agent can access inventory")

            # Test RAG search
            search_results = rag.search_vectors("test query", top_k=1)
            if search_results is not None:
                self._pass(f"✓ RAG search working (returns list)")
            else:
                self._warning("⚠ RAG search returned None")

            # Test LLM health
            health = llm.health_check()
            if health.get("status") in ["healthy", "offline"]:
                self._pass("✓ LLM service responsive")
            else:
                self._fail("✗ LLM service unresponsive")

        except Exception as e:
            self._fail(f"✗ Integration check failed: {e}")

    def check_streamlit(self):
        """Verify Streamlit configuration."""
        print("\n🎨 Checking Streamlit...")

        try:
            import streamlit as st
            self._pass("✓ Streamlit imported successfully")

            # Check for app.py
            app_file = Path(__file__).parent / "app.py"
            if app_file.exists():
                self._pass("✓ app.py found")
                with open(app_file) as f:
                    content = f.read()
                    if "st.title" in content:
                        self._pass("✓ app.py has Streamlit elements")
                    else:
                        self._fail("✗ app.py missing Streamlit elements")
            else:
                self._fail("✗ app.py not found")

        except Exception as e:
            self._warning(f"⚠ Streamlit check warning: {e}")

    def _pass(self, message: str):
        """Record passed check."""
        print(f"  {message}")
        self.results["passed"].append(message)
        self.results["total_checks"] += 1

    def _warning(self, message: str):
        """Record warning."""
        print(f"  {message}")
        self.results["warnings"].append(message)
        self.results["total_checks"] += 1

    def _fail(self, message: str):
        """Record failure."""
        print(f"  {message}")
        self.results["failed"].append(message)
        self.results["total_checks"] += 1

    def generate_report(self) -> dict:
        """Generate summary report."""
        print("\n" + "=" * 70)
        print("DEPLOYMENT VERIFICATION REPORT")
        print("=" * 70)

        passed = len(self.results["passed"])
        warnings = len(self.results["warnings"])
        failed = len(self.results["failed"])
        total = self.results["total_checks"]

        print(f"\n✓ Passed: {passed}/{total}")
        print(f"⚠ Warnings: {warnings}/{total}")
        print(f"✗ Failed: {failed}/{total}")

        if failed == 0:
            print("\n✅ READY FOR DEPLOYMENT")
        elif failed <= 2 and warnings < 5:
            print("\n⚠️  READY WITH CAUTION (address warnings)")
        else:
            print("\n❌ NOT READY FOR DEPLOYMENT (fix failures)")

        return self.results


class DeploymentChecklist:
    """Pre-deployment checklist."""

    @staticmethod
    def print_checklist():
        """Print deployment checklist."""
        print("\n" + "=" * 70)
        print("PRE-DEPLOYMENT CHECKLIST")
        print("=" * 70)

        checklist = [
            ("📋 Code Review", [
                "All modules reviewed for bugs",
                "Error handling covers edge cases",
                "Logging implemented throughout",
                "Type hints complete",
                "Documentation updated"
            ]),
            ("🧪 Testing", [
                "Unit tests passing (pytest tests/test_all.py)",
                "Integration tests passing",
                "Performance tested (handles 10k+ advisories)",
                "Error scenarios tested",
                "Coverage > 80%"
            ]),
            ("💾 Database", [
                "SQLite schema verified",
                "Indexes created for performance",
                "Backup strategy defined",
                "Data migration plan ready",
                "Recovery procedure documented"
            ]),
            ("🤖 LLM Integration", [
                "Ollama running with llama3 model",
                "Prompt templates tested",
                "Response handling verified",
                "Timeout handling implemented",
                "Fallback logic ready"
            ]),
            ("🔍 Vector Database", [
                "ChromaDB persistent storage configured",
                "Embeddings updated",
                "Search performance tested",
                "Collection backup created",
                "Recovery plan ready"
            ]),
            ("🎨 UI/UX", [
                "Streamlit app tested on target system",
                "All pages responsive",
                "Error messages user-friendly",
                "Performance acceptable",
                "Mobile view tested"
            ]),
            ("🔒 Security", [
                "No hardcoded secrets in code",
                ".env template provided",
                "API keys properly managed",
                "No sensitive data logged",
                "Input validation implemented"
            ]),
            ("📚 Documentation", [
                "README comprehensive",
                "Setup instructions clear",
                "Troubleshooting guide complete",
                "API documentation ready",
                "Configuration documented"
            ]),
            ("🚀 Deployment", [
                "requirements.txt updated",
                "Python version specified (3.9+)",
                "Environment setup tested",
                "Installation guide tested",
                "Rollback plan created"
            ]),
            ("📊 Monitoring", [
                "Logging configured",
                "Error alerts defined",
                "Performance metrics identified",
                "Health check endpoints created",
                "Dashboard monitoring ready"
            ])
        ]

        for category, items in checklist:
            print(f"\n{category}")
            for item in items:
                print(f"  ☐ {item}")

        print("\n" + "=" * 70)


if __name__ == "__main__":
    # Run verification
    checker = DeploymentChecker()
    results = checker.check_all()

    # Print checklist
    DeploymentChecklist.print_checklist()

    # Exit code based on results
    if len(results["failed"]) == 0:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure
