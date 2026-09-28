# ai/project_matcher.py
"""
تطبیق هوشمند نام پروژه — با ۳ لایه

1. Aliases سخت‌افزاری (STATIC) — سریع و ثابت
2. Aliases یادگیری (DB) — داینامیک از تأیید کاربران
3. Fuzzy + Transliteration — تطبیق خودکار برای تایپ اشتباه

نحوه کار:
    matcher = ProjectMatcher(db_manager, app)
    name, confidence, method = matcher.match("ربانی", ["Rabbani", "01-Typical"])
    # → ("Rabbani", 0.95, "static")
"""

import re
import logging
from difflib import SequenceMatcher
from datetime import datetime
from typing import Optional, List, Dict, Tuple

logger = logging.getLogger(__name__)


# ================================================================
# TRANSLITERATION MAP (فارسی → فینگلیش)
# ================================================================

FA_TO_EN_MAP = {
    # حروف اصلی
    'ا': 'a', 'آ': 'a', 'أ': 'a', 'إ': 'a',
    'ب': 'b', 'پ': 'p', 'ت': 't', 'ث': 's',
    'ج': 'j', 'چ': 'ch', 'ح': 'h', 'خ': 'kh',
    'د': 'd', 'ذ': 'z', 'ر': 'r', 'ز': 'z', 'ژ': 'zh',
    'س': 's', 'ش': 'sh', 'ص': 's', 'ض': 'z',
    'ط': 't', 'ظ': 'z', 'ع': 'a', 'غ': 'gh',
    'ف': 'f', 'ق': 'gh', 'ک': 'k', 'ك': 'k',
    'گ': 'g', 'ل': 'l', 'م': 'm', 'ن': 'n',
    'و': 'v', 'ه': 'h', 'ی': 'y', 'ي': 'y',
    'ء': '', 'ئ': 'y', 'ة': 'h',
    # نگه‌داشتن اعداد و علائم مفید
    '0': '0', '1': '1', '2': '2', '3': '3', '4': '4',
    '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
    '-': '-', '_': '_', ' ': ' ',
}


def transliterate_fa(text: str) -> str:
    """تبدیل حروف فارسی به فینگلیش"""
    result = ''
    for char in (text or '').lower():
        result += FA_TO_EN_MAP.get(char, char)
    return result


def similarity(a: str, b: str) -> float:
    """محاسبه شباهت (0.0 - 1.0)"""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _clean_name(text: str) -> str:
    """
    نرمال‌سازی نام:
    - lowercase
    - حذف علائم نگارشی غیرضروری
    - حذف فاصله‌های اضافی
    """
    if not text:
        return ''
    
    text = text.lower()
    # حفظ: حروف انگلیسی، اعداد، حروف فارسی، فاصله، خط تیره، زیرخط
    text = re.sub(r'[^\w\s\u0600-\u06FF\u200c\-]', '', text)
    # نیم‌فاصله → فاصله
    text = text.replace('\u200c', ' ')
    # چند فاصله → یک فاصله
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# ================================================================
# STATIC ALIASES (لایه ۱)
# ================================================================

# ⚠️ این aliases را می‌توانید برای پروژه‌های رایج اضافه کنید
# ولی سیستم با یادگیری، خودش بقیه را مدیریت می‌کند
STATIC_PROJECT_ALIASES = {
    'Rabbani': ['ربانی', 'ربانى', 'rabbani', 'rbani', 'rabany'],
    'Abadrahan': ['ابادراهان', 'آبادرهان', 'abadrahan', 'abadrhan'],
    '01-Typical': ['تیپیکال', 'typical', '01typical', '01 typical'],
    'Data Center Saderat': [
        'دیتاسنتر صادرات', 'دیتا سنتر صادرات', 'صادرات',
        'saderat', 'datacenter saderat', 'saderat dc', 'dc saderat'
    ],
    'Data Center Tejarat': [
        'دیتاسنتر تجارت', 'دیتا سنتر تجارت', 'تجارت',
        'tejarat', 'datacenter tejarat', 'tejarat dc', 'dc tejarat'
    ],
    'Haspital Nikan Gharb': [
        'بیمارستان نیکان غرب', 'نیکان غرب', 'hospital nikan',
        'nikan gharb', 'nikan'
    ],
    'Mall Sam Shariati': [
        'مال سام شریعتی', 'سام شریعتی', 'sam shariati', 'mall sam'
    ],
    'Nikan Gharb AHU': [
        'نیکان غرب ahu', 'ahu نیکان', 'nikan gharb ahu', 'ahu nikan'
    ],
}


# ================================================================
# PROJECT MATCHER
# ================================================================

