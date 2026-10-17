import datetime as dt

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.deps import CurrentUser, DbSession
from app.models import Category, Expense
from app.schemas import ExpenseCreate, ExpenseOut, ExpenseUpdate

router = APIRouter(prefix="/expenses", tags=["Gastos"])


def ensure_own_category(db: DbSession, user: CurrentUser, category_id: int) -> None:
    category = db.scalar(
        select(Category).where(Category.id == category_id, Category.user_id == user.id)
    )
    if category is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")


def get_own_expense(db: DbSession, user: CurrentUser, expense_id: int) -> Expense:
    expense = db.scalar(
        select(Expense).where(Expense.id == expense_id, Expense.user_id == user.id)
    )
    if expense is None:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    return expense


@router.post("", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(data: ExpenseCreate, db: DbSession, user: CurrentUser):
    ensure_own_category(db, user, data.category_id)
    expense = Expense(**data.model_dump(), user_id=user.id)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("", response_model=list[ExpenseOut])
def list_expenses(
    db: DbSession,
    user: CurrentUser,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    category_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    query = select(Expense).where(Expense.user_id == user.id)
    if date_from:
        query = query.where(Expense.date >= date_from)
    if date_to:
        query = query.where(Expense.date <= date_to)
    if category_id:
        query = query.where(Expense.category_id == category_id)
    query = query.order_by(Expense.date.desc(), Expense.id.desc()).offset(skip).limit(limit)
    return db.scalars(query).all()


@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: int, db: DbSession, user: CurrentUser):
    return get_own_expense(db, user, expense_id)


@router.patch("/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, data: ExpenseUpdate, db: DbSession, user: CurrentUser):
    expense = get_own_expense(db, user, expense_id)
    changes = data.model_dump(exclude_unset=True)
    if "category_id" in changes and changes["category_id"] is not None:
        ensure_own_category(db, user, changes["category_id"])
    for field, value in changes.items():
        if value is not None:
            setattr(expense, field, value)
    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, db: DbSession, user: CurrentUser):
    expense = get_own_expense(db, user, expense_id)
    db.delete(expense)
    db.commit()