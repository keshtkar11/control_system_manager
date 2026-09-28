# gui/help/__init__.py
"""
ماژول Help Center
"""

from .help_content import (
    HELP_SECTIONS,
    get_section,
    get_all_sections,
    get_section_ids,
)
from .help_dialog import HelpDialog


__all__ = [
    'HELP_SECTIONS',
    'get_section',
    'get_all_sections',
    'get_section_ids',
    'HelpDialog',
]