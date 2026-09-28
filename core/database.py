"""مدیریت دیتابیس SQLite با قابلیت مهاجرت کامل"""

import sqlite3
import json
import os
import sys
import shutil
import tempfile
import zipfile
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

from .models import Project, ProjectSection, Motor, Revision, Valve
from .constants import DEFAULT_DB_PATH, COMPONENT_LABELS

logger = logging.getLogger(__name__)

# ================================================================
# ✅ نسخه Schema — با ON UPDATE CASCADE
# ================================================================
# 
# v1: Initial schema (revisions, valves, attachments, ...)
# v2: Added ON UPDATE CASCADE to all project_name FKs
# 
CURRENT_SCHEMA_VERSION = 2


# ================================================================
# ✅ SAFE ZIP EXTRACTION (جلوگیری از Zip Slip)
# ================================================================

def _safe_extract_zip(zip_path: str, extract_to: str) -> None:
    """
    استخراج امن فایل ZIP — جلوگیری از Zip Slip / Path Traversal
    """
    extract_to_resolved = Path(extract_to).resolve()
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.namelist():
            member_path = (extract_to_resolved / member).resolve()
            
            try:
                member_path.relative_to(extract_to_resolved)
            except ValueError:
                raise ValueError(
                    f"⚠️ Zip Slip detected: '{member}' tries to escape "
                    f"'{extract_to_resolved}'"
                )
        
        zf.extractall(extract_to)


