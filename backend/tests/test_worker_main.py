import pytest
import asyncio
import signal
from unittest.mock import patch, MagicMock

from app.orchestration.worker_main import main


@pytest.mark.asyncio
async def test_worker_main_graceful_shutdown():
    # We will mock the LocalAnalysisWorker
    with patch("app.orchestration.worker_main.LocalAnalysisWorker") as MockWorker:
        mock_worker_instance = MockWorker.return_value
        from unittest.mock import AsyncMock
        mock_worker_instance.start = AsyncMock()
        mock_worker_instance.stop = AsyncMock()

        
        # We will mock the asyncio.Event to trigger a shutdown directly
        with patch("app.orchestration.worker_main.asyncio.Event") as MockEvent:
            mock_event_instance = MockEvent.return_value
            from unittest.mock import AsyncMock
            mock_event_instance.wait = AsyncMock()
            
            # Create a task that runs the main function
            await main()
            
            # Assert that worker.start() was called
            mock_worker_instance.start.assert_called_once()
            
            # Assert worker.stop() was called
            mock_worker_instance.stop.assert_called_once()
