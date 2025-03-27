"""
Display components for CHUI UI system.

This package provides enhanced display components for tables, panels,
and other visual elements in the CHUI framework.
"""

from .tables import (
    TableDisplayManager, 
    TableConfig, 
    ColumnConfig, 
    TableBuilder,
    ColumnAlign,
    create_table
)

from .panels import (
    PanelManager,
    PanelType,
    PanelStyleConfig,
    PanelSection,
    create_section
)

__all__ = [
    'TableDisplayManager',
    'TableConfig',
    'ColumnConfig', 
    'TableBuilder',
    'ColumnAlign',
    'create_table',
    'PanelManager',
    'PanelType',
    'PanelStyleConfig',
    'PanelSection',
    'create_section'
]