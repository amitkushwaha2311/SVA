import asyncio
import logging
import signal
import sys
from app.orchestration.worker import LocalAnalysisWorker
from app.persistence.database import async_session_maker

# Setup basic logging for the worker process
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("worker_main")


async def main():
    logger.info("Starting Analysis Worker...")
    worker = LocalAnalysisWorker(session_factory=async_session_maker, poll_interval_seconds=2.0)

    # Handle graceful shutdown on SIGINT/SIGTERM
    shutdown_event = asyncio.Event()

    def handle_shutdown(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        shutdown_event.set()

    # Register signal handlers
    try:
        # Windows supports SIGINT and SIGTERM, but signal handling is slightly different
        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)
    except Exception as e:
        logger.warning(f"Failed to register signal handlers: {e}")

    try:
        await worker.start()
        logger.info("Analysis Worker started. Waiting for jobs...")
        await shutdown_event.wait()
    except asyncio.CancelledError:
        logger.info("Worker main task cancelled.")
    except Exception as e:
        logger.error(f"Worker main loop crashed: {e}")
    finally:
        logger.info("Stopping Analysis Worker...")
        await worker.stop()
        logger.info("Analysis Worker stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user.")
