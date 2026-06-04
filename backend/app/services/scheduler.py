import asyncio
import logging

from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.services.classifier import get_classifier
from app.services.email_reader import get_email_reader
from app.services.processor import EmailProcessor

logger = logging.getLogger(__name__)


class PollingScheduler:
    def __init__(self, settings: Settings, session_factory: sessionmaker) -> None:
        self._settings = settings
        self._session_factory = session_factory
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await asyncio.to_thread(self._process_once)
            except Exception:
                logger.exception("Scheduled email polling failed")

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=max(1, self._settings.poll_interval_seconds),
                )
            except TimeoutError:
                continue

    def _process_once(self) -> None:
        db = self._session_factory()
        try:
            processor = EmailProcessor(
                db=db,
                reader=get_email_reader(self._settings),
                classifier=get_classifier(self._settings),
            )
            processor.run_once()
        finally:
            db.close()