class DatabaseManager:
    """مدیریت عملیات دیتابیس با قابلیت مهاجرت خودکار"""
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._conn = None
        self._ensure_directory()
        self._seed_database_if_needed()
        self._init_db()
        self._create_auto_backup()
        logger.info(f"Database initialized at: {db_path}")
    
    # ==================== متدهای اتصال ====================
    
    def get_connection(self) -> sqlite3.Connection:
        """دریافت اتصال به دیتابیس با مدیریت خطا"""
        try:
            if self._conn is None:
                self._conn = sqlite3.connect(self.db_path)
                self._conn.row_factory = sqlite3.Row
                self._conn.execute("PRAGMA busy_timeout = 5000")
                self._conn.execute("PRAGMA journal_mode = DELETE")
                self._conn.execute("PRAGMA foreign_keys = ON")
            return self._conn
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}", exc_info=True)
            raise
    
    def close_connection(self):
        """بستن اتصال دیتابیس"""
        try:
            if self._conn:
                self._conn.close()
                self._conn = None
                logger.info("Database connection closed")
        except sqlite3.Error as e:
            logger.warning(f"Error closing database connection: {e}")
    
    def get_cursor(self):
        """دریافت cursor از اتصال"""
        conn = self.get_connection()
        return conn.cursor()
    
    def _ensure_directory(self):
        """اطمینان از وجود پوشه دیتابیس"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _seed_database_if_needed(self):
        """کپی دیتابیس seed از bundle (فقط اولین بار)"""
        try:
            if os.path.exists(self.db_path) and os.path.getsize(self.db_path) > 0:
                logger.info(f"✅ Database exists: {self.db_path}")
                return
            
            if getattr(sys, 'frozen', False):
                seed_path = Path(sys._MEIPASS) / "data" / "IO_List_Generator.db"
            else:
                seed_path = Path(__file__).parent.parent / "data" / "IO_List_Generator.db"
            
            if seed_path.exists():
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
                shutil.copy2(str(seed_path), self.db_path)
                logger.info(f"✅ Seeded database from bundle: {seed_path}")
            else:
                logger.warning(f"⚠️ Seed database not found: {seed_path}")
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
                self._create_all_tables()
                logger.info(f"✅ Created empty database: {self.db_path}")
        
        except Exception as e:
            logger.error(f"❌ Seed failed: {e}", exc_info=True)
    
    # ============================================================
    # ✅ BACKUP با sqlite3.backup() — Atomic
    # ============================================================
    
    @staticmethod
    def _backup_database_atomic(source_db: str, backup_path: str) -> bool:
        """Backup اتمیک با sqlite3.Connection.backup()"""
        try:
            backup_dir = os.path.dirname(backup_path)
            if backup_dir and not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)
            
            src = sqlite3.connect(source_db)
            dst = sqlite3.connect(backup_path)
            
            try:
                with dst:
                    src.backup(dst)
                logger.info(f"✅ Atomic backup created: {backup_path}")
                return True
            finally:
                src.close()
                dst.close()
        
        except Exception as e:
            logger.error(f"❌ Atomic backup failed: {e}", exc_info=True)
            return False
    
    def _create_auto_backup(self, min_interval_hours: int = 4):
        """ایجاد بک‌آپ خودکار از دیتابیس در زمان اجرا"""
        try:
            backup_dir = Path(self.db_path).parent / "Backups"
            backup_dir = str(backup_dir.resolve())
            
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)

            # ============================================================
            # ✅ چک: آخرین بکاپ چقدر قبل بوده؟
            # ============================================================
            existing = sorted(
                Path(backup_dir).glob("IO_List_Generator_Backup_*.db"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            if existing:
                last_mtime = datetime.fromtimestamp(existing[0].stat().st_mtime)
                elapsed = datetime.now() - last_mtime
                if elapsed.total_seconds() < min_interval_hours * 3600:
                    logger.info(
                        f"⏭️ Skipping auto-backup "
                        f"(last one was {elapsed.total_seconds()/3600:.1f}h ago)"
                    )
                    return None
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"IO_List_Generator_Backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            if os.path.exists(self.db_path):
                self.close_connection()
                
                success = self._backup_database_atomic(self.db_path, backup_path)
                
                if success:
                    self._cleanup_old_backups(backup_dir, keep_count=30)
                    logger.info(f"✅ Auto-backup created: {backup_path}")
                    return backup_path
                else:
                    logger.warning("⚠️ Atomic backup failed, trying shutil fallback")
                    shutil.copy2(self.db_path, backup_path)
                    self._cleanup_old_backups(backup_dir, keep_count=30)
                    return backup_path
            else:
                logger.warning("⚠️ Database file not found for backup")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating auto-backup: {e}")
            return None
    
    def _cleanup_old_backups(self, backup_dir: str, keep_count: int = 30):
        """حذف بک‌آپ‌های قدیمی"""
        try:
            backup_files = []
            for filename in os.listdir(backup_dir):
                if filename.startswith('IO_List_Generator_Backup_') and filename.endswith('.db'):
                    filepath = os.path.join(backup_dir, filename)
                    backup_files.append((filepath, os.path.getctime(filepath)))
            
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            if len(backup_files) > keep_count:
                for filepath, _ in backup_files[keep_count:]:
                    try:
                        os.remove(filepath)
                        logger.info(f"🗑️ Removed old backup: {os.path.basename(filepath)}")
                    except Exception as e:
                        logger.warning(f"Could not remove old backup {filepath}: {e}")
                        
        except Exception as e:
            logger.warning(f"Error cleaning old backups: {e}")
    
    def get_backup_path(self) -> str:
        """دریافت مسیر پوشه بک‌آپ"""
        backup_dir = Path(self.db_path).parent / "Backups"
        return str(backup_dir.resolve())
    
    def get_backup_files(self) -> List[Dict[str, Any]]:
        """دریافت لیست فایل‌های بک‌آپ موجود"""
        backup_dir = self.get_backup_path()
        backups = []
        
        if os.path.exists(backup_dir):
            for filename in os.listdir(backup_dir):
                if filename.startswith('IO_List_Generator_Backup_') and filename.endswith('.db'):
                    filepath = os.path.join(backup_dir, filename)
                    size = os.path.getsize(filepath)
                    modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                    backups.append({
                        'filename': filename,
                        'path': filepath,
                        'size': size,
                        'size_mb': round(size / (1024 * 1024), 2),
                        'modified': modified,
                        'modified_str': modified.strftime('%Y/%m/%d %H:%M:%S')
                    })
        
        backups.sort(key=lambda x: x['modified'], reverse=True)
        return backups
    
    # ==================== متدهای دیتابیس ====================
    
    def _init_db(self):
        """ایجاد یا به‌روزرسانی جداول دیتابیس"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                # ============================================================
                # ✅ نصب اول — هیچ بکاپی لازم نیست
                # ============================================================
                logger.info("🆕 Fresh database — creating all tables...")
                self._create_all_tables(cursor)
                self._ensure_schema_version_table(cursor)
                self._record_schema_version(
                    cursor, CURRENT_SCHEMA_VERSION,
                    "Initial schema with ON UPDATE CASCADE"
                )
                conn.commit()
                return
            
            # ============================================================
            # ✅ دیتابیس موجود — اول نسخه را چک کن
            # ============================================================
            self._ensure_schema_version_table(cursor)
            current_version = self._get_current_schema_version()
            
            # اگر از قبل up-to-date است → هیچ کاری نکن
            if current_version >= CURRENT_SCHEMA_VERSION:
                logger.info(f"✅ Schema is up-to-date (v{current_version}), no migration needed")
                conn.commit()
                return
            
            # ============================================================
            # ✅ فقط الان Migration لازم است → بکاپ بگیر
            # ============================================================
            logger.info(
                f"🔄 Migration required: v{current_version} → v{CURRENT_SCHEMA_VERSION}"
            )
            
            pre_migration_backup = self._create_pre_migration_backup()
            if pre_migration_backup:
                logger.info(f"✅ Pre-migration backup: {pre_migration_backup}")
            else:
                logger.warning("⚠️ Could not create pre-migration backup, proceeding anyway...")
            
            # Migration ساختاری (ستون‌های گمشده و ...)
            self._migrate_database(cursor)
            
            # Migration نسخه‌ای
            self._check_and_apply_migrations(cursor)
            
            conn.commit()
            
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def _create_pre_migration_backup(self) -> Optional[str]:
        """✅ ساخت Backup قبل از Migration"""
        try:
            if not os.path.exists(self.db_path):
                return None
            
            backup_dir = Path(self.db_path).parent / "Backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"pre_migration_{timestamp}.db"
            backup_path = str(backup_dir / backup_filename)
            
            success = self._backup_database_atomic(self.db_path, backup_path)
            
            if success:
                logger.info(f"✅ Pre-migration backup created: {backup_path}")
                return backup_path
            else:
                shutil.copy2(self.db_path, backup_path)
                logger.info(f"✅ Pre-migration backup (fallback): {backup_path}")
                return backup_path
        
        except Exception as e:
            logger.error(f"❌ Pre-migration backup failed: {e}", exc_info=True)
            return None
    
    # ============================================================
    # ✅ SCHEMA VERSIONING
    # ============================================================
    
    def _ensure_schema_version_table(self, cursor):
        """ایجاد جدول schema_migrations"""
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL,
                    description TEXT
                )
            ''')
            logger.debug("✅ schema_migrations table ensured")
        except sqlite3.Error as e:
            logger.warning(f"⚠️ Could not create schema_migrations table: {e}")
    
    def _get_current_schema_version(self) -> int:
        """خواندن نسخه فعلی Schema"""
        try:
            cursor = self.get_cursor()
            cursor.execute('SELECT MAX(version) FROM schema_migrations')
            row = cursor.fetchone()
            return row[0] if row and row[0] else 0
        except sqlite3.Error:
            return 0
    
    def _record_schema_version(self, cursor, version: int, description: str = ""):
        """ثبت نسخه Schema"""
        try:
            now = datetime.now().isoformat()
            cursor.execute('''
                INSERT OR IGNORE INTO schema_migrations (version, applied_at, description)
                VALUES (?, ?, ?)
            ''', (version, now, description))
            logger.info(f"✅ Schema version recorded: v{version} ({description})")
        except sqlite3.Error as e:
            logger.warning(f"⚠️ Could not record schema version: {e}")
    
    def _check_and_apply_migrations(self, cursor):
        """
        بررسی و اعمال Migration های جدید
        
        v0 → v1: ساختار پایه
        v1 → v2: اضافه کردن ON UPDATE CASCADE
        """
        try:
            self._ensure_schema_version_table(cursor)
            
            current_version = self._get_current_schema_version()
            logger.info(f"📊 Current schema version: v{current_version}, target: v{CURRENT_SCHEMA_VERSION}")
            
            if current_version >= CURRENT_SCHEMA_VERSION:
                logger.info("✅ Schema is up-to-date")
                return
            
            # ============================================================
            # Migration v0 → v1 (ساختار پایه)
            # ============================================================
            if current_version < 1:
                logger.info("🔄 Applying migration v0 → v1...")
                self._record_schema_version(
                    cursor, 1,
                    "Initial schema with revisions, valves, attachments"
                )
            
            # ============================================================
            # Migration v1 → v2 (ON UPDATE CASCADE)
            # ============================================================
            if current_version < 2:
                logger.info("🔄 Applying migration v1 → v2...")
                logger.info("   Adding ON UPDATE CASCADE to all project FKs")
                
                self._migrate_to_update_cascade(cursor)
                
                self._record_schema_version(
                    cursor, 2,
                    "Added ON UPDATE CASCADE to all project FKs"
                )
        
        except sqlite3.Error as e:
            logger.error(f"❌ Migration check failed: {e}", exc_info=True)
            raise
    
    # ============================================================
    # ✅ MIGRATION v1 → v2: ON UPDATE CASCADE
    # ============================================================
    
    def _table_has_update_cascade(self, cursor, table_name: str) -> bool:
        """
        بررسی آیا جدول ON UPDATE CASCADE دارد
        
        Returns:
            True اگر FK با on_update='CASCADE' وجود داشته باشد
        """
        try:
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            fks = cursor.fetchall()
            
            # FK structure: (id, seq, table, from, to, on_update, on_delete, match)
            for fk in fks:
                on_update = fk[5]
                if on_update == 'CASCADE':
                    return True
            
            return False
        except sqlite3.Error:
            return False
    
    def _migrate_to_update_cascade(self, cursor):
        """
        Migration: اضافه کردن ON UPDATE CASCADE به Foreign Keys
        
        روش:
        1. ساخت جدول جدید با ON UPDATE CASCADE
        2. کپی داده‌ها
        3. حذف جدول قدیمی
        4. Rename جدول جدید
        
        ⚠️ این Migration فقط برای جداول زیر:
        - revisions, sections, devices, valves, attachments, component_labels
        """
        logger.info("🔄 Migrating Foreign Keys to ON UPDATE CASCADE...")
        
        # ============================================================
        # تعریف SQL برای هر جدول
        # ============================================================
        table_schemas = {
            'revisions': '''
                CREATE TABLE revisions_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    revision_name TEXT NOT NULL,
                    is_current INTEGER DEFAULT 0,
                    description TEXT DEFAULT '',
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY(project_name) REFERENCES projects(name) 
                        ON UPDATE CASCADE ON DELETE CASCADE,
                    UNIQUE(project_name, revision_name)
                )
            ''',
            'sections': '''
                CREATE TABLE sections_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT,
                    revision_name TEXT DEFAULT 'Rev-0',
                    section_name TEXT,
                    description TEXT,
                    order_index INTEGER,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY(project_name) REFERENCES projects(name) 
                        ON UPDATE CASCADE ON DELETE CASCADE
                )
            ''',
            'devices': '''
                CREATE TABLE devices_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT,
                    revision_name TEXT DEFAULT 'Rev-0',
                    section_name TEXT,
                    motor_data TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY(project_name) REFERENCES projects(name) 
                        ON UPDATE CASCADE ON DELETE CASCADE
                )
            ''',
            'valves': '''
                CREATE TABLE valves_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT,
                    revision_name TEXT DEFAULT 'Rev-0',
                    section_name TEXT,
                    valve_data TEXT,
                    order_index INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY(project_name) REFERENCES projects(name) 
                        ON UPDATE CASCADE ON DELETE CASCADE
                )
            ''',
            'attachments': '''
                CREATE TABLE attachments_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    file_type TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    added_at TEXT,
                    FOREIGN KEY(project_name) REFERENCES projects(name) 
                        ON UPDATE CASCADE ON DELETE CASCADE,
                    UNIQUE(project_name, file_name)
                )
            ''',
            'component_labels': '''
                CREATE TABLE component_labels_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    component_key TEXT NOT NULL,
                    persian_label TEXT NOT NULL,
                    english_label TEXT NOT NULL,
                    FOREIGN KEY(project_name) REFERENCES projects(name) 
                        ON UPDATE CASCADE ON DELETE CASCADE,
                    UNIQUE(project_name, component_key)
                )
            ''',
        }
        
        # ============================================================
        # Migration برای هر جدول
        # ============================================================
        for table_name, create_sql in table_schemas.items():
            try:
                # ============================================================
                # چک: آیا جدول وجود دارد؟
                # ============================================================
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,)
                )
                if not cursor.fetchone():
                    logger.debug(f"ℹ️ Table {table_name} does not exist, skipping")
                    continue
                
                # ============================================================
                # چک: آیا ON UPDATE CASCADE دارد؟
                # ============================================================
                if self._table_has_update_cascade(cursor, table_name):
                    logger.debug(f"✅ {table_name} already has ON UPDATE CASCADE")
                    continue
                
                # ============================================================
                # Migration: rebuild جدول
                # ============================================================
                logger.info(f"🔄 Rebuilding {table_name} with ON UPDATE CASCADE...")
                
                # ۱. حذف جدول موقت اگر از قبل مانده
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}_new")
                
                # ۲. ساخت جدول جدید
                cursor.execute(create_sql)
                
                # ۳. کپی داده‌ها
                cursor.execute(f"INSERT INTO {table_name}_new SELECT * FROM {table_name}")
                rows_copied = cursor.rowcount
                
                # ۴. حذف جدول قدیمی
                cursor.execute(f"DROP TABLE {table_name}")
                
                # ۵. Rename جدول جدید
                cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")
                
                # ۶. بازسازی Index ها (اگر لازم باشد)
                if table_name == 'revisions':
                    cursor.execute('''
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_revisions_current
                        ON revisions(project_name)
                        WHERE is_current = 1
                    ''')
                
                logger.info(
                    f"✅ {table_name} rebuilt with ON UPDATE CASCADE "
                    f"({rows_copied} rows copied)"
                )
            
            except sqlite3.Error as e:
                logger.error(f"❌ Failed to migrate {table_name}: {e}")
                raise
        
        logger.info("🎉 ON UPDATE CASCADE migration completed")
    
    # ============================================================
    # ✅ MIGRATION ساختاری (v0 → v1)
    # ============================================================
    
    def _migrate_database(self, cursor):
        """به‌روزرسانی دیتابیس موجود با ستون‌های جدید"""
        try:
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # ============================================================
            # 0. description در projects
            # ============================================================
            cursor.execute("PRAGMA table_info(projects)")
            project_cols = [col[1] for col in cursor.fetchall()]
            
            if 'description' not in project_cols:
                logger.info("🔄 Adding 'description' column to projects...")
                cursor.execute(
                    "ALTER TABLE projects ADD COLUMN description TEXT DEFAULT ''"
                )
                logger.info("✅ 'description' column added to projects")
            
            # ============================================================
            # 1. component_labels migration
            # ============================================================
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='component_labels'")
            if cursor.fetchone():
                cursor.execute("PRAGMA table_info(component_labels)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'project_name' not in columns:
                    cursor.execute("ALTER TABLE component_labels RENAME TO component_labels_old")
                    
                    cursor.execute('''
                        CREATE TABLE component_labels (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            project_name TEXT NOT NULL,
                            component_key TEXT NOT NULL,
                            persian_label TEXT NOT NULL,
                            english_label TEXT NOT NULL,
                            FOREIGN KEY(project_name) REFERENCES projects(name) 
                                ON UPDATE CASCADE ON DELETE CASCADE,
                            UNIQUE(project_name, component_key)
                        )
                    ''')
                    
                    cursor.execute('''
                        INSERT INTO component_labels (project_name, component_key, persian_label, english_label)
                        SELECT 'Default', component_key, persian_label, english_label
                        FROM component_labels_old
                    ''')
                    
                    cursor.execute("DROP TABLE component_labels_old")
                    logger.info("✅ Migrated component_labels table")
            
            # ============================================================
            # 2. ایجاد جداول جدید
            # ============================================================
            self._create_all_tables(cursor)
            
            # ============================================================
            # 3. revision_name در sections
            # ============================================================
            cursor.execute("PRAGMA table_info(sections)")
            section_cols = [col[1] for col in cursor.fetchall()]
            
            if 'revision_name' not in section_cols:
                logger.info("🔄 Adding revision_name column to sections...")
                cursor.execute(
                    "ALTER TABLE sections ADD COLUMN revision_name TEXT DEFAULT 'Rev-0'"
                )
                logger.info("✅ revision_name added to sections")
            
            # ============================================================
            # 4. revision_name در devices
            # ============================================================
            cursor.execute("PRAGMA table_info(devices)")
            device_cols = [col[1] for col in cursor.fetchall()]
            
            if 'revision_name' not in device_cols:
                logger.info("🔄 Adding revision_name column to devices...")
                cursor.execute(
                    "ALTER TABLE devices ADD COLUMN revision_name TEXT DEFAULT 'Rev-0'"
                )
                logger.info("✅ revision_name added to devices")
            
            # ============================================================
            # 5. Migrate Revisions
            # ============================================================
            self._migrate_revisions(cursor)
            
            # ============================================================
            # 6-10. جداول دیگر در _create_all_tables ساخته می‌شوند
            # ============================================================
            
            # ============================================================
            # order_index در valves
            # ============================================================
            cursor.execute("PRAGMA table_info(valves)")
            valve_cols = [col[1] for col in cursor.fetchall()]
            
            if 'order_index' not in valve_cols:
                logger.info("🔄 Adding order_index column to valves...")
                cursor.execute(
                    "ALTER TABLE valves ADD COLUMN order_index INTEGER DEFAULT 0"
                )
                logger.info("✅ order_index added to valves")
            
            logger.info("🎉 Structural migration completed successfully")
        
        except sqlite3.Error as e:
            logger.warning(f"⚠️ Migration warning: {e}")
            raise
    
    def _migrate_revisions(self, cursor):
        """ایجاد Rev-0 برای همه پروژه‌های موجود"""
        try:
            cursor.execute("SELECT name FROM projects")
            projects = cursor.fetchall()
            
            if not projects:
                return
            
            now = datetime.now().isoformat()
            migrated_count = 0
            
            for row in projects:
                project_name = row[0]
                
                cursor.execute(
                    "SELECT COUNT(*) FROM revisions WHERE project_name = ?",
                    (project_name,)
                )
                count = cursor.fetchone()[0]
                
                if count == 0:
                    cursor.execute('''
                        INSERT INTO revisions 
                        (project_name, revision_name, is_current, description, created_at, updated_at)
                        VALUES (?, 'Rev-0', 1, 'Initial revision (migrated)', ?, ?)
                    ''', (project_name, now, now))
                    
                    migrated_count += 1
                    logger.info(f"✅ Created Rev-0 for project: {project_name}")
            
            if migrated_count > 0:
                logger.info(f"✅ Migration: {migrated_count} project(s) received Rev-0")
            
        except sqlite3.Error as e:
            logger.error(f"Error migrating revisions: {e}")
            raise
    
    # ============================================================
    # ✅ CREATE ALL TABLES — با ON UPDATE CASCADE
    # ============================================================
    
    def _create_all_tables(self, cursor):
        """ایجاد تمام جداول با ON UPDATE CASCADE"""
        
        # ============================================================
        # projects
        # ============================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                name TEXT PRIMARY KEY,
                description TEXT DEFAULT '',
                client_name TEXT,
                client_phone TEXT,
                client_address TEXT,
                consultant_name TEXT,
                consultant_phone TEXT,
                consultant_address TEXT,
                contractor_name TEXT,
                contractor_phone TEXT,
                contractor_address TEXT,
                designer_name TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # ============================================================
        # revisions — ✅ ON UPDATE CASCADE
        # ============================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS revisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                revision_name TEXT NOT NULL,
                is_current INTEGER DEFAULT 0,
                description TEXT DEFAULT '',
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY(project_name) REFERENCES projects(name) 
                    ON UPDATE CASCADE ON DELETE CASCADE,
                UNIQUE(project_name, revision_name)
            )
        ''')
        
        # ============================================================
        # ✅ Unique Partial Index — Current Revision
        # ============================================================
        try:
            cursor.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_revisions_current
                ON revisions(project_name)
                WHERE is_current = 1
            ''')
            logger.info("✅ Unique partial index on current revision ensured")
        except sqlite3.Error as e:
            logger.warning(f"⚠️ Could not create unique index: {e}")
        
        # ============================================================
        # sections — ✅ ON UPDATE CASCADE
        # ============================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT,
                revision_name TEXT DEFAULT 'Rev-0',
                section_name TEXT,
                description TEXT,
                order_index INTEGER,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY(project_name) REFERENCES projects(name) 
                    ON UPDATE CASCADE ON DELETE CASCADE
            )
        ''')
        
        # ============================================================
        # devices — ✅ ON UPDATE CASCADE
        # ============================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT,
                revision_name TEXT DEFAULT 'Rev-0',
                section_name TEXT,
                motor_data TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY(project_name) REFERENCES projects(name) 
                    ON UPDATE CASCADE ON DELETE CASCADE
            )
        ''')
        
        # ============================================================
        # valves — ✅ ON UPDATE CASCADE
        # ============================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS valves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT,
                revision_name TEXT DEFAULT 'Rev-0',
                section_name TEXT,
                valve_data TEXT,
                order_index INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY(project_name) REFERENCES projects(name) 
                    ON UPDATE CASCADE ON DELETE CASCADE
            )
        ''')
        logger.info("✅ valves table ensured")
        
        # ============================================================
        # component_labels — ✅ ON UPDATE CASCADE
        # ============================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS component_labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                component_key TEXT NOT NULL,
                persian_label TEXT NOT NULL,
                english_label TEXT NOT NULL,
                FOREIGN KEY(project_name) REFERENCES projects(name) 
                    ON UPDATE CASCADE ON DELETE CASCADE,
                UNIQUE(project_name, component_key)
            )
        ''')
        
        # ============================================================
        # templates
        # ============================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                source_project TEXT,
                source_section TEXT,
                devices TEXT NOT NULL,
                device_count INTEGER DEFAULT 0,
                total_io INTEGER DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                last_used TEXT,
                created_at TEXT,
                updated_at TEXT,
                created_by TEXT DEFAULT 'user',
                category TEXT DEFAULT 'Custom'
            )
        ''')
        
        # ============================================================
        # custom_components
        # ============================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                label_fa TEXT NOT NULL,
                label_en TEXT NOT NULL,
                di INTEGER DEFAULT 0,
                do INTEGER DEFAULT 0,
                ai INTEGER DEFAULT 0,
                ao INTEGER DEFAULT 0,
                cable_size TEXT DEFAULT '2x1mm²',
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # ============================================================
        # attachments — ✅ ON UPDATE CASCADE
        # ============================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                file_type TEXT DEFAULT '',
                description TEXT DEFAULT '',
                added_at TEXT,
                FOREIGN KEY(project_name) REFERENCES projects(name) 
                    ON UPDATE CASCADE ON DELETE CASCADE,
                UNIQUE(project_name, file_name)
            )
        ''')
        
        # ============================================================
        # app_state
        # ============================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ============================================================
        # learning_smart_tags
        # ============================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_smart_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                revision_name TEXT DEFAULT 'Rev-0',
                tag TEXT NOT NULL,
                components TEXT,
                usage_count INTEGER DEFAULT 1,
                last_used TEXT,
                created_at TEXT,
                updated_at TEXT,
                UNIQUE(project_name, revision_name, tag)
            )
        ''')
        
        # ============================================================
        # learning_models
        # ============================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                pattern_signature TEXT NOT NULL,
                components TEXT NOT NULL,
                usage_count INTEGER DEFAULT 1,
                sample_devices TEXT,
                created_at TEXT,
                updated_at TEXT,
                UNIQUE(model_name, pattern_signature)
            )
        ''')
        
        logger.info("All tables created/verified successfully")
    
    # ============================================================
    # ✅ BACKUP / RESTORE
    # ============================================================
    
    def backup_database(self, backup_path: str) -> bool:
        """ایجاد پشتیبان اتمیک"""
        try:
            self.close_connection()
            
            success = self._backup_database_atomic(self.db_path, backup_path)
            
            if success:
                logger.info(f"✅ Database backed up to: {backup_path}")
                return True
            else:
                logger.warning("⚠️ Atomic backup failed, using shutil fallback")
                shutil.copy2(self.db_path, backup_path)
                logger.info(f"✅ Database backed up (fallback): {backup_path}")
                return True
        
        except Exception as e:
            logger.error(f"❌ Error backing up database: {e}", exc_info=True)
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """بازگردانی دیتابیس از پشتیبان — اتمیک"""
        temp_path = None
        
        try:
            if not os.path.exists(backup_path):
                logger.error(f"❌ Backup file not found: {backup_path}")
                return False
            
            try:
                test_conn = sqlite3.connect(backup_path)
                test_cursor = test_conn.cursor()
                test_cursor.execute("PRAGMA integrity_check")
                result = test_cursor.fetchone()
                test_conn.close()
                
                if result and result[0] != 'ok':
                    logger.error(f"❌ Backup integrity check failed: {result[0]}")
                    return False
                
                logger.info("✅ Backup integrity check passed")
            except sqlite3.Error as e:
                logger.error(f"❌ Backup is not a valid SQLite file: {e}")
                return False
            
            self.close_connection()
            
            # Safety backup
            if os.path.exists(self.db_path):
                try:
                    backup_dir = Path(self.db_path).parent / "Backups"
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    safety_backup = str(backup_dir / f"pre_restore_{timestamp}.db")
                    shutil.copy2(self.db_path, safety_backup)
                    logger.info(f"✅ Safety backup before restore: {safety_backup}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not create safety backup: {e}")
            
            # Copy to temp
            db_dir = os.path.dirname(self.db_path)
            fd, temp_path = tempfile.mkstemp(
                suffix='.db',
                prefix='restore_',
                dir=db_dir if db_dir else None
            )
            os.close(fd)
            
            shutil.copy2(backup_path, temp_path)
            logger.info(f"✅ Backup copied to temp: {temp_path}")
            
            # Atomic replace
            os.replace(temp_path, self.db_path)
            temp_path = None
            logger.info(f"✅ Database replaced atomically: {self.db_path}")
            
            # Reopen
            self.get_connection()
            
            logger.info(f"✅ Database restored successfully from: {backup_path}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error restoring database: {e}", exc_info=True)
            return False
        
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
    
    # ============================================================
    # ✅ SAVE PROJECT
    # ============================================================
    
    def save_project(self, project: Project):
        """ذخیره کامل پروژه"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute("SELECT COUNT(*) FROM projects WHERE name = ?", (project.name,))
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                cursor.execute('''
                    UPDATE projects SET
                        description = ?, client_name = ?, client_phone = ?,
                        client_address = ?, consultant_name = ?, consultant_phone = ?,
                        consultant_address = ?, contractor_name = ?, contractor_phone = ?,
                        contractor_address = ?, designer_name = ?, updated_at = ?
                    WHERE name = ?
                ''', (
                    project.description or "", project.client_name or "",
                    project.client_phone or "", project.client_address or "",
                    project.consultant_name or "", project.consultant_phone or "",
                    project.consultant_address or "", project.contractor_name or "",
                    project.contractor_phone or "", project.contractor_address or "",
                    project.designer_name or "", now, project.name
                ))
            else:
                cursor.execute('''
                    INSERT INTO projects (
                        name, description, client_name, client_phone, client_address,
                        consultant_name, consultant_phone, consultant_address,
                        contractor_name, contractor_phone, contractor_address,
                        designer_name, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    project.name, project.description or "",
                    project.client_name or "", project.client_phone or "",
                    project.client_address or "", project.consultant_name or "",
                    project.consultant_phone or "", project.consultant_address or "",
                    project.contractor_name or "", project.contractor_phone or "",
                    project.contractor_address or "", project.designer_name or "",
                    getattr(project, 'created_at', datetime.now()).isoformat()
                        if isinstance(getattr(project, 'created_at', None), datetime)
                        else str(getattr(project, 'created_at', now)),
                    now
                ))
            
            cursor.execute("DELETE FROM devices WHERE project_name = ?", (project.name,))
            cursor.execute("DELETE FROM valves WHERE project_name = ?", (project.name,))
            cursor.execute("DELETE FROM sections WHERE project_name = ?", (project.name,))
            cursor.execute("DELETE FROM revisions WHERE project_name = ?", (project.name,))
            
            for revision in project.revisions:
                is_current = 1 if revision.name == project.current_revision_name else 0
                
                cursor.execute('''
                    INSERT INTO revisions (
                        project_name, revision_name, is_current,
                        description, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    project.name, revision.name, is_current,
                    revision.description or "",
                    getattr(revision, 'created_at', datetime.now()).isoformat()
                        if isinstance(getattr(revision, 'created_at', None), datetime)
                        else str(getattr(revision, 'created_at', now)),
                    now
                ))
                
                for section in revision.sections:
                    cursor.execute('''
                        INSERT INTO sections (
                            project_name, revision_name, section_name,
                            description, order_index, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        project.name, revision.name, section.name,
                        section.description or "", section.order_index,
                        getattr(section, 'created_at', datetime.now()).isoformat()
                            if isinstance(getattr(section, 'created_at', None), datetime)
                            else str(getattr(section, 'created_at', now)),
                        now
                    ))
                    
                    for motor in section.devices:
                        cursor.execute('''
                            INSERT INTO devices (
                                project_name, revision_name, section_name,
                                motor_data, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            project.name, revision.name, section.name,
                            json.dumps(motor.to_dict(), ensure_ascii=False),
                            getattr(motor, 'created_at', datetime.now()).isoformat()
                                if isinstance(getattr(motor, 'created_at', None), datetime)
                                else str(getattr(motor, 'created_at', now)),
                            now
                        ))
                    
                    if hasattr(section, 'valves') and section.valves:
                        for valve_index, valve in enumerate(section.valves):
                            cursor.execute('''
                                INSERT INTO valves (
                                    project_name, revision_name, section_name,
                                    valve_data, order_index, created_at, updated_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                project.name, revision.name, section.name,
                                json.dumps(valve.to_dict(), ensure_ascii=False),
                                valve_index, now, now
                            ))
            
            conn.commit()
            logger.info(f"Project '{project.name}' saved successfully "
                    f"({len(project.revisions)} revision(s))")
            
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Error saving project '{project.name}': {e}")
            raise
    
    def save_project_info(self, project: Project) -> bool:
        """ذخیره فقط اطلاعات پایه پروژه"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute('''
                UPDATE projects SET
                    description = ?, client_name = ?, client_phone = ?,
                    client_address = ?, consultant_name = ?, consultant_phone = ?,
                    consultant_address = ?, contractor_name = ?, contractor_phone = ?,
                    contractor_address = ?, designer_name = ?, updated_at = ?
                WHERE name = ?
            ''', (
                project.description or "", project.client_name or "",
                project.client_phone or "", project.client_address or "",
                project.consultant_name or "", project.consultant_phone or "",
                project.consultant_address or "", project.contractor_name or "",
                project.contractor_phone or "", project.contractor_address or "",
                project.designer_name or "", now, project.name
            ))
            
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO projects (
                        name, description, client_name, client_phone, client_address,
                        consultant_name, consultant_phone, consultant_address,
                        contractor_name, contractor_phone, contractor_address,
                        designer_name, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    project.name, project.description or "",
                    project.client_name or "", project.client_phone or "",
                    project.client_address or "", project.consultant_name or "",
                    project.consultant_phone or "", project.consultant_address or "",
                    project.contractor_name or "", project.contractor_phone or "",
                    project.contractor_address or "", project.designer_name or "",
                    now, now
                ))
            
            conn.commit()
            logger.info(f"✅ Project info saved: '{project.name}' (revisions untouched)")
            return True
        
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Error saving project info '{project.name}': {e}", exc_info=True)
            raise
    
    # ============================================================
    # ✅ RENAME PROJECT — با ON UPDATE CASCADE
    # ============================================================
    
    def rename_project(self, old_name: str, new_name: str) -> bool:
        """
        تغییر نام پروژه — بسیار ساده با ON UPDATE CASCADE
        
        SQLite خودش تمام جداول فرزند را با ON UPDATE CASCADE
        به‌روزرسانی می‌کند:
        - revisions, sections, devices, valves
        - attachments, component_labels
        
        فقط نیاز است:
        1. projects UPDATE شود
        2. app_state (چون FK نیست) دستی UPDATE شود
        3. learning_* (چون FK نیستند) دستی UPDATE شوند
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # ============================================================
            # ۱. UPDATE projects — SQLite خودش CASCADE می‌کند
            # ============================================================
            cursor.execute(
                "UPDATE projects SET name = ?, updated_at = ? WHERE name = ?",
                (new_name, datetime.now().isoformat(), old_name)
            )
            
            if cursor.rowcount == 0:
                logger.warning(f"⚠️ Project '{old_name}' not found")
                return False
            
            logger.debug(f"✅ projects updated ({cursor.rowcount} rows)")
            
            # ============================================================
            # ۲. app_state — چون FK ندارد، دستی UPDATE می‌کنیم
            # ============================================================
            try:
                cursor.execute('''
                    UPDATE app_state
                    SET value = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE key = 'last_active_project' AND value = ?
                ''', (new_name, old_name))
                
                if cursor.rowcount > 0:
                    logger.info(
                        f"✅ app_state updated: last_active_project → '{new_name}'"
                    )
            except Exception as e:
                logger.debug(f"⚠️ app_state skipped: {e}")
            
            # ============================================================
            # ۳. learning_* — چون FK ندارند، دستی UPDATE می‌کنیم
            # ============================================================
            learning_tables = [
                'learning_patterns',
                'learning_project_analysis',
                'learning_smart_tags',
            ]
            
            for table in learning_tables:
                try:
                    cursor.execute(
                        f"UPDATE {table} SET project_name = ? WHERE project_name = ?",
                        (new_name, old_name)
                    )
                    if cursor.rowcount > 0:
                        logger.debug(f"✅ {table} updated ({cursor.rowcount} rows)")
                except Exception as e:
                    logger.debug(f"⚠️ {table} skipped: {e}")
            
            # ============================================================
            # ۴. Commit
            # ============================================================
            conn.commit()
            
            logger.info(f"✅ Project renamed: '{old_name}' → '{new_name}'")
            return True
        
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                    logger.warning("Rollback performed for rename_project")
                except Exception:
                    pass
            logger.error(f"rename_project failed: {e}", exc_info=True)
            raise
    
    # ============================================================
    # ✅ LOAD PROJECTS
    # ============================================================
    
    def load_all_projects(self) -> Dict[str, Project]:
        """بارگذاری تمام پروژه‌ها از دیتابیس"""
        projects = {}
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(projects)")
            columns = [col[1] for col in cursor.fetchall()]
            has_description = 'description' in columns
            
            cursor.execute("""
                SELECT name, client_name, client_phone, client_address,
                    consultant_name, consultant_phone, consultant_address,
                    contractor_name, contractor_phone, contractor_address,
                    designer_name, created_at, updated_at, description
                FROM projects
            """)
            
            for row in cursor.fetchall():
                project = Project(name=row[0])
                project.client_name = row[1] or ""
                project.client_phone = row[2] or ""
                project.client_address = row[3] or ""
                project.consultant_name = row[4] or ""
                project.consultant_phone = row[5] or ""
                project.consultant_address = row[6] or ""
                project.contractor_name = row[7] or ""
                project.contractor_phone = row[8] or ""
                project.contractor_address = row[9] or ""
                project.designer_name = row[10] or ""
                
                if row[11]:
                    try:
                        project.created_at = datetime.fromisoformat(row[11])
                    except:
                        pass
                if row[12]:
                    try:
                        project.updated_at = datetime.fromisoformat(row[12])
                    except:
                        pass
                
                if has_description:
                    project.description = row[13] or ""
                else:
                    project.description = ""
                
                projects[project.name] = project
            
            cursor.execute('''
                SELECT project_name, revision_name, is_current, description,
                    created_at, updated_at
                FROM revisions
                ORDER BY project_name, revision_name
            ''')
            
            for row in cursor.fetchall():
                proj_name = row[0]
                if proj_name not in projects:
                    continue
                
                project = projects[proj_name]
                revision = Revision(name=row[1], project_name=proj_name)
                revision.description = row[3] or ""
                
                if row[4]:
                    try:
                        revision.created_at = datetime.fromisoformat(row[4])
                    except:
                        pass
                if row[5]:
                    try:
                        revision.updated_at = datetime.fromisoformat(row[5])
                    except:
                        pass
                
                project.revisions.append(revision)
                
                if row[2] == 1:
                    project.current_revision_name = revision.name
            
            for project in projects.values():
                if not project.revisions:
                    logger.warning(f"⚠️ Project '{project.name}' has no revisions, creating Rev-0")
                    rev = Revision(name='Rev-0', project_name=project.name)
                    project.revisions.append(rev)
                    project.current_revision_name = 'Rev-0'
                elif not project.current_revision_name:
                    project.current_revision_name = project.revisions[0].name
            
            cursor.execute('''
                SELECT project_name, revision_name, section_name, description,
                    order_index, created_at, updated_at
                FROM sections
                ORDER BY order_index
            ''')
            
            for row in cursor.fetchall():
                proj_name = row[0]
                rev_name = row[1] or 'Rev-0'
                sec_name = row[2]
                
                if proj_name not in projects:
                    continue
                
                project = projects[proj_name]
                revision = project.get_revision_by_name(rev_name)
                
                if not revision:
                    logger.warning(f"⚠️ Revision '{rev_name}' not found in '{proj_name}', skipping section '{sec_name}'")
                    continue
                
                section = ProjectSection(sec_name, row[3] or "")
                section.order_index = row[4] or 0
                
                if row[5]:
                    try:
                        section.created_at = datetime.fromisoformat(row[5])
                    except:
                        pass
                if row[6]:
                    try:
                        section.updated_at = datetime.fromisoformat(row[6])
                    except:
                        pass
                
                revision.sections.append(section)
            
            cursor.execute('''
                SELECT project_name, revision_name, section_name, motor_data,
                    created_at, updated_at
                FROM devices
            ''')
            
            for row in cursor.fetchall():
                proj_name = row[0]
                rev_name = row[1] or 'Rev-0'
                sec_name = row[2]
                motor_json = row[3]
                
                if proj_name not in projects:
                    continue
                
                project = projects[proj_name]
                revision = project.get_revision_by_name(rev_name)
                
                if not revision:
                    continue
                
                section = revision.get_section_by_name(sec_name)
                if not section:
                    continue
                
                try:
                    motor_dict = json.loads(motor_json)
                    motor = Motor(**motor_dict)
                    
                    if row[4]:
                        try:
                            motor.created_at = datetime.fromisoformat(row[4])
                        except:
                            pass
                    if row[5]:
                        try:
                            motor.updated_at = datetime.fromisoformat(row[5])
                        except:
                            pass
                    
                    section.devices.append(motor)
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding motor data: {e}")
            
            cursor.execute('''
                SELECT project_name, revision_name, section_name, valve_data,
                    order_index, created_at, updated_at
                FROM valves
                ORDER BY section_name, order_index
            ''')
            
            for row in cursor.fetchall():
                proj_name = row[0]
                rev_name = row[1] or 'Rev-0'
                sec_name = row[2]
                valve_json = row[3]
                
                if proj_name not in projects:
                    continue
                
                project = projects[proj_name]
                revision = project.get_revision_by_name(rev_name)
                
                if not revision:
                    continue
                
                section = revision.get_section_by_name(sec_name)
                if not section:
                    continue
                
                try:
                    valve_dict = json.loads(valve_json)
                    
                    if 'created_at' in valve_dict and isinstance(valve_dict['created_at'], str):
                        try:
                            valve_dict['created_at'] = datetime.fromisoformat(valve_dict['created_at'])
                        except:
                            pass
                    
                    if 'updated_at' in valve_dict and isinstance(valve_dict['updated_at'], str):
                        try:
                            valve_dict['updated_at'] = datetime.fromisoformat(valve_dict['updated_at'])
                        except:
                            pass
                    
                    valve = Valve(**valve_dict)
                    section.valves.append(valve)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding valve data: {e}")
            
            logger.info(f"Loaded {len(projects)} projects from database")
            for proj in projects.values():
                logger.info(f"  • {proj.name}: {len(proj.revisions)} revision(s), "
                        f"current='{proj.current_revision_name}'")
            
            return projects
        
        except sqlite3.Error as e:
            logger.error(f"Error loading projects: {e}")
            return {}
    
    # ============================================================
    # ✅ DELETE / REVISION
    # ============================================================
    
    def delete_revision(self, project_name: str, revision_name: str) -> bool:
        """حذف یک Revision"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''DELETE FROM devices WHERE project_name = ? AND revision_name = ?''',
                         (project_name, revision_name))
            cursor.execute('''DELETE FROM valves WHERE project_name = ? AND revision_name = ?''',
                         (project_name, revision_name))
            cursor.execute('''DELETE FROM sections WHERE project_name = ? AND revision_name = ?''',
                         (project_name, revision_name))
            cursor.execute('''DELETE FROM revisions WHERE project_name = ? AND revision_name = ?''',
                         (project_name, revision_name))
            
            conn.commit()
            logger.info(f"Revision '{revision_name}' deleted from '{project_name}'")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error deleting revision: {e}")
            return False
    
    def set_current_revision(self, project_name: str, revision_name: str) -> bool:
        """تنظیم Revision فعلی"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''UPDATE revisions SET is_current = 0 WHERE project_name = ?''',
                         (project_name,))
            cursor.execute('''UPDATE revisions SET is_current = 1 WHERE project_name = ? AND revision_name = ?''',
                         (project_name, revision_name))
            
            conn.commit()
            logger.info(f"Current revision for '{project_name}' set to '{revision_name}'")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error setting current revision: {e}")
            return False
    
    def delete_project(self, project_name: str):
        """حذف کامل یک پروژه — CASCADE"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # ✅ با ON DELETE CASCADE، فقط projects حذف کنیم کافیه
            # ولی برای اطمینان، همه رو دستی حذف می‌کنیم
            
            cursor.execute("DELETE FROM devices WHERE project_name = ?", (project_name,))
            cursor.execute("DELETE FROM valves WHERE project_name = ?", (project_name,))
            cursor.execute("DELETE FROM sections WHERE project_name = ?", (project_name,))
            cursor.execute("DELETE FROM revisions WHERE project_name = ?", (project_name,))
            cursor.execute("DELETE FROM component_labels WHERE project_name = ?", (project_name,))
            cursor.execute("DELETE FROM attachments WHERE project_name = ?", (project_name,))
            cursor.execute("DELETE FROM projects WHERE name = ?", (project_name,))
            
            conn.commit()
            logger.info(f"Project '{project_name}' deleted successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Error deleting project '{project_name}': {e}")
            raise
    
    # ============================================================
    # ✅ CUSTOM COMPONENTS
    # ============================================================
    
    def get_custom_components(self) -> List[Dict]:
        """دریافت لیست کامپوننت‌های سفارشی"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT key, label_fa, label_en, di, do, ai, ao, cable_size, is_active
                FROM custom_components
                ORDER BY key
            ''')
            
            result = []
            for row in cursor.fetchall():
                result.append({
                    'key': row[0],
                    'label_fa': row[1],
                    'label_en': row[2],
                    'di': row[3],
                    'do': row[4],
                    'ai': row[5],
                    'ao': row[6],
                    'cable_size': row[7],
                    'is_active': bool(row[8])
                })
            
            return result
            
        except sqlite3.Error as e:
            logger.error(f"Error getting custom components: {e}")
            return []
    
    def save_custom_component(self, component_data: Dict) -> bool:
        """ذخیره کامپوننت سفارشی"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO custom_components 
                (key, label_fa, label_en, di, do, ai, ao, cable_size, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    label_fa = excluded.label_fa,
                    label_en = excluded.label_en,
                    di = excluded.di,
                    do = excluded.do,
                    ai = excluded.ai,
                    ao = excluded.ao,
                    cable_size = excluded.cable_size,
                    is_active = excluded.is_active,
                    updated_at = excluded.updated_at
            ''', (
                component_data['key'],
                component_data.get('label_fa', component_data['key']),
                component_data.get('label_en', component_data['key']),
                component_data.get('di', 0),
                component_data.get('do', 0),
                component_data.get('ai', 0),
                component_data.get('ao', 0),
                component_data.get('cable_size', '2x1mm²'),
                1,
                now,
                now
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving custom component: {e}")
            return False
    
    # ============================================================
    # ✅ COMPONENT LABELS
    # ============================================================
    
    def save_component_labels(self, project_name: str, labels: Dict[str, Dict[str, str]]):
        """ذخیره برچسب‌های کامپوننت"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM component_labels WHERE project_name = ?", (project_name,))
            
            for key, val in labels.items():
                cursor.execute('''
                    INSERT INTO component_labels (project_name, component_key, persian_label, english_label)
                    VALUES (?, ?, ?, ?)
                ''', (project_name, key, val.get('fa', ''), val.get('en', '')))
            
            conn.commit()
            logger.info(f"Component labels saved for project '{project_name}'")
            
        except sqlite3.Error as e:
            logger.error(f"Error saving component labels: {e}")
            raise
    
    def load_component_labels(self, project_name: str) -> Dict[str, Dict[str, str]]:
        """بارگذاری برچسب‌های کامپوننت"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='component_labels'")
            if not cursor.fetchone():
                logger.warning("component_labels table does not exist, using defaults")
                return COMPONENT_LABELS.copy()
            
            cursor.execute('''
                SELECT component_key, persian_label, english_label
                FROM component_labels
                WHERE project_name = ?
            ''', (project_name,))
            
            labels = {}
            for row in cursor.fetchall():
                labels[row[0]] = {
                    'fa': row[1] or row[0],
                    'en': row[2] or row[0]
                }
            
            if not labels:
                labels = COMPONENT_LABELS.copy()
                self.save_component_labels(project_name, labels)
            
            return labels
            
        except sqlite3.Error as e:
            logger.error(f"Error loading component labels: {e}")
            return COMPONENT_LABELS.copy()
    
    # ============================================================
    # ✅ BACKUP / RESTORE PROJECT
    # ============================================================
    
    def backup_project(self, project_name: str, backup_path: str) -> bool:
        """بکاپ از یک پروژه خاص"""
        try:
            project = self.load_all_projects().get(project_name)
            if not project:
                logger.error(f"Project '{project_name}' not found")
                return False
            
            backup_data = self._build_project_backup_data(project)
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Project '{project_name}' backed up to: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up project '{project_name}': {e}")
            return False
    
    def restore_project(self, backup_path: str, new_name: str = None) -> bool:
        """بازیابی یک پروژه از فایل بکاپ"""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            version = backup_data.get('version', '1.0')
            
            project_data = backup_data.get('project', {})
            original_name = project_data.get('name', 'Restored Project')
            project_name = new_name if new_name else original_name
            
            existing_projects = self.load_all_projects()
            if project_name in existing_projects and not new_name:
                counter = 1
                while f"{project_name} (Restored {counter})" in existing_projects:
                    counter += 1
                project_name = f"{project_name} (Restored {counter})"
            
            project = self._build_project_from_backup(
                backup_data, project_name, version
            )
            
            self.save_project(project)
            
            component_labels = backup_data.get('component_labels', {})
            if component_labels:
                self.save_component_labels(project_name, component_labels)
            
            logger.info(f"Project restored as '{project_name}' from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring project: {e}")
            return False
    
    def _build_project_from_backup(self, backup_data: dict, project_name: str, version: str = '3.0'):
        """ساخت Project از داده‌های JSON"""
        project_data = backup_data.get('project', {})
        
        project = Project(name=project_name)
        project.description = project_data.get('description', '')
        project.client_name = project_data.get('client_name', '')
        project.client_phone = project_data.get('client_phone', '')
        project.client_address = project_data.get('client_address', '')
        project.consultant_name = project_data.get('consultant_name', '')
        project.consultant_phone = project_data.get('consultant_phone', '')
        project.consultant_address = project_data.get('consultant_address', '')
        project.contractor_name = project_data.get('contractor_name', '')
        project.contractor_phone = project_data.get('contractor_phone', '')
        project.contractor_address = project_data.get('contractor_address', '')
        project.designer_name = project_data.get('designer_name', '')
        
        if version in ('2.0', '3.0'):
            project.current_revision_name = project_data.get('current_revision_name', 'Rev-0')
            
            for rev_data in backup_data.get('revisions', []):
                revision = Revision(
                    name=rev_data.get('name', 'Rev-0'),
                    project_name=project_name
                )
                revision.description = rev_data.get('description', '')
                
                for sec_data in rev_data.get('sections', []):
                    section = ProjectSection(
                        name=sec_data.get('name', 'New Section'),
                        description=sec_data.get('description', '')
                    )
                    section.order_index = sec_data.get('order_index', 0)
                    
                    for device_data in sec_data.get('devices', []):
                        motor = Motor(**device_data)
                        section.devices.append(motor)
                    
                    for valve_data in sec_data.get('valves', []):
                        try:
                            valve = Valve(**valve_data)
                            section.valves.append(valve)
                        except Exception as e:
                            logger.warning(f"Failed to restore valve: {e}")
                    
                    revision.sections.append(section)
                
                project.revisions.append(revision)
        else:
            # نسخه 1.0
            project.current_revision_name = 'Rev-0'
            rev_0 = Revision(name='Rev-0', project_name=project_name)
            
            for section_data in backup_data.get('sections', []):
                section = ProjectSection(
                    name=section_data.get('name', 'New Section'),
                    description=section_data.get('description', '')
                )
                section.order_index = section_data.get('order_index', 0)
                
                for device_data in section_data.get('devices', []):
                    motor = Motor(**device_data)
                    section.devices.append(motor)
                
                for valve_data in section_data.get('valves', []):
                    try:
                        valve = Valve(**valve_data)
                        section.valves.append(valve)
                    except Exception as e:
                        logger.warning(f"Failed to restore valve: {e}")
                
                rev_0.sections.append(section)
            
            project.revisions.append(rev_0)
        
        return project
    
    def backup_project_full(self, project_name: str, backup_zip_path: str,
                            attachment_manager=None) -> bool:
        """بکاپ کامل پروژه — شامل دیتابیس + فایل‌های فیزیکی"""
        try:
            project = self.load_all_projects().get(project_name)
            if not project:
                logger.error(f"Project '{project_name}' not found")
                return False
            
            project_data = self._build_project_backup_data(project)
            
            with zipfile.ZipFile(backup_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                project_json = json.dumps(project_data, ensure_ascii=False, indent=2)
                zf.writestr('project.json', project_json)
                
                metadata = {
                    'version': '3.0',
                    'backup_type': 'full',
                    'backup_date': datetime.now().isoformat(),
                    'project_name': project_name,
                    'includes_attachments': attachment_manager is not None,
                    'attachment_count': 0,
                }
                
                if attachment_manager:
                    try:
                        project_attachments_dir = attachment_manager.get_project_dir(project_name)
                        
                        if os.path.exists(project_attachments_dir):
                            file_count = 0
                            
                            for root, dirs, files in os.walk(project_attachments_dir):
                                for file in files:
                                    full_path = os.path.join(root, file)
                                    rel_path = os.path.relpath(full_path, project_attachments_dir)
                                    arcname = os.path.join('Attachments', rel_path).replace('\\', '/')
                                    zf.write(full_path, arcname)
                                    file_count += 1
                            
                            metadata['attachment_count'] = file_count
                            logger.info(f"📎 Added {file_count} attachment(s) to backup")
                    
                    except Exception as e:
                        logger.warning(f"Failed to add attachments: {e}")
                
                metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2)
                zf.writestr('metadata.json', metadata_json)
            
            logger.info(f"✅ Full project backup created: {backup_zip_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error creating full backup: {e}", exc_info=True)
            return False
    
    def restore_project_full(self, backup_zip_path: str,
                            new_name: str = None,
                            attachment_manager=None) -> bool:
        """بازیابی کامل پروژه — با Safe Extraction"""
        temp_dir = None
        
        try:
            temp_dir = tempfile.mkdtemp(prefix='project_restore_')
            
            try:
                _safe_extract_zip(backup_zip_path, temp_dir)
                logger.info(f"✅ Safe extraction completed: {temp_dir}")
            except ValueError as e:
                logger.error(f"❌ Zip Slip detected: {e}")
                return False
            except zipfile.BadZipFile as e:
                logger.error(f"❌ Invalid ZIP file: {e}")
                return False
            
            metadata_path = os.path.join(temp_dir, 'metadata.json')
            project_json_path = os.path.join(temp_dir, 'project.json')
            
            if not os.path.exists(project_json_path):
                logger.error("project.json not found in backup")
                return False
            
            metadata = {}
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            version = metadata.get('version', '3.0')
            logger.info(f"📦 Restoring backup (version {version})")
            
            with open(project_json_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            project_data = backup_data.get('project', {})
            original_name = project_data.get('name', 'Restored Project')
            project_name = new_name if new_name else original_name
            
            existing_projects = self.load_all_projects()
            if project_name in existing_projects and not new_name:
                counter = 1
                while f"{project_name} (Restored {counter})" in existing_projects:
                    counter += 1
                project_name = f"{project_name} (Restored {counter})"
            
            project = self._build_project_from_backup(backup_data, project_name, version)
            
            self.save_project(project)
            
            component_labels = backup_data.get('component_labels', {})
            if component_labels:
                self.save_component_labels(project_name, component_labels)
            
            logger.info(f"✅ Project '{project_name}' restored to database")
            
            # بازیابی Attachments
            temp_attachments = os.path.join(temp_dir, 'Attachments')
            
            if os.path.exists(temp_attachments) and attachment_manager:
                try:
                    dest_attachments = attachment_manager.get_project_dir(project_name)
                    
                    if os.path.exists(dest_attachments):
                        shutil.rmtree(dest_attachments)
                    
                    shutil.copytree(temp_attachments, dest_attachments)
                    
                    logger.info(f"📎 Attachments restored to: {dest_attachments}")
                    
                    attachment_manager.sync_with_filesystem(project_name)
                    
                except Exception as e:
                    logger.warning(f"Failed to restore attachments: {e}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error restoring full backup: {e}", exc_info=True)
            return False
        
        finally:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to clean temp dir: {e}")
    
    def _build_project_backup_data(self, project: Project) -> dict:
        """ساخت داده JSON برای Backup"""
        return {
            'version': '3.0',
            'backup_date': datetime.now().isoformat(),
            'project_name': project.name,
            'project': {
                'name': project.name,
                'description': project.description,
                'client_name': project.client_name,
                'client_phone': project.client_phone,
                'client_address': project.client_address,
                'consultant_name': project.consultant_name,
                'consultant_phone': project.consultant_phone,
                'consultant_address': project.consultant_address,
                'contractor_name': project.contractor_name,
                'contractor_phone': project.contractor_phone,
                'contractor_address': project.contractor_address,
                'designer_name': project.designer_name,
                'current_revision_name': project.current_revision_name,
                'created_at': project.created_at.isoformat() if hasattr(project.created_at, 'isoformat') else str(project.created_at),
                'updated_at': project.updated_at.isoformat() if hasattr(project.updated_at, 'isoformat') else str(project.updated_at),
            },
            'revisions': [
                {
                    'name': rev.name,
                    'description': rev.description,
                    'created_at': rev.created_at.isoformat() if hasattr(rev.created_at, 'isoformat') else str(rev.created_at),
                    'updated_at': rev.updated_at.isoformat() if hasattr(rev.updated_at, 'isoformat') else str(rev.updated_at),
                    'sections': [
                        {
                            'name': section.name,
                            'description': section.description,
                            'order_index': section.order_index,
                            'created_at': section.created_at.isoformat() if hasattr(section.created_at, 'isoformat') else str(section.created_at),
                            'updated_at': section.updated_at.isoformat() if hasattr(section.updated_at, 'isoformat') else str(section.updated_at),
                            'devices': [device.to_dict() for device in section.devices],
                            'valves': [valve.to_dict() for valve in section.valves]
                        }
                        for section in rev.sections
                    ]
                }
                for rev in project.revisions
            ],
            'component_labels': self.load_component_labels(project.name)
        }
    
    def get_project_backup_path(self) -> str:
        """دریافت مسیر پوشه بکاپ پروژه‌ها"""
        backup_dir = Path(self.db_path).parent / "Project_Backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return str(backup_dir.resolve())
    
    # ============================================================
    # ✅ ATTACHMENT OPERATIONS
    # ============================================================
    
    def add_attachment(self, data: Dict[str, Any]) -> bool:
        """افزودن یک پیوست — با ON CONFLICT"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO attachments (
                    project_name, file_name, file_path, file_size,
                    file_type, description, added_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_name, file_name) DO UPDATE SET
                    file_path = excluded.file_path,
                    file_size = excluded.file_size,
                    file_type = excluded.file_type,
                    description = excluded.description,
                    added_at = excluded.added_at
            ''', (
                data['project_name'], data['file_name'], data['file_path'],
                data.get('file_size', 0), data.get('file_type', ''),
                data.get('description', ''), now
            ))
            
            conn.commit()
            logger.info(f"✅ Attachment added to DB: {data['file_name']}")
            return True
        
        except sqlite3.Error as e:
            logger.error(f"Error adding attachment: {e}")
            return False
    
    def get_attachments(self, project_name: str) -> List[Dict[str, Any]]:
        """دریافت لیست پیوست‌ها"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, project_name, file_name, file_path,
                    file_size, file_type, description, added_at
                FROM attachments
                WHERE project_name = ?
                ORDER BY file_name
            ''', (project_name,))
            
            result = []
            for row in cursor.fetchall():
                result.append({
                    'id': row[0],
                    'project_name': row[1],
                    'file_name': row[2],
                    'file_path': row[3],
                    'file_size': row[4] or 0,
                    'file_type': row[5] or '',
                    'description': row[6] or '',
                    'added_at': row[7] or '',
                })
            
            return result
        
        except sqlite3.Error as e:
            logger.error(f"Error getting attachments: {e}")
            return []
    
    def delete_attachment(self, project_name: str, file_name: str) -> bool:
        """حذف یک پیوست از دیتابیس"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM attachments
                WHERE project_name = ? AND file_name = ?
            ''', (project_name, file_name))
            
            conn.commit()
            logger.info(f"🗑️ Attachment deleted from DB: {file_name}")
            return True
        
        except sqlite3.Error as e:
            logger.error(f"Error deleting attachment: {e}")
            return False
    
    def rename_attachment(self, project_name: str, old_name: str,
                        new_name: str, new_path: str = None) -> bool:
        """تغییر نام یک پیوست"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if new_path:
                cursor.execute('''
                    UPDATE attachments SET file_name = ?, file_path = ?
                    WHERE project_name = ? AND file_name = ?
                ''', (new_name, new_path, project_name, old_name))
            else:
                cursor.execute('''
                    UPDATE attachments SET file_name = ?
                    WHERE project_name = ? AND file_name = ?
                ''', (new_name, project_name, old_name))
            
            conn.commit()
            logger.info(f"✏️ Attachment renamed: {old_name} → {new_name}")
            return True
        
        except sqlite3.Error as e:
            logger.error(f"Error renaming attachment: {e}")
            return False
    
    def delete_all_attachments(self, project_name: str) -> int:
        """حذف تمام پیوست‌های یک پروژه"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT COUNT(*) FROM attachments WHERE project_name = ?",
                (project_name,)
            )
            count = cursor.fetchone()[0]
            
            cursor.execute(
                "DELETE FROM attachments WHERE project_name = ?",
                (project_name,)
            )
            
            conn.commit()
            logger.info(f"🗑️ Deleted {count} attachments for '{project_name}'")
            return count
        
        except sqlite3.Error as e:
            logger.error(f"Error deleting all attachments: {e}")
            return 0
    
    # ============================================================
    # ✅ VALVE OPERATIONS
    # ============================================================
    
    def save_valve(self, project_name: str, revision_name: str,
                section_name: str, valve, order_index: int = None) -> bool:
        """ذخیره یک شیر"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            valve_json = json.dumps(valve.to_dict(), ensure_ascii=False)
            
            if order_index is None:
                cursor.execute('''
                    SELECT COALESCE(MAX(order_index), -1) + 1
                    FROM valves
                    WHERE project_name = ? AND revision_name = ? AND section_name = ?
                ''', (project_name, revision_name, section_name))
                order_index = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO valves (
                    project_name, revision_name, section_name,
                    valve_data, order_index, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                project_name, revision_name, section_name,
                valve_json, order_index, now, now,
            ))
            
            conn.commit()
            logger.debug(f"✅ Valve saved: {valve.Equipment} in {section_name}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error saving valve: {e}")
            return False
    
    def update_valve(self, valve_id: int, valve) -> bool:
        """به‌روزرسانی یک شیر"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            valve_json = json.dumps(valve.to_dict(), ensure_ascii=False)
            
            cursor.execute('''
                UPDATE valves SET valve_data = ?, updated_at = ?
                WHERE id = ?
            ''', (valve_json, now, valve_id))
            
            conn.commit()
            logger.debug(f"✅ Valve updated: ID={valve_id}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error updating valve: {e}")
            return False
    
    def delete_valve(self, valve_id: int) -> bool:
        """حذف یک شیر"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM valves WHERE id = ?", (valve_id,))
            
            conn.commit()
            logger.debug(f"🗑️ Valve deleted: ID={valve_id}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error deleting valve: {e}")
            return False
    
    def delete_all_valves(self, project_name: str, revision_name: str = None) -> int:
        """حذف تمام شیرهای یک پروژه"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if revision_name:
                cursor.execute('''
                    SELECT COUNT(*) FROM valves
                    WHERE project_name = ? AND revision_name = ?
                ''', (project_name, revision_name))
                count = cursor.fetchone()[0]
                
                cursor.execute('''
                    DELETE FROM valves
                    WHERE project_name = ? AND revision_name = ?
                ''', (project_name, revision_name))
            else:
                cursor.execute(
                    "SELECT COUNT(*) FROM valves WHERE project_name = ?",
                    (project_name,)
                )
                count = cursor.fetchone()[0]
                
                cursor.execute(
                    "DELETE FROM valves WHERE project_name = ?",
                    (project_name,)
                )
            
            conn.commit()
            logger.debug(f"🗑️ Deleted {count} valves from '{project_name}'")
            return count
            
        except sqlite3.Error as e:
            logger.error(f"Error deleting valves: {e}")
            return 0
    
    def get_valves(self, project_name: str, revision_name: str = None,
                section_name: str = None) -> List[Dict]:
        """دریافت شیرهای یک پروژه"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = '''
                SELECT id, project_name, revision_name, section_name,
                    valve_data, order_index, created_at, updated_at
                FROM valves
                WHERE project_name = ?
            '''
            params = [project_name]
            
            if revision_name:
                query += " AND revision_name = ?"
                params.append(revision_name)
            
            if section_name:
                query += " AND section_name = ?"
                params.append(section_name)
            
            query += " ORDER BY section_name, order_index, id"
            
            cursor.execute(query, params)
            
            result = []
            for row in cursor.fetchall():
                try:
                    valve_data = json.loads(row[4]) if row[4] else {}
                except json.JSONDecodeError:
                    valve_data = {}
                
                valve_data['_id'] = row[0]
                valve_data['_project_name'] = row[1]
                valve_data['_revision_name'] = row[2]
                valve_data['_section_name'] = row[3]
                valve_data['_order_index'] = row[5]
                valve_data['_db_created_at'] = row[6]
                valve_data['_db_updated_at'] = row[7]
                
                result.append(valve_data)
            
            return result
            
        except sqlite3.Error as e:
            logger.error(f"Error getting valves: {e}")
            return []
    
    def get_valves_count(self, project_name: str, revision_name: str = None) -> int:
        """تعداد شیرهای یک پروژه"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if revision_name:
                cursor.execute('''
                    SELECT COUNT(*) FROM valves
                    WHERE project_name = ? AND revision_name = ?
                ''', (project_name, revision_name))
            else:
                cursor.execute(
                    "SELECT COUNT(*) FROM valves WHERE project_name = ?",
                    (project_name,)
                )
            
            return cursor.fetchone()[0]
            
        except sqlite3.Error as e:
            logger.error(f"Error counting valves: {e}")
            return 0
    
    def save_all_valves_for_revision(self, project_name: str, revision_name: str,
                                    valve_sections: List) -> bool:
        """ذخیره تمام شیرهای یک Revision"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM valves
                WHERE project_name = ? AND revision_name = ?
            ''', (project_name, revision_name))
            
            now = datetime.now().isoformat()
            
            for section in valve_sections:
                section_name = getattr(section, 'name', 'Unnamed')
                valves = getattr(section, 'valves', [])
                
                for order_index, valve in enumerate(valves):
                    valve_json = json.dumps(valve.to_dict(), ensure_ascii=False)
                    
                    cursor.execute('''
                        INSERT INTO valves (
                            project_name, revision_name, section_name,
                            valve_data, order_index, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        project_name, revision_name, section_name,
                        valve_json, order_index, now, now,
                    ))
            
            conn.commit()
            logger.info(f"✅ Saved valves for '{project_name}/{revision_name}'")
            return True
            
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Error saving valves: {e}")
            return False
    
    def move_valve(self, valve_id: int, direction: str) -> bool:
        """جابجایی شیر در لیست"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT project_name, revision_name, section_name, order_index
                FROM valves WHERE id = ?
            ''', (valve_id,))
            
            row = cursor.fetchone()
            if not row:
                return False
            
            proj_name, rev_name, sec_name, curr_order = row
            
            if direction == 'up':
                cursor.execute('''
                    SELECT id, order_index FROM valves
                    WHERE project_name = ? AND revision_name = ? AND section_name = ?
                    AND order_index < ?
                    ORDER BY order_index DESC LIMIT 1
                ''', (proj_name, rev_name, sec_name, curr_order))
            else:
                cursor.execute('''
                    SELECT id, order_index FROM valves
                    WHERE project_name = ? AND revision_name = ? AND section_name = ?
                    AND order_index > ?
                    ORDER BY order_index ASC LIMIT 1
                ''', (proj_name, rev_name, sec_name, curr_order))
            
            neighbor = cursor.fetchone()
            if not neighbor:
                return False
            
            neighbor_id, neighbor_order = neighbor
            
            cursor.execute("UPDATE valves SET order_index = ? WHERE id = ?",
                         (neighbor_order, valve_id))
            cursor.execute("UPDATE valves SET order_index = ? WHERE id = ?",
                         (curr_order, neighbor_id))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error moving valve: {e}")
            return False
    
    # ============================================================
    # ✅ LAST ACTIVE PROJECT
    # ============================================================
    
    def set_last_active_project(self, project_name: str) -> bool:
        """ذخیره نام آخرین پروژه فعال"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO app_state (key, value, updated_at)
                VALUES ('last_active_project', ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
            """, (project_name,))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to set last active project: {e}", exc_info=True)
            return False
    
    def get_last_active_project(self) -> Optional[str]:
        """دریافت نام آخرین پروژه فعال"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT value FROM app_state
                WHERE key = 'last_active_project'
            """)
            
            row = cursor.fetchone()
            return row[0] if row else None
            
        except Exception as e:
            logger.error(f"Failed to get last active project: {e}", exc_info=True)
            return None
    
    def clear_last_active_project(self) -> bool:
        """پاک کردن آخرین پروژه فعال"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM app_state WHERE key = 'last_active_project'
            """)
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear last active project: {e}", exc_info=True)
            return False


__all__ = ['DatabaseManager']