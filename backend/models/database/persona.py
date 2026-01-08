"""
Persona MongoDB Schema

Defines the Persona document model for the 'personas' collection.
Stores weekly persona configuration metadata (actual prompts in Git).

Schema Fields:
- _id: ObjectId
- week_number: Integer week identifier
- start_date: ISO date string for week start
- end_date: ISO date string for week end
- persona_name: Display name (e.g., "Conservative Value Investor")
- config_file: Git file path reference (e.g., "personas/conservative_value.yaml")
- description: Short description of persona behavior
- active: Boolean indicating if this is the current active persona
- created_at: Document creation timestamp

Indexes:
- week_number (unique)
- active

Note: Personas rotate weekly (Monday 00:00 EST)
All 8 agents use the same persona in a given week.
"""

# TODO: Implement Pydantic models for Persona schema
# TODO: Create index definitions
