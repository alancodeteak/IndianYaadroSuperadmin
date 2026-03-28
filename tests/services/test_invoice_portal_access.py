"""Portal invoice access enforced in InvoiceService."""

from unittest.mock import MagicMock

import pytest

from app.domain.exceptions import PermissionDeniedError
from app.services.invoice_service import InvoiceService


def test_ensure_portal_invoice_access_denied_when_shop_mismatch():
    shop_repo = MagicMock()
    shop_repo.get_shop_id_by_email = MagicMock(return_value="shop-a")
    inv_repo = MagicMock()
    svc = InvoiceService(
        repository=inv_repo,
        session=MagicMock(),
        shop_owner_repository=shop_repo,
    )
    with pytest.raises(PermissionDeniedError):
        svc.ensure_portal_invoice_access("portal@test", "shop-b")
