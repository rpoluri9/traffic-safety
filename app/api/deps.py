"""Shared dependencies: DB session + API-key auth."""
from fastapi import Depends
from sqlalchemy.orm import Session

from ..core.security import require_api_key
from ..db.session import get_db


def authed_db(
    db: Session = Depends(get_db), _key: str = Depends(require_api_key)
) -> Session:
    return db
