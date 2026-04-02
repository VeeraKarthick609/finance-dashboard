"""
Seed script: Creates 3 demo users and ~50 financial records.

Usage: python seed.py
"""

import random
from datetime import date, timedelta

import bcrypt
from dotenv import load_dotenv

load_dotenv()

from app.database import supabase

# --- Users ---

USERS = [
    {"email": "admin@example.com", "name": "Admin User", "role": "admin"},
    {"email": "analyst@example.com", "name": "Analyst User", "role": "analyst"},
    {"email": "viewer@example.com", "name": "Viewer User", "role": "viewer"},
]

DEFAULT_PASSWORD = "password123"

# --- Record templates ---

INCOME_CATEGORIES = {
    "Salary": (3000, 8000),
    "Freelance": (500, 3000),
    "Investments": (100, 2000),
    "Bonus": (500, 5000),
}

EXPENSE_CATEGORIES = {
    "Rent": (800, 2000),
    "Groceries": (50, 300),
    "Utilities": (50, 200),
    "Transport": (30, 150),
    "Entertainment": (20, 200),
    "Healthcare": (50, 500),
    "Insurance": (100, 400),
    "Subscriptions": (10, 50),
    "Dining Out": (15, 100),
    "Education": (50, 500),
}

INCOME_NOTES = [
    "Monthly salary deposit",
    "Client project payment",
    "Quarterly dividend",
    "Performance bonus",
    "Side project income",
    None,
]

EXPENSE_NOTES = [
    "Monthly rent payment",
    "Weekly grocery shopping",
    "Electricity and water bill",
    "Public transit pass",
    "Movie tickets",
    "Doctor visit copay",
    "Car insurance premium",
    "Netflix and Spotify",
    "Dinner with friends",
    "Online course",
    None,
    None,
]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def seed_users() -> list[dict]:
    print("Seeding users...")
    hashed = hash_password(DEFAULT_PASSWORD)
    created_users = []

    for user_data in USERS:
        # Check if already exists
        existing = (
            supabase.table("users")
            .select("id")
            .eq("email", user_data["email"])
            .execute()
        )
        if existing.data:
            print(f"  User {user_data['email']} already exists, skipping")
            created_users.append(existing.data[0])
            continue

        response = (
            supabase.table("users")
            .insert({**user_data, "password": hashed})
            .execute()
        )
        created_users.append(response.data[0])
        print(f"  Created {user_data['role']}: {user_data['email']}")

    return created_users


def seed_records(users: list[dict]) -> None:
    print("Seeding records...")
    admin_id = users[0]["id"]
    records = []
    today = date.today()

    for month_offset in range(6):
        # 1-2 income records per month
        for _ in range(random.randint(1, 2)):
            category = random.choice(list(INCOME_CATEGORIES.keys()))
            min_amt, max_amt = INCOME_CATEGORIES[category]
            record_date = today - timedelta(days=month_offset * 30 + random.randint(0, 28))
            records.append({
                "amount": round(random.uniform(min_amt, max_amt), 2),
                "type": "income",
                "category": category,
                "date": str(record_date),
                "notes": random.choice(INCOME_NOTES),
                "user_id": admin_id,
            })

        # 5-8 expense records per month
        for _ in range(random.randint(5, 8)):
            category = random.choice(list(EXPENSE_CATEGORIES.keys()))
            min_amt, max_amt = EXPENSE_CATEGORIES[category]
            record_date = today - timedelta(days=month_offset * 30 + random.randint(0, 28))
            records.append({
                "amount": round(random.uniform(min_amt, max_amt), 2),
                "type": "expense",
                "category": category,
                "date": str(record_date),
                "notes": random.choice(EXPENSE_NOTES),
                "user_id": admin_id,
            })

    # Batch insert in chunks of 20
    for i in range(0, len(records), 20):
        chunk = records[i : i + 20]
        supabase.table("records").insert(chunk).execute()

    print(f"  Created {len(records)} financial records")


def main():
    print("=" * 40)
    print("Finance Dashboard - Seed Data")
    print("=" * 40)

    users = seed_users()
    seed_records(users)

    print("=" * 40)
    print("Seeding complete!")
    print()
    print("Login credentials (all use same password):")
    print(f"  Password: {DEFAULT_PASSWORD}")
    for u in USERS:
        print(f"  {u['role']:>8}: {u['email']}")
    print("=" * 40)


if __name__ == "__main__":
    main()
