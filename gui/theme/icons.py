# gui/theme/icons.py
"""
سیستم آیکون‌ها - Unicode Symbols
بدون نیاز به فایل خارجی
"""

# ================================================================
# ICONS (Unicode Symbols)
# ================================================================

ICONS = {
    # ═══ File & Project ═══
    'file':             '📄',
    'folder':           '📁',
    'folder_open':      '📂',
    'project':          '🏗️',
    'section':          '📂',
    'device':           '🔧',
    'new':              '➕',
    'open':             '📂',
    'save':             '💾',
    'import':           '📥',
    'export':           '📤',
    'backup':           '📦',
    'restore':          '📥',
    
    # ═══ Actions ═══
    'add':              '➕',
    'edit':             '✏️',
    'delete':           '🗑️',
    'copy':             '📋',
    'paste':            '📋',
    'cut':              '✂️',
    'undo':             '↶',
    'redo':             '↷',
    'refresh':          '🔄',
    'search':           '🔍',
    'filter':           '🔽',
    'sort':             '↕️',
    'clear':            '🗑️',
    'reset':            '🔄',
    'save_alt':         '💾',
    'cancel':           '❌',
    'close':            '✖️',
    'check':            '✅',
    'apply':            '✅',
    
    # ═══ Navigation ═══
    'up':               '⬆️',
    'down':             '⬇️',
    'left':             '⬅️',
    'right':            '➡️',
    'back':             '◀️',
    'forward':          '▶️',
    'home':             '🏠',
    'menu':             '☰',
    'more':             '⋯',
    'expand':           '▸',
    'collapse':         '▾',
    'chevron_right':    '›',
    'chevron_down':     '⌄',
    
    # ═══ Status ═══
    'success':          '✅',
    'warning':          '⚠️',
    'error':            '❌',
    'info':             'ℹ️',
    'question':         '❓',
    'loading':          '⏳',
    'lock':             '🔒',
    'unlock':           '🔓',
    
    # ═══ User & System ═══
    'user':             '👤',
    'users':            '👥',
    'admin':            '👑',
    'settings':         '⚙️',
    'config':           '🔧',
    'logout':           '🚪',
    'login':            '🔑',
    'password':         '🔒',
    
    # ═══ Data & Charts ═══
    'chart':            '📊',
    'chart_bar':        '📊',
    'chart_line':       '📈',
    'chart_pie':        '🥧',
    'report':           '📋',
    'table':            '📋',
    'list':             '📝',
    'grid':             '⊞',
    'database':         '🗄️',
    
    # ═══ Communication ═══
    'email':            '📧',
    'phone':            '📞',
    'message':          '💬',
    'notification':     '🔔',
    'toast':            '💬',
    
    # ═══ AI & Learning ═══
    'ai':               '🤖',
    'brain':            '🧠',
    'predict':          '🔮',
    'optimize':         '⚡',
    'magic':            '✨',
    'sparkles':         '✨',
    'lightning':        '⚡',
    
    # ═══ Actions (Specific) ═══
    'learn':            '🧠',
    'analyze':          '📈',
    'help':             '❓',
    'guide':            '📖',
    'keyboard':         '⌨️',
    'shortcuts':        '⌨️',
    'info_circle':      'ℹ️',
    'check_circle':     '✅',
    'x_circle':         '❌',
    'warning_triangle': '⚠️',
    
    # ═══ Theme ═══
    'dark':             '🌙',
    'light':            '☀️',
    'theme':            '🎨',
    
    # ═══ Special ═══
    'star':             '⭐',
    'heart':            '❤️',
    'fire':             '🔥',
    'rocket':           '🚀',
    'sparkle':          '✨',
    'trophy':           '🏆',
    'medal':            '🏅',
    'crown':            '👑',
    'shield':           '🛡️',
    'flag':             '🚩',
    'pin':              '📌',
    'bookmark':         '🔖',
    'tag':              '🏷️',
    'link':             '🔗',
    'attachment':       '📎',
    'image':            '🖼️',
    'video':            '🎬',
    'audio':            '🔊',
    'file_text':        '📄',
    'file_pdf':         '📕',
    'file_excel':       '📗',
    'file_word':        '📘',
    'file_zip':         '📦',
    
    # ═══ Components (Industry) ═══
    'motor':            '⚙️',
    'valve':            '🚰',
    'pump':             '💧',
    'fan':              '🌀',
    'valve':            '🚰',
    'sensor':           '📡',
    'thermometer':      '🌡️',
    'gauge':            '🎯',
    'meter':            '📏',
    'light':            '💡',
    'power':            '⚡',
    'plug':             '🔌',
    'battery':          '🔋',
    'factory':          '🏭',
    'building':         '🏢',
    'wrench':           '🔧',
    'hammer':           '🔨',
    'gear':             '⚙️',
    'chip':             '💾',
    'circuit':          '🔌',
}


# ================================================================
# SIZES
# ================================================================

ICON_SIZES = {
    'xs':    10,
    'sm':    12,
    'md':    14,
    'lg':    16,
    'xl':    20,
    '2xl':   24,
    '3xl':   32,
    '4xl':   48,
    '5xl':   64,
}


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def ico(name: str, fallback: str = '•') -> str:
    """دریافت آیکون با نام"""
    return ICONS.get(name, fallback)


def icon_with_text(icon_name: str, text: str, separator: str = '  ') -> str:
    """ترکیب آیکون و متن"""
    icon = ico(icon_name)
    return f"{icon}{separator}{text}"


# ================================================================
# EXPORTS
# ================================================================

__all__ = [
    'ICONS',
    'ICON_SIZES',
    'ico',
    'icon_with_text',
]