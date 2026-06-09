"""
Streamlit UI for Security Advisory Digest.

Multi-page application for managing security advisories.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
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
from config.settings import DATABASE_PATH, CHROMA_COLLECTION_NAME, OLLAMA_HOST, OLLAMA_MODEL

# Page configuration
st.set_page_config(
    page_title="Security Advisory Digest",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .critical {
        color: #d32f2f;
        font-weight: bold;
    }
    .high {
        color: #f57c00;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
@st.cache_resource
def get_database():
    return AdvisoryDatabase(DATABASE_PATH)

@st.cache_resource
def get_rag_engine():
    return RAGEngine(CHROMA_COLLECTION_NAME)

@st.cache_resource
def get_llm_service():
    return OllamaService(OLLAMA_HOST, OLLAMA_MODEL)

@st.cache_resource
def get_agent(db, rag, llm, matcher):
    return SecurityAgent(db, rag, llm, matcher)

# Get resources
db = get_database()
rag = get_rag_engine()
llm = get_llm_service()
matcher = InventoryMatcher(db)
agent = get_agent(db, rag, llm, matcher)
ingester = FeedIngester(db)
dedup_engine = DeduplicationEngine(db)
summary_gen = SummaryGenerator(db, llm)

# Sidebar navigation
st.sidebar.title("🛡️ Security Advisory Digest")
page = st.sidebar.radio(
    "Navigation",
    ["Home Dashboard", "Advisory Search", "Inventory Upload", "AI Assistant", "Risk Report"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Database Actions")

if st.sidebar.button("🔄 Ingest Advisories"):
    with st.spinner("Ingesting advisories..."):
        results = ingester.ingest_all()
        st.sidebar.success(f"Added {results['total']} new advisories")
        st.rerun()

if st.sidebar.button("🧹 Deduplicate CVEs"):
    with st.spinner("Deduplicating..."):
        stats = dedup_engine.deduplicate_all_cves()
        st.sidebar.success(f"Deleted {stats['advisories_deleted']} duplicates")
        st.rerun()

if st.sidebar.button("📊 Update Vector DB"):
    with st.spinner("Updating vector database..."):
        advisories = db.get_all_advisories(limit=10000)
        added = rag.add_advisories_batch(advisories)
        st.sidebar.success(f"Updated {added} vectors")

st.sidebar.markdown("---")
st.sidebar.subheader("System Status")

llm_health = llm.health_check()
if llm_health.get("status") == "healthy":
    st.sidebar.info(f"✅ Ollama: Ready")
else:
    st.sidebar.warning(f"⚠️ Ollama: {llm_health.get('status')}")

vector_stats = rag.get_collection_stats()
st.sidebar.info(f"📚 Vectors: {vector_stats.get('document_count', 0)}")

# PAGE 1: HOME DASHBOARD
if page == "Home Dashboard":
    st.title("🛡️ Security Advisory Digest - Dashboard")

    # Get database statistics
    stats = db.get_statistics()

    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Advisories", stats.get("total_advisories", 0))

    with col2:
        st.metric("Unique CVEs", stats.get("unique_cves", 0))

    with col3:
        critical_count = stats.get("by_severity", {}).get("Critical", 0)
        st.metric("Critical", critical_count, delta_color="off")

    with col4:
        high_count = stats.get("by_severity", {}).get("High", 0)
        st.metric("High Severity", high_count, delta_color="off")

    # Severity distribution chart
    st.subheader("Advisories by Severity")

    severity_data = stats.get("by_severity", {})
    if severity_data:
        fig = px.bar(
            x=list(severity_data.keys()),
            y=list(severity_data.values()),
            labels={"x": "Severity", "y": "Count"},
            color=list(severity_data.keys()),
            color_discrete_map={
                "Critical": "#d32f2f",
                "High": "#f57c00",
                "Medium": "#fbc02d",
                "Low": "#388e3c"
            }
        )
        st.plotly_chart(fig, use_container_width=True)

    # Latest critical advisories
    st.subheader("Latest Critical Advisories")

    critical_advs = db.get_critical_advisories(limit=10)

    if critical_advs:
        df = pd.DataFrame([
            {
                "CVE": a.get("cve_id"),
                "Title": a.get("title", "")[:60],
                "Vendor": a.get("vendor", ""),
                "Product": a.get("product", ""),
                "Severity": a.get("severity", ""),
                "Published": a.get("published_date", "")
            }
            for a in critical_advs
        ])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No critical advisories found")

    # Inventory overview
    st.subheader("Inventory Overview")

    inventory_risk = agent.get_inventory_risk_summary()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Inventory Items", inventory_risk.get("total_inventory_items", 0))

    with col2:
        st.metric("Items at Risk", inventory_risk.get("items_at_risk", 0))

    with col3:
        st.metric("Total Vulnerabilities", inventory_risk.get("total_vulnerabilities", 0))

    if inventory_risk.get("top_at_risk"):
        st.write("**Top At-Risk Products**")
        for item in inventory_risk["top_at_risk"]:
            st.write(f"- {item['product']} {item['version']}: {item['vulnerabilities']} vulnerabilities")

# PAGE 2: ADVISORY SEARCH
elif page == "Advisory Search":
    st.title("🔍 Advisory Search")

    search_type = st.radio("Search Type", ["Semantic Search", "CVE ID", "Product", "Severity"])

    if search_type == "Semantic Search":
        query = st.text_area("Enter your search query:")

        if st.button("Search"):
            results = rag.search_vectors(query, top_k=10)

            st.subheader(f"Found {len(results)} advisories")

            for result in results:
                metadata = result.get("metadata", {})
                with st.expander(f"{metadata.get('cve_id')} - {metadata.get('severity', 'Unknown')}"):
                    st.write(result.get("document", ""))
                    st.caption(f"Distance: {result.get('distance', 'N/A')}")

    elif search_type == "CVE ID":
        cve_id = st.text_input("Enter CVE ID (e.g., CVE-2024-1234):")

        if st.button("Search"):
            advisory = db.get_advisory_by_cve(cve_id)

            if advisory:
                st.subheader(advisory.get("cve_id"))
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Severity**: {advisory.get('severity')}")
                    st.write(f"**Vendor**: {advisory.get('vendor')}")
                    st.write(f"**Product**: {advisory.get('product')}")

                with col2:
                    st.write(f"**Published**: {advisory.get('published_date')}")
                    st.write(f"**Source**: {advisory.get('source_feed')}")
                    st.write(f"**URL**: {advisory.get('url')}")

                st.write(f"**Description**: {advisory.get('description')}")
            else:
                st.warning(f"CVE {cve_id} not found")

    elif search_type == "Product":
        product = st.text_input("Enter product name:")

        if st.button("Search"):
            advisories = db.get_advisories_by_product(product)

            st.subheader(f"Found {len(advisories)} advisories for {product}")

            if advisories:
                df = pd.DataFrame([
                    {
                        "CVE": a.get("cve_id"),
                        "Severity": a.get("severity"),
                        "Published": a.get("published_date")
                    }
                    for a in advisories
                ])
                st.dataframe(df, use_container_width=True)

    elif search_type == "Severity":
        severity = st.selectbox("Select Severity", ["Critical", "High", "Medium", "Low"])

        if st.button("Search"):
            advisories = db.get_advisories_by_severity(severity)

            st.subheader(f"Found {len(advisories)} {severity} severity advisories")

            if advisories:
                df = pd.DataFrame([
                    {
                        "CVE": a.get("cve_id"),
                        "Product": a.get("product"),
                        "Published": a.get("published_date")
                    }
                    for a in advisories
                ])
                st.dataframe(df, use_container_width=True)

# PAGE 3: INVENTORY UPLOAD
elif page == "Inventory Upload":
    st.title("📦 Inventory Management")

    # Upload CSV
    st.subheader("Upload Inventory CSV")

    uploaded_file = st.file_uploader("Choose CSV file", type="csv")

    if uploaded_file:
        temp_path = f"temp_inventory_{datetime.now().timestamp()}.csv"

        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        if st.button("Import Inventory"):
            with st.spinner("Importing inventory..."):
                count, errors = matcher.load_inventory_from_csv(temp_path)
                st.success(f"Imported {count} items")

                if errors:
                    st.warning(f"Encountered {len(errors)} errors:")
                    for error in errors[:10]:
                        st.write(f"- {error}")

                # Clean up
                Path(temp_path).unlink()

    # Current inventory
    st.subheader("Current Inventory")

    inventory = db.get_inventory()

    if inventory:
        df = pd.DataFrame([
            {
                "Product": item["product"],
                "Version": item["version"],
                "Added": item["created_at"]
            }
            for item in inventory
        ])
        st.dataframe(df, use_container_width=True)

        # Match inventory
        if st.button("🔗 Match to Advisories"):
            with st.spinner("Matching inventory to advisories..."):
                results = matcher.match_inventory_to_advisories()
                st.success(f"Found {results['total_matches']} vulnerability matches")
                st.write(f"- Items at risk: {results['items_with_matches']}")
                st.write(f"- Critical: {results['critical_vulnerabilities']}")
                st.write(f"- High: {results['high_vulnerabilities']}")

    else:
        st.info("No inventory items. Upload a CSV file to get started.")

    # Download sample CSV
    st.subheader("Sample Inventory CSV")

    sample_csv = """Product,Version
