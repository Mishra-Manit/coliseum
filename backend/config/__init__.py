"""
Configuration module initialization.
Exports configuration components for use throughout the application.
"""

from config.settings import settings, get_settings

__all__ = ["settings", "get_settings"]