class ProjectMatcher:
    """
    تطبیق هوشمند نام پروژه با ۳ لایه
    """
    
    # ===== آستانه‌ها =====
    FUZZY_THRESHOLD = 0.75        # 75٪ به بالا → قبول
    FUZZY_AMBIGUOUS = 0.55        # 55-75٪ → نیاز به تأیید
    
    def __init__(self, db_manager, app):
        self.db = db_manager
        self.app = app
        self._ensure_db_table()
        self._alias_cache = None      # cache برای سرعت
        self._cache_dirty = True
    
    # ================================================================
    # DB SETUP
    # ================================================================
    
    def _ensure_db_table(self):
        """ایجاد جدول aliases در دیتابیس"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS project_aliases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    alias TEXT NOT NULL,
                    created_at TEXT,
                    UNIQUE(project_name, alias)
                )
            ''')
            
            conn.commit()
            logger.info("✅ project_aliases table ensured")
        
        except Exception as e:
            logger.warning(f"Could not create project_aliases table: {e}")
    
    # ================================================================
    # MAIN MATCH
    # ================================================================
    
    def match(
        self, 
        text: str, 
        project_names: List[str]
    ) -> Tuple[Optional[str], float, str]:
        """
        تطبیق نام پروژه — با ۳ لایه
        
        Args:
            text: متن حاوی نام پروژه
            project_names: لیست نام‌های واقعی پروژه‌ها
        
        Returns:
            (project_name, confidence, method)
            - method ∈ {'exact', 'static', 'learned', 'substring', 'fuzzy', 'none'}
        """
        if not text or not project_names:
            return (None, 0.0, 'none')
        
        text_clean = _clean_name(text)
        if not text_clean:
            return (None, 0.0, 'none')
        
        # ============================================================
        # لایه ۱: تطبیق دقیق
        # ============================================================
        for name in project_names:
            if _clean_name(name) == text_clean:
                logger.debug(f"✅ Match exact: '{text}' → '{name}'")
                return (name, 1.0, 'exact')
        
        # ============================================================
        # لایه ۲: Aliases سخت‌افزاری
        # ============================================================
        for name, aliases in STATIC_PROJECT_ALIASES.items():
            if name not in project_names:
                continue
            for alias in aliases:
                alias_clean = _clean_name(alias)
                if not alias_clean:
                    continue
                # تطبیق کامل یا substring
                if alias_clean == text_clean:
                    logger.debug(f"✅ Match static: '{text}' → '{name}' (exact alias)")
                    return (name, 0.98, 'static')
                if len(alias_clean) >= 4 and alias_clean in text_clean:
                    logger.debug(f"✅ Match static: '{text}' → '{name}' (substring alias)")
                    return (name, 0.95, 'static')
        
        # ============================================================
        # لایه ۳: Aliases یادگیری (DB)
        # ============================================================
        learned = self._load_learned_aliases()
        for alias_clean, name in learned.items():
            if name not in project_names:
                continue
            if alias_clean == text_clean:
                logger.debug(f"✅ Match learned: '{text}' → '{name}'")
                return (name, 0.92, 'learned')
            if len(alias_clean) >= 4 and alias_clean in text_clean:
                logger.debug(f"✅ Match learned: '{text}' → '{name}' (substring)")
                return (name, 0.88, 'learned')
        
        # ============================================================
        # لایه ۴: Substring Match
        # ============================================================
        # اگر نام پروژه کامل در متن باشد
        candidates = []
        for name in project_names:
            name_clean = _clean_name(name)
            
            # نام کامل در متن
            if name_clean in text_clean:
                candidates.append((name, len(name_clean), 0.85, 'full_substring'))
                continue
            
            # کلمات نام پروژه در متن
            name_words = [w for w in name_clean.split() if len(w) >= 3]
            text_words = text_clean.split()
            
            if len(name_words) >= 2:
                matched = sum(1 for w in name_words if w in text_words)
                ratio = matched / len(name_words)
                if ratio >= 0.6:
                    candidates.append((name, matched, 0.60 + ratio * 0.20, 'word_match'))
        
        if candidates:
            candidates.sort(key=lambda x: (-x[1], -x[2]))
            best = candidates[0]
            logger.debug(f"✅ Match substring: '{text}' → '{best[0]}' ({best[3]})")
            return (best[0], best[2], 'substring')
        
        # ============================================================
        # لایه ۵: Fuzzy + Transliteration
        # ============================================================
        text_translit = transliterate_fa(text_clean)
        
        best_name = None
        best_score = 0.0
        
        for name in project_names:
            name_clean = _clean_name(name)
            name_translit = transliterate_fa(name_clean)
            
            # مقایسه‌ی مستقیم
            score_direct = similarity(text_clean, name_clean)
            # مقایسه با transliteration
            score_translit = similarity(text_translit, name_translit)
            # مقایسه‌ی partial
            score_partial = 0.0
            min_len = min(len(text_clean), len(name_clean))
            if min_len >= 4:
                score_partial = similarity(
                    text_clean[:min_len],
                    name_clean[:min_len]
                )
            
            score = max(score_direct, score_translit, score_partial)
            
            if score > best_score:
                best_score = score
                best_name = name
        
        if best_name and best_score >= self.FUZZY_THRESHOLD:
            logger.debug(f"✅ Match fuzzy: '{text}' → '{best_name}' ({best_score:.2f})")
            return (best_name, best_score, 'fuzzy')
        
        # ============================================================
        # هیچ تطبیقی پیدا نشد
        # ============================================================
        logger.debug(f"❌ No match for '{text}' (best score: {best_score:.2f})")
        return (None, best_score, 'none')
    
    # ================================================================
    # AMBIGUOUS MATCHES (برای تأیید کاربر)
    # ================================================================
    
    def find_ambiguous(
        self, 
        text: str, 
        project_names: List[str], 
        top_n: int = 5
    ) -> List[Tuple[str, float]]:
        """
        پیدا کردن چند پروژه‌ی نزدیک (برای تأیید کاربر)
        
        Returns:
            [(project_name, score), ...]
        """
        if not text or not project_names:
            return []
        
        text_clean = _clean_name(text)
        text_translit = transliterate_fa(text_clean)
        
        scores = []
        for name in project_names:
            name_clean = _clean_name(name)
            name_translit = transliterate_fa(name_clean)
            
            score = max(
                similarity(text_clean, name_clean),
                similarity(text_translit, name_translit),
            )
            scores.append((name, score))
        
        scores.sort(key=lambda x: -x[1])
        return scores[:top_n]
    
    # ================================================================
    # LEARNING
    # ================================================================
    
    def learn_alias(self, project_name: str, alias: str) -> bool:
        """
        ذخیره‌ی یک alias جدید
        
        Args:
            project_name: نام واقعی پروژه
            alias: نامی که کاربر استفاده کرده
        
        Returns:
            True اگر موفق باشد
        """
        try:
            alias_clean = _clean_name(alias)
            if not alias_clean or len(alias_clean) < 2:
                return False
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO project_aliases
                (project_name, alias, created_at)
                VALUES (?, ?, ?)
            ''', (project_name, alias_clean, datetime.now().isoformat()))
            
            conn.commit()
            
            # پاک کردن cache
            self._cache_dirty = True
            
            logger.info(f"✅ Learned alias: '{alias_clean}' → '{project_name}'")
            return True
        
        except Exception as e:
            logger.error(f"Failed to learn alias: {e}")
            return False
    
    def _load_learned_aliases(self) -> Dict[str, str]:
        """بارگذاری aliases یادگیری‌شده (با cache)"""
        if not self._cache_dirty and self._alias_cache is not None:
            return self._alias_cache
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT alias, project_name FROM project_aliases')
            
            result = {}
            for row in cursor.fetchall():
                result[row[0]] = row[1]
            
            self._alias_cache = result
            self._cache_dirty = False
            return result
        
        except Exception as e:
            logger.warning(f"Could not load aliases: {e}")
            return {}
    
    def list_learned_aliases(self) -> Dict[str, List[str]]:
        """لیست همه‌ی aliases یادگیری‌شده"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT project_name, alias
                FROM project_aliases
                ORDER BY project_name, alias
            ''')
            
            result = {}
            for row in cursor.fetchall():
                if row[0] not in result:
                    result[row[0]] = []
                result[row[0]].append(row[1])
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to list aliases: {e}")
            return {}
    
    def clear_alias(self, project_name: str, alias: str) -> bool:
        """حذف یک alias یادگیری‌شده"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM project_aliases
                WHERE project_name = ? AND alias = ?
            ''', (project_name, _clean_name(alias)))
            
            conn.commit()
            self._cache_dirty = True
            
            return cursor.rowcount > 0
        
        except Exception as e:
            logger.error(f"Failed to clear alias: {e}")
            return False
    
    def clear_all_aliases(self) -> int:
        """حذف همه‌ی aliases یادگیری‌شده"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM project_aliases')
            count = cursor.rowcount
            
            conn.commit()
            self._cache_dirty = True
            
            logger.info(f"🗑️ Cleared {count} aliases")
            return count
        
        except Exception as e:
            logger.error(f"Failed to clear aliases: {e}")
            return 0


# ================================================================
# EXPORTS
# ================================================================

__all__ = [
    'ProjectMatcher',
    'transliterate_fa',
    'similarity',
    '_clean_name',
]