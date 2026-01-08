"""
Events API Response Models

GET /api/events - Paginated event list
GET /api/events/{event_id} - Detailed event with bets

List response includes:
- total, limit, offset for pagination
- events array with summary data

Detail response includes:
- Full event data with intelligence_brief
- bets array with agent decisions and outcomes
"""
