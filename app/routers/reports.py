import datetime as dt

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import extract, func, select

from app.deps import CurrentUser, DbSession
from app.models import Category, Expense
from app.schemas import (
    CategoryReportItem,
    ExpenseOut,
    MonthlyReportItem,
    SummaryOut,
)

router = APIRouter(prefix="/reports", tags=["Reportes"])


def check_range(date_from: dt.date | None, date_to: dt.date | None) -> None:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=422, detail="date_from no puede ser posterior a date_to"
        )


def apply_range(query, date_from: dt.date | None, date_to: dt.date | None):
    if date_from:
        query = query.where(Expense.date >= date_from)
    if date_to:
        query = query.where(Expense.date <= date_to)
    return query


@router.get("/summary", response_model=SummaryOut)
def summary(
    db: DbSession,
    user: CurrentUser,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
):
    """Total, cantidad, promedio y gasto más grande en un rango de fechas."""
    check_range(date_from, date_to)

    totals_query = apply_range(
        select(func.coalesce(func.sum(Expense.amount), 0), func.count(Expense.id)).where(
            Expense.user_id == user.id
        ),
        date_from,
        date_to,
    )
    total, count = db.execute(totals_query).one()
    total = float(total)

    largest_query = apply_range(
        select(Expense).where(Expense.user_id == user.id), date_from, date_to
    )
    largest = db.scalar(largest_query.order_by(Expense.amount.desc(), Expense.id).limit(1))

    return SummaryOut(
        date_from=date_from,
        date_to=date_to,
        total=round(total, 2),
        count=count,
        average=round(total / count, 2) if count else 0.0,
        largest_expense=ExpenseOut.model_validate(largest) if largest else None,
    )


@router.get("/by-category", response_model=list[CategoryReportItem])
def by_category(
    db: DbSession,
    user: CurrentUser,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
):
    """Cuánto se gastó en cada categoría y qué porcentaje representa."""
    check_range(date_from, date_to)

    query = apply_range(
        select(
            Category.id,
            Category.name,
            func.sum(Expense.amount),
            func.count(Expense.id),
        )
        .join(Expense, Expense.category_id == Category.id)
        .where(Expense.user_id == user.id),
        date_from,
        date_to,
    )
    rows = db.execute(
        query.group_by(Category.id, Category.name).order_by(func.sum(Expense.amount).desc())
    ).all()

    grand_total = sum(float(row[2]) for row in rows)
    return [
        CategoryReportItem(
            category_id=row[0],
            category=row[1],
            total=round(float(row[2]), 2),
            count=row[3],
            percentage=round(float(row[2]) / grand_total * 100, 1) if grand_total else 0.0,
        )
        for row in rows
    ]


@router.get("/monthly", response_model=list[MonthlyReportItem])
def monthly(
    db: DbSession,
    user: CurrentUser,
    year: int | None = Query(default=None, ge=2000, le=2100),
):
    """Total por mes de un año (por defecto, el actual). Siempre devuelve los 12 meses."""
    year = year or dt.date.today().year

    rows = db.execute(
        select(
            extract("month", Expense.date),
            func.sum(Expense.amount),
            func.count(Expense.id),
        )
        .where(Expense.user_id == user.id, extract("year", Expense.date) == year)
        .group_by(extract("month", Expense.date))
    ).all()
    by_month = {int(row[0]): (float(row[1]), row[2]) for row in rows}

    return [
        MonthlyReportItem(
            month=f"{year}-{m:02d}",
            total=round(by_month.get(m, (0.0, 0))[0], 2),
            count=by_month.get(m, (0.0, 0))[1],
        )
        for m in range(1, 13)
    ]