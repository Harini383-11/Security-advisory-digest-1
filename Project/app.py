"""
FastAPI application for Security Advisory Digest.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import feedparser
import json as _json
from pathlib import Path

from config import API_TITLE, API_VERSION
from models import HealthResponse, ScanResponse, Advisory, Match
from agent import SecurityAdvisoryAgent
from db.sqlite import Database
from llm.ollama import OllamaClient
from ingestion.rss import RSSIngester
from ingestion.json_feed import JSONFeedIngester
from inventory.inventory_match import InventoryMatchService
from models import AdvisoryDB, InventoryItemDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description="Security Advisory Digest - Automated security advisory ingestion and matching"
)

# Initialize components
database = Database()
ollama_client = OllamaClient()
agent = SecurityAdvisoryAgent()

logger.info(f"Starting {API_TITLE} v{API_VERSION}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down application")
    agent.close()
    database.close()


@app.get("/", tags=["info"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "description": "Security advisory ingestion and inventory matching system",
        "endpoints": {
            "GET /": "This endpoint",
            "GET /health": "Health check",
            "GET /advisories": "List all advisories",
            "GET /matches": "List all matches",
            "GET /report": "Get latest report",
            "POST /scan": "Run security advisory scan",
            "POST /scan/upload?file_type={rss,json,csv}": "Upload raw RSS/JSON/CSV payload and run a scan"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint."""
    try:
        # Check database
        db_available = True
        try:
            advisories = database.get_all_advisories()
            db_available = True
        except Exception:
            db_available = False
        
        # Check Ollama
        ollama_available = ollama_client.is_available()
        
        return HealthResponse(
            status="healthy" if (db_available) else "degraded",
            timestamp=datetime.now().isoformat(),
            ollama_available=ollama_available,
            database_available=db_available
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.get("/advisories", tags=["advisories"])
async def get_advisories(limit: int = 50):
    """Get recent advisories."""
    try:
        advisories = database.get_recent_advisories(limit)
        return {
            "total": len(advisories),
            "advisories": [
                {
                    "id": a.id,
                    "advisory_id": a.advisory_id,
                    "title": a.title,
                    "severity": a.severity,
                    "vendor": a.vendor,
                    "product": a.product,
                    "published_date": a.published_date.isoformat(),
                    "source_feed": a.source_feed,
                    "url": a.url
                }
                for a in advisories
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching advisories: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch advisories")


@app.get("/matches", tags=["matches"])
async def get_matches():
    """Get all advisory-inventory matches."""
    try:
        matches = database.get_all_matches()
        
        # Enrich match data with advisory and inventory information
        enriched_matches = []
        
        for match in matches:
            advisory = database.get_advisory_by_id(match.advisory_id)
            inventory = database.get_inventory_by_id(match.inventory_item_id)
            
            if advisory and inventory:
                enriched_matches.append({
                    "match_id": match.id,
                    "advisory": {
                        "id": advisory.id,
                        "advisory_id": advisory.advisory_id,
                        "title": advisory.title,
                        "severity": advisory.severity,
                        "product": advisory.product
                    },
                    "inventory_item": {
                        "asset_id": inventory.asset_id,
                        "software_name": inventory.software_name,
                        "version": inventory.version
                    },
                    "risk_level": match.risk_level,
                    "created_at": match.created_at.isoformat() if match.created_at else None
                })
        
        return {
            "total_matches": len(enriched_matches),
            "matches": enriched_matches
        }
    except Exception as e:
        logger.error(f"Error fetching matches: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch matches")


@app.get("/report", tags=["reports"])
async def get_report():
    """Get latest scan report."""
    try:
        import json
        from pathlib import Path
        
        report_path = Path("data/report.json")
        
        if not report_path.exists():
            return {
                "status": "no_report",
                "message": "No report available. Run /scan endpoint to generate one."
            }
        
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        return {
            "status": "success",
            "report": report_data
        }
    except Exception as e:
        logger.error(f"Error fetching report: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch report")


@app.post("/scan", response_model=ScanResponse, tags=["scan"])
async def run_scan(force_refresh: bool = False):
    """
    Execute complete security advisory scan.
    
    This endpoint:
    1. Reads RSS feeds
    2. Stores advisories
    3. Loads inventory
    4. Matches advisories
    5. Generates AI summaries
    6. Generates report
    
    Args:
        force_refresh: Force refresh of advisories
        
    Returns:
        ScanResponse with report data
    """
    try:
        logger.info("Received scan request")
        logger.info(f"Force refresh: {force_refresh}")
        
        # Run the agent
        result = agent.run(force_refresh=force_refresh)
        
        if result and result.get("status") == "success":
            logger.info("Scan completed successfully")
            
            return ScanResponse(
                status="success",
                message="Scan completed successfully",
                report=result.get("report"),
                error=None
            )
        else:
            error_msg = result.get("message", "Unknown error") if result else "Unknown error"
            logger.error(f"Scan failed: {error_msg}")
            
            return ScanResponse(
                status="error",
                message="Scan failed",
                report=None,
                error=error_msg
            )
            
    except Exception as e:
        logger.error(f"Exception during scan: {e}", exc_info=True)
        
        return ScanResponse(
            status="error",
            message="Scan failed with exception",
            report=None,
            error=str(e)
        )


@app.post("/scan/upload", response_model=ScanResponse, tags=["scan"])
async def upload_and_scan(file: UploadFile = File(...), file_type: Optional[str] = Form(None)):
    """Upload a local RSS/JSON/inventory file and run a scan using that input."""
    try:
        content = await file.read()
        filename = file.filename or ""
        ft = (file_type or Path(filename).suffix.lstrip('.')).lower()

        if not ft:
            raise HTTPException(status_code=400, detail="The form field 'file_type' or file extension is required")

        # Inventory CSV
        if ft in ("csv", "inventory"):
            path = Path("data") / "inventory.csv"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

            inv_service = InventoryMatchService()
            inventory = inv_service.load_inventory_from_csv(path)

            result = agent.run(inventory_override=inventory)
            if result and result.get("status") == "success":
                return ScanResponse(status="success", message="Inventory uploaded and scan executed", report=result.get("report"), error=None)
            return ScanResponse(status="error", message="Scan failed", report=None, error=str(result))

        # RSS/XML
        if ft in ("xml", "rss"):
            parsed = feedparser.parse(content)
            rss = RSSIngester()
            advisories = []
            for entry in parsed.entries:
                a = rss._parse_entry(entry, "local_upload")
                if a:
                    advisories.append(a)

            result = agent.run(advisories_override=advisories)
            if result and result.get("status") == "success":
                return ScanResponse(status="success", message="RSS uploaded and scan executed", report=result.get("report"), error=None)
            return ScanResponse(status="error", message="Scan failed", report=None, error=str(result))

        # JSON
        if ft in ("json",):
            data = _json.loads(content.decode("utf-8"))
            jf = JSONFeedIngester()
            advisories = jf.ingest_feed("local_upload", data)

            result = agent.run(advisories_override=advisories)
            if result and result.get("status") == "success":
                return ScanResponse(status="success", message="JSON uploaded and scan executed", report=result.get("report"), error=None)
            return ScanResponse(status="error", message="Scan failed", report=None, error=str(result))

        return ScanResponse(status="error", message="Unsupported file type", report=None, error=f"Unsupported file type: {ft}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload scan failed: {e}")
        return ScanResponse(status="error", message="Upload scan failed", report=None, error=str(e))


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    from config import API_HOST, API_PORT
    
    logger.info(f"Starting server on {API_HOST}:{API_PORT}")
    
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info"
    )
