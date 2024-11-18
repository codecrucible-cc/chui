"""
Core plugin system for the Chui framework.
"""
from .base import Plugin
from .discovery import PluginDiscovery
from .registry import PluginRegistry

__all__ = ['Plugin', 'PluginDiscovery', 'PluginRegistry']