Windows Server,2019
Apache Tomcat,9
OpenSSL,1.1
Ubuntu,20.04
nginx,1.18"""

    st.download_button(
        label="Download Sample CSV",
        data=sample_csv,
        file_name="sample_inventory.csv",
        mime="text/csv"
    )

# PAGE 4: AI ASSISTANT
elif page == "AI Assistant":
    st.title("🤖 AI Security Assistant")

    query = st.text_area("Ask a security question about advisories:")

    col1, col2 = st.columns(2)

    with col1:
        include_inventory = st.checkbox("Include inventory context", value=True)

    with col2:
        if st.button("Ask Assistant"):
            with st.spinner("Processing query..."):
                response = agent.process_query(query, inventory_context=include_inventory)

                st.subheader("Answer")
                st.write(response.get("answer", "No answer generated"))

                with st.expander("Details"):
                    st.write(f"**Confidence**: {response.get('confidence')}")
                    st.write(f"**Advisories Retrieved**: {response.get('retrieved_advisories')}")
                    st.write(f"**Sources**: {', '.join(response.get('sources', []))}")

                    st.write("**Reasoning Steps**:")
                    for step in response.get("reasoning_steps", []):
                        st.write(f"- {step}")

    # Quick commands
    st.subheader("Quick Commands")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔴 Show Critical Advisories"):
            critical = agent.get_critical_advisories(limit=10)
            st.write(f"Found {len(critical)} critical advisories:")
            for adv in critical[:5]:
                st.write(f"- **{adv['cve_id']}**: {adv.get('title', 'N/A')}")

    with col2:
        if st.button("📊 Inventory Risk Summary"):
            risk = agent.get_inventory_risk_summary()
            st.write(f"**Items at Risk**: {risk.get('items_at_risk')} of {risk.get('total_inventory_items')}")
            st.write(f"**Total Vulnerabilities**: {risk.get('total_vulnerabilities')}")
            st.write(f"**Critical**: {risk.get('critical_vulnerabilities')}")

    with col3:
        if st.button("📄 Generate Daily Digest"):
            digest = summary_gen.generate_daily_digest()
            if digest:
                st.write(digest)

# PAGE 5: RISK REPORT
elif page == "Risk Report":
    st.title("📋 Risk Report")

    report_type = st.radio("Report Type", ["Inventory Risk", "Executive Summary"])

    if report_type == "Inventory Risk":
        report = matcher.generate_risk_report()

        st.subheader("Risk Summary")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Items at Risk", report["summary"]["at_risk"])

        with col2:
            st.metric("Critical", report["summary"]["critical_count"])

        with col3:
            st.metric("Total CVEs", report["summary"]["total_count"])

        st.subheader("Affected Inventory Items")

        if report.get("inventory_items"):
            for item in report["inventory_items"]:
                with st.expander(f"{item['product']} {item['version']} - {item['vulnerabilities']} CVEs"):
                    st.write(f"**By Severity**: {item['by_severity']}")

                    if item.get("critical_vulnerabilities"):
                        st.warning("**Critical Vulnerabilities**:")
                        for vuln in item["critical_vulnerabilities"]:
                            st.write(f"- {vuln['cve_id']}: {vuln['title']}")

    elif report_type == "Executive Summary":
        summary = summary_gen.generate_executive_summary()

        st.write(f"**Generated**: {summary.get('generated_at')}")

        st.subheader("Database Statistics")

        stats = summary.get("database_statistics", {})
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Advisories", stats.get("total_advisories"))

        with col2:
            st.metric("Unique CVEs", stats.get("unique_cves"))

        with col3:
            st.metric("Vendors", stats.get("unique_vendors"))

        st.subheader("Top Vulnerabilities")

        for vuln in summary.get("top_vulnerabilities", [])[:10]:
            st.write(f"- **{vuln['cve_id']}** ({vuln['severity']}): {vuln['product']}")

        st.subheader("Recommendations")

        recs = summary.get("recommendations", "")
        st.write(recs)

# Footer
st.markdown("---")
st.markdown(
    """
    **Security Advisory Digest** - A comprehensive vulnerability management system.
    Powered by Ollama LLM, ChromaDB, and SQLite.
    """
)
