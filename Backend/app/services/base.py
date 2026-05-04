from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def commit_or_400(db: Session, instance):
    try:
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate or invalid data") from exc
