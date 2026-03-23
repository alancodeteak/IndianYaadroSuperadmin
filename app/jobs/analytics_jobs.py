from app.api.core.logger import get_logger

log = get_logger(__name__)


def refresh_analytics_cache_job() -> None:
    # Placeholder for async worker/cron.
    log.info("refresh_analytics_cache_job")

