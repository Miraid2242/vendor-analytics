# seed_db.py
import asyncio
import datetime
import random
from sqlalchemy.future import select
from sqlalchemy import text
from database import SessionLocal
from models import Product, Order

async def seed_db():
    async with SessionLocal() as session:
        # Clear existing data (optional)
        await session.execute(text("DELETE FROM orders"))
        await session.execute(text("DELETE FROM products"))
        await session.commit()

        # Add sample products
        products = [
            Product(name="Apples", stock=100, price=1.5, vendor_id=1),
            Product(name="Bananas", stock=80, price=0.8, vendor_id=1),
            Product(name="Oranges", stock=50, price=1.2, vendor_id=1),
            Product(name="Grapes", stock=60, price=2.0, vendor_id=1),
            Product(name="Mangoes", stock=40, price=2.5, vendor_id=1),
        ]

        session.add_all(products)
        await session.commit()

        # Reload products so IDs are populated
        result = await session.execute(select(Product))
        products = result.scalars().all()

        # Add sample orders for past 5 days
        for day_offset in range(5):
            order_date = datetime.datetime.now() - datetime.timedelta(days=day_offset)
            for product in products:
                quantity = random.randint(5, 20)
                total_price = quantity * product.price
                order = Order(
                    product_id=product.id,
                    quantity=quantity,
                    total_price=total_price,
                    date=order_date
                )
                session.add(order)
            await session.commit()

    print("Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_db())
