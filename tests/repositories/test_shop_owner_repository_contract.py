from app.repositories.shop_owner_repository import ShopOwnerRepository


def test_shop_owner_repository_has_required_methods():
    required = [
        "list_supermarkets",
        "get_supermarket_detail_by_user_id",
        "create_supermarket",
    ]
    for method in required:
        assert hasattr(ShopOwnerRepository, method)
