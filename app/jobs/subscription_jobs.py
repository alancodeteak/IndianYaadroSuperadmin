from app.api.core.logger import get_logger

log = get_logger(__name__)


def run_subscription_renewal_job(shop_id: str) -> None:
    # Placeholder for scheduling layer.
    log.info("run_subscription_renewal_job", extra={"shop_id": shop_id})

