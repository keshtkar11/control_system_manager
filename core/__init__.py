"""ماژول هسته برنامه - شامل مدل‌ها، دیتابیس و منطق اصلی"""

from .models import Motor, ProjectSection, Revision, Project
from .database import DatabaseManager
from .history import HistoryManager
from .validation_errors import (
    ErrorSeverity,
    ValidationError,
    ValidationErrorCollector,
    validate_device_components,
    validate_project_components,
)
from .validators import (
    validate_device_name,
    validate_io_value,
    validate_section_name,
    validate_project_name
)
from .constants import (
    COMPONENT_LABELS,
    COMPONENT_LABELS_FA,
    COMPONENT_LABELS_EN,
    COMPONENT_KEYS,
    COMPONENT_FIELDS,
    IO_CALCULATION,
    DEFAULT_IO_CONFIG,
    CABLE_SIZE,
    CABLE_SIZE_MAP,
    COLORS,
    DEFAULT_SECTIONS,
    DEFAULT_DB_PATH,
    LIMITS,
    TABLE_COLUMNS,
    EXPORT,
    WINDOW,
    STATUS_KEYS,
    COMMAND_KEYS,
    RESERVED_KEYS,
    EXCLUDED_FROM_COMPONENTS
)

__all__ = [
    # مدل‌ها
    'Motor',
    'ProjectSection',
    'Project',
    
    # مدیریت
    'DatabaseManager',
    'HistoryManager',
    
    # اعتبارسنجی
    'validate_device_name',
    'validate_io_value',
    'validate_section_name',
    'validate_project_name',
    
    # ثابت‌ها
    'COMPONENT_LABELS',
    'COMPONENT_LABELS_FA',
    'COMPONENT_LABELS_EN',
    'COMPONENT_KEYS',
    'COMPONENT_FIELDS',
    'IO_CALCULATION',
    'DEFAULT_IO_CONFIG',
    'CABLE_SIZE',
    'CABLE_SIZE_MAP',
    'COLORS',
    'DEFAULT_SECTIONS',
    'DEFAULT_DB_PATH',
    'LIMITS',
    'TABLE_COLUMNS',
    'EXPORT',
    'WINDOW',
    'STATUS_KEYS',
    'COMMAND_KEYS',
    'RESERVED_KEYS',
    'EXCLUDED_FROM_COMPONENTS',
]