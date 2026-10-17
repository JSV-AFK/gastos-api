from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.deps import CurrentUser, DbSession
from app.models import Category, Expense
from app.schemas import CategoryCreate, CategoryOut

router = APIRouter(prefix="/categories", tags=["Categorías"])


def get_own_category(db: DbSession, user: CurrentUser, category_id: int) -> Category:
    category = db.scalar(
        select(Category).where(Category.id == category_id, Category.user_id == user.id)
    )
    if category is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return category


def ensure_unique_name(db: DbSession, user: CurrentUser, name: str, exclude_id: int | None = None):
    query = select(Category).where(
        Category.user_id == user.id, func.lower(Category.name) == name.lower()
    )
    existing = db.scalar(query)
    if existing and existing.id != exclude_id:
        raise HTTPException(status_code=409, detail="Ya tienes una categoría con ese nombre")


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, db: DbSession, user: CurrentUser):
    name = data.name.strip()
    ensure_unique_name(db, user, name)
    category = Category(name=name, user_id=user.id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("", response_model=list[CategoryOut])
def list_categories(db: DbSession, user: CurrentUser):
    return db.scalars(
        select(Category).where(Category.user_id == user.id).order_by(Category.name)
    ).all()


@router.put("/{category_id}", response_model=CategoryOut)
def rename_category(category_id: int, data: CategoryCreate, db: DbSession, user: CurrentUser):
    category = get_own_category(db, user, category_id)
    name = data.name.strip()
    ensure_unique_name(db, user, name, exclude_id=category.id)
    category.name = name
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: DbSession, user: CurrentUser):
    category = get_own_category(db, user, category_id)
    has_expenses = db.scalar(
        select(func.count()).select_from(Expense).where(Expense.category_id == category.id)
    )
    if has_expenses:
        raise HTTPException(
            status_code=409,
            detail="No se puede borrar: la categoría tiene gastos asociados",
        )
    db.delete(category)
    db.commit()