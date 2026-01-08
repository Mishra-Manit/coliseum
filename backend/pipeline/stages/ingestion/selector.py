"""
Event Selector

Applies hard quota selection rules.

Quota: 5 events total
- 2 Politics events
- 1 Finance event
- 1 Sports event
- 1 Wildcard (any category)

Picks highest-scoring events within each category.
Filters out events that typically take >24 hours to resolve.
Locks current YES price at selection time.
"""
