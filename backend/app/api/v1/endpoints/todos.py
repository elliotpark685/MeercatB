from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.todo import Todo
from app.models.user import User
from app.schemas.todo import TodoCreate, TodoResponse, TodoUpdate

router = APIRouter()


@router.get("", response_model=list[TodoResponse])
def list_todos(
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Todo]:
    query = select(Todo).where(Todo.user_id == user.id)
    if from_date:
        query = query.where(Todo.due_date >= from_date)
    if to_date:
        query = query.where(Todo.due_date <= to_date)
    return list(db.scalars(query.order_by(Todo.is_completed, Todo.due_date, Todo.created_at.desc())).all())


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(
    payload: TodoCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Todo:
    todo = Todo(user_id=user.id, **payload.model_dump())
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@router.patch("/{todo_id}", response_model=TodoResponse)
def update_todo(
    todo_id: int,
    payload: TodoUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Todo:
    todo = db.scalar(select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id))
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(todo, field, value)
    db.commit()
    db.refresh(todo)
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    todo = db.scalar(select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id))
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    db.delete(todo)
    db.commit()
