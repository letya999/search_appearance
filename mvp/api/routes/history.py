from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from mvp.storage.database import get_session
from mvp.storage.models import SearchSession, SavedExample
from mvp.api.routes.collections import get_current_user_id

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/history", response_model=List[SearchSession])
def get_search_history(session: Session = Depends(get_session)):
    user_id = UUID(get_current_user_id())
    stmt = select(SearchSession).where(SearchSession.user_id == user_id).order_by(SearchSession.started_at.desc())
    results = session.exec(stmt).all()
    return results

@router.get("/saved", response_model=List[SavedExample])
def get_saved_examples(session: Session = Depends(get_session)):
    user_id = UUID(get_current_user_id())
    stmt = select(SavedExample).where(SavedExample.user_id == user_id).order_by(SavedExample.created_at.desc())
    return session.exec(stmt).all()

@router.post("/saved", response_model=SavedExample)
def save_example(example: SavedExample, session: Session = Depends(get_session)):
    user_id = UUID(get_current_user_id())
    example.user_id = user_id
    session.add(example)
    session.commit()
    session.refresh(example)
    return example

@router.delete("/saved/{example_id}")
def delete_saved_example(example_id: UUID, session: Session = Depends(get_session)):
    user_id = UUID(get_current_user_id())
    example = session.get(SavedExample, example_id)
    if not example or example.user_id != user_id:
        raise HTTPException(status_code=404, detail="Example not found")
    session.delete(example)
    session.commit()
    return {"ok": True}
