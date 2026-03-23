def normalize_pagination(page: int, page_size: int, max_page_size: int = 100) -> tuple[int, int]:
    page = max(page, 1)
    page_size = max(1, min(page_size, max_page_size))
    return page, page_size

