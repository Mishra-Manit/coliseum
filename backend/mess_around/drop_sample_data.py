"""
Drop sample_mflix database from MongoDB.
Run from backend directory: python -m mess_around.drop_sample_data
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from config import settings


async def drop_sample_data():
    client = AsyncIOMotorClient(settings.mongodb_url)

    # Show what will be deleted
    db = client["sample_mflix"]
    collections = await db.list_collection_names()

    print("Will delete 'sample_mflix' database with collections:")
    for coll in collections:
        count = await db[coll].count_documents({})
        print(f"   - {coll}: {count} documents")

    # Confirm
    confirm = input("\nType 'yes' to confirm deletion: ")
    if confirm.lower() != "yes":
        print("Cancelled.")
        client.close()
        return

    # Drop the database
    await client.drop_database("sample_mflix")
    print("\nDeleted 'sample_mflix' database.")

    client.close()


if __name__ == "__main__":
    asyncio.run(drop_sample_data())
