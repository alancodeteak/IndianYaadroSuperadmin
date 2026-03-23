from app.api.core.logger import get_logger

log = get_logger(__name__)


def send_invoice_email_job(invoice_id: int, recipient: str) -> None:
    # Placeholder for Celery/RQ/FastAPI background integration.
    log.info(
        "send_invoice_email_job",
        extra={"invoice_id": invoice_id, "recipient": recipient},
    )

