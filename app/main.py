from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from app.scheduler import MLSScheduler
from app.utils.logging_config import setup_logging, get_logger
from app.config import settings

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Global scheduler instance
scheduler: MLSScheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown"""
    global scheduler

    # Startup
    logger.info("Starting House Search MLS Monitor")
    logger.info(f"Environment: {settings.timezone}")
    logger.info(f"Check times: {settings.check_times}")

    scheduler = MLSScheduler()
    scheduler.start()

    yield

    # Shutdown
    logger.info("Shutting down House Search MLS Monitor")
    if scheduler:
        scheduler.stop()


# Create FastAPI app
app = FastAPI(
    title="House Search MLS Monitor",
    description="Backend service to monitor MLS listings in San Diego coastal areas",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "House Search MLS Monitor",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if scheduler is running
        if not scheduler or not scheduler.is_running:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "reason": "Scheduler not running"}
            )

        # Check API quota health
        if not scheduler.api_router.check_quota_health():
            logger.warning("Low quota across all APIs")

        return {
            "status": "healthy",
            "scheduler_running": scheduler.is_running,
            "timestamp": scheduler.storage.load_listings()
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/status")
async def get_status():
    """Get detailed status information"""
    try:
        if not scheduler:
            raise HTTPException(status_code=503, detail="Scheduler not initialized")

        status = scheduler.get_status()
        return status

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/check-now")
async def trigger_manual_check():
    """Manually trigger an MLS check"""
    try:
        if not scheduler:
            raise HTTPException(status_code=503, detail="Scheduler not initialized")

        logger.info("Manual check triggered via API")

        # Run check in background (don't block API response)
        import threading
        thread = threading.Thread(target=scheduler.run_check)
        thread.start()

        return {
            "status": "success",
            "message": "MLS check started in background"
        }

    except Exception as e:
        logger.error(f"Error triggering manual check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/listings")
async def get_listings(limit: int = 50, offset: int = 0):
    """Get current listings"""
    try:
        if not scheduler:
            raise HTTPException(status_code=503, detail="Scheduler not initialized")

        listings_dict = scheduler.storage.load_listings()

        # Convert to list and sort by first_seen (newest first)
        listings_list = list(listings_dict.values())
        listings_list.sort(key=lambda x: x.first_seen, reverse=True)

        # Apply pagination
        paginated = listings_list[offset:offset + limit]

        return {
            "total": len(listings_list),
            "limit": limit,
            "offset": offset,
            "listings": [listing.model_dump() for listing in paginated]
        }

    except Exception as e:
        logger.error(f"Error getting listings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/quotas")
async def get_quota_status():
    """Get API quota status"""
    try:
        if not scheduler:
            raise HTTPException(status_code=503, detail="Scheduler not initialized")

        return scheduler.api_router.get_quota_status()

    except Exception as e:
        logger.error(f"Error getting quotas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Run the application"""
    logger.info("Starting House Search MLS Monitor server")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
