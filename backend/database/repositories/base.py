"""
BaseRepository Abstract Class

Base class for all MongoDB repositories providing common CRUD operations.

Methods:
- create(document: Dict) -> str: Insert document, return ID
- find_by_id(id: str) -> Optional[Dict]: Find single document
- update(id: str, updates: Dict) -> bool: Update document
- delete(id: str) -> bool: Delete document
- find_many(filter: Dict, limit: int, skip: int) -> List[Dict]

Subclasses override collection_name and add specialized queries.
"""
