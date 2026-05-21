"""
WORLD_BUILDER Package

This package contains worldbuilding and lore management systems:
- worldbuilding_rag: Categories + RAG system engine
- realitas_lore: All Realitas Neo worldbuilding content
"""

from WORLD_BUILDER.worldbuilding_rag import (
    WorldbuildingCategory,
    WorldbuildingRAGSystem,
    WorldbuildingDocument,
    initialize_worldbuilding_rag,
    get_worldbuilding_rag,
    get_category_display_name,
    CATEGORY_DESCRIPTIONS
)

__all__ = [
    # RAG System
    'WorldbuildingCategory',
    'WorldbuildingRAGSystem',
    'WorldbuildingDocument',
    'initialize_worldbuilding_rag',
    'get_worldbuilding_rag',
    'get_category_display_name',
    'CATEGORY_DESCRIPTIONS',
]
