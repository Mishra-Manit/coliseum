"""
MongoDB connection test script.
Run from backend directory: python -m mess_around.test_mongodb
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from config import settings


async def test_connection():
    client = AsyncIOMotorClient(settings.mongodb_url)

    # Test connection with ping
    try:
        await client.admin.command("ping")
        print("MongoDB connection successful!\n")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # List ALL databases on the cluster
    print("Databases on cluster:")
    db_names = await client.list_database_names()
    for db_name in db_names:
        db = client[db_name]
        collections = await db.list_collection_names()
        print(f"\n  {db_name}/")
        if not collections:
            print("     (no collections)")
        for coll in collections:
            count = await db[coll].count_documents({})
            print(f"     - {coll}: {count} documents")

    # Show sample documents from sample_mflix (your data)
    print("\n" + "=" * 50)
    print("Sample documents from 'sample_mflix':")
    print("=" * 50)

    sample_db = client["sample_mflix"]
    collections = await sample_db.list_collection_names()

    for coll in collections[:3]:  # First 3 collections
        print(f"\n--- {coll} ---")
        async for doc in sample_db[coll].find().limit(1):
            doc["_id"] = str(doc["_id"])
            # Truncate long fields for readability
            for key, val in doc.items():
                if isinstance(val, str) and len(val) > 100:
                    doc[key] = val[:100] + "..."
            print(doc)

    client.close()


if __name__ == "__main__":
    asyncio.run(test_connection())
