from app.repositories.order_repository import OrderRepository


def test_order_repository_has_required_methods():
    required = [
        "list_orders",
        "count_orders",
        "get_by_id",
        "create_order",
        "update_order",
    ]

    for method in required:
        assert hasattr(OrderRepository, method)
