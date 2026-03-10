from sqlalchemy import Select, func, select
from sqlalchemy.orm import Query, Session


DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 200


def normalize_pagination(page: int, page_size: int) -> tuple[int, int]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
    return page, page_size


def paginate_query(query: Query, page: int, page_size: int):
    """Apply page/page_size to an ORM query and return metadata + records."""
    page, page_size = normalize_pagination(page, page_size)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "data": items,
    }


def paginate_select(db: Session, stmt: Select, count_stmt: Select, page: int, page_size: int):
    """Pagination helper for select() style queries."""
    page, page_size = normalize_pagination(page, page_size)
    total = db.execute(count_stmt).scalar_one()
    records = db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "data": records,
    }
