# crud.py
from typing import List
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from models import Product, Order
from schemas import Summary, SalesTrendData, InventoryChange, TopProduct
import datetime
import logging

logger = logging.getLogger(__name__)

# Constants
LOW_STOCK_THRESHOLD = 10
SALES_TREND_DAYS = 5
RECENT_INVENTORY_LIMIT = 5
TOP_PRODUCTS_LIMIT = 5

# Dashboard summary
async def get_dashboard_summary(db: AsyncSession) -> Summary:
    # Total Sales (aggregate)
    result = await db.execute(select(func.coalesce(func.sum(Order.total_price), 0.0)))
    total_sales = float(result.scalar_one())

    # Total Orders (aggregate)
    result = await db.execute(select(func.count(Order.id)))
    total_orders = int(result.scalar_one())

    # Low Stock
    result = await db.execute(select(func.count(Product.id)).where(Product.stock < LOW_STOCK_THRESHOLD))
    low_stock_count = int(result.scalar_one())

    logger.info("Dashboard summary fetched: sales=%s orders=%s low_stock=%s", total_sales, total_orders, low_stock_count)

    return Summary(totalSales=total_sales, totalOrders=total_orders, lowStock=low_stock_count)

# Sales trend (past SALES_TREND_DAYS days)
async def get_sales_trend(db: AsyncSession) -> SalesTrendData:
    labels: List[str] = []
    data: List[float] = []

    today = datetime.date.today()
    for days_ago in range(SALES_TREND_DAYS - 1, -1, -1):
        day = today - datetime.timedelta(days=days_ago)
        start_dt = datetime.datetime.combine(day, datetime.time.min)
        end_dt = datetime.datetime.combine(day, datetime.time.max)

        q: Select = select(func.coalesce(func.sum(Order.total_price), 0.0)).where(
            Order.date >= start_dt,
            Order.date <= end_dt,
        )
        result = await db.execute(q)
        day_sales = float(result.scalar_one())

        labels.append(day.strftime("%b %d"))  # e.g., "Sep 22"
        data.append(day_sales)

    return SalesTrendData(labels=labels, data=data)

# Recent inventory changes (simple: latest products)
async def get_inventory_changes(db: AsyncSession) -> List[InventoryChange]:
    result = await db.execute(select(Product).order_by(Product.id.desc()).limit(RECENT_INVENTORY_LIMIT))
    products = result.scalars().all()

    changes: List[InventoryChange] = []
    for p in products:
        changes.append(
            InventoryChange(
                product=p.name,
                change=p.stock,
                date=str(datetime.date.today()),  # Placeholder: use actual log/timestamp if available
            )
        )
    return changes

# Top performing products (by units sold)
async def get_top_products(db: AsyncSession) -> List[TopProduct]:
    # Aggregate orders per product
    q = (
        select(
            Order.product_id.label("product_id"),
            func.coalesce(func.sum(Order.quantity), 0).label("units"),
            func.coalesce(func.sum(Order.total_price), 0.0).label("revenue"),
        )
        .group_by(Order.product_id)
        .order_by(func.sum(Order.quantity).desc())
        .limit(TOP_PRODUCTS_LIMIT)
    )

    result = await db.execute(q)
    rows = result.all()

    top_products: List[TopProduct] = []
    for row in rows:
        pid = row.product_id
        units = int(row.units)
        revenue = float(row.revenue)
        product_obj = await db.get(Product, pid)
        product_name = product_obj.name if product_obj else f"Product {pid}"
        top_products.append(TopProduct(product=product_name, unitsSold=units, revenue=revenue))

    return top_products

# Recommendations
async def get_recommendations(db: AsyncSession) -> List[str]:
    recommendations: List[str] = []

    # Low stock recommendations
    result = await db.execute(select(Product).where(Product.stock < LOW_STOCK_THRESHOLD))
    low_stock_products = result.scalars().all()
    for p in low_stock_products:
        recommendations.append(f"Restock {p.name}: inventory below {LOW_STOCK_THRESHOLD} units")

    # Promote top-selling product
    top_products = await get_top_products(db)
    if top_products:
        recommendations.append(f"Promote {top_products[0].product}: high sales recently")

    # Simple mocked forecast recommendation
    recommendations.append("Forecast: expected 15% increase in total sales next week (estimate)")

    return recommendations
