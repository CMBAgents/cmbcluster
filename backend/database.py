import sqlite3
import asyncio
import threading
import structlog
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
from pathlib import Path

from models import User, Environment, ActivityLog, UserRole, PodStatus
from storage_models import UserStorage, StorageType, StorageStatus
from file_models import UserFile, FileType
from config import settings

logger = structlog.get_logger()

class DatabaseManager:
    # User environment variable management
    async def get_user_env_vars(self, user_id: str) -> Dict[str, str]:
        """Get all environment variables for a user as a dict"""
        async with self.get_connection() as conn:
            rows = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "SELECT key, value FROM user_env_vars WHERE user_id = ?",
                    (user_id,)
                ).fetchall()
            )
            return {row['key']: row['value'] for row in rows}

    async def set_user_env_var(self, user_id: str, key: str, value: str) -> None:
        """Insert or update a user environment variable"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """
                    INSERT INTO user_env_vars (user_id, key, value, created_at, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id, key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
                    """,
                    (user_id, key, value)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)

    async def delete_user_env_var(self, user_id: str, key: str) -> None:
        """Delete a user environment variable by key"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "DELETE FROM user_env_vars WHERE user_id = ? AND key = ?",
                    (user_id, key)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)

    async def clear_user_env_vars(self, user_id: str) -> None:
        """Delete all environment variables for a user"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "DELETE FROM user_env_vars WHERE user_id = ?",
                    (user_id,)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)

    # ============ USER FILES MANAGEMENT ============
    
    async def create_user_file(self, user_file: UserFile) -> UserFile:
        """Create a new user file record"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """
                    INSERT INTO user_files 
                    (id, user_id, file_name, file_type, encrypted_content, 
                     environment_variable_name, container_path, file_size, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (user_file.id, user_file.user_id, user_file.file_name, user_file.file_type.value,
                     user_file.encrypted_content, user_file.environment_variable_name, 
                     user_file.container_path, user_file.file_size, user_file.created_at.isoformat())
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
            logger.info("User file created", file_id=user_file.id, user_id=user_file.user_id, file_name=user_file.file_name)
            return user_file

    async def get_user_files(self, user_id: str) -> List[UserFile]:
        """Get all files for a user"""
        async with self.get_connection() as conn:
            rows = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """
                    SELECT id, user_id, file_name, file_type, encrypted_content,
                           environment_variable_name, container_path, file_size, 
                           created_at, updated_at 
                    FROM user_files 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC
                    """,
                    (user_id,)
                ).fetchall()
            )
            
            files = []
            for row in rows:
                user_file = UserFile(
                    id=row['id'],
                    user_id=row['user_id'],
                    file_name=row['file_name'],
                    file_type=FileType(row['file_type']),
                    encrypted_content=row['encrypted_content'],
                    environment_variable_name=row['environment_variable_name'],
                    container_path=row['container_path'],
                    file_size=row['file_size'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
                )
                files.append(user_file)
            
            return files

    async def get_user_file(self, user_id: str, file_id: str) -> Optional[UserFile]:
        """Get a specific user file by ID"""
        async with self.get_connection() as conn:
            row = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """
                    SELECT id, user_id, file_name, file_type, encrypted_content,
                           environment_variable_name, container_path, file_size, 
                           created_at, updated_at 
                    FROM user_files 
                    WHERE user_id = ? AND id = ?
                    """,
                    (user_id, file_id)
                ).fetchone()
            )
            
            if not row:
                return None
            
            return UserFile(
                id=row['id'],
                user_id=row['user_id'],
                file_name=row['file_name'],
                file_type=FileType(row['file_type']),
                encrypted_content=row['encrypted_content'],
                environment_variable_name=row['environment_variable_name'],
                container_path=row['container_path'],
                file_size=row['file_size'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            )

    async def update_user_file(self, user_id: str, file_id: str, **updates) -> bool:
        """Update user file metadata and/or content"""
        if not updates:
            return False
        
        # Build dynamic update query
        set_clauses = []
        values = []
        
        for field, value in updates.items():
            if field == 'encrypted_content':
                set_clauses.append(f"{field} = ?")
                values.append(value)
            elif field in ['file_name', 'environment_variable_name', 'container_path', 'file_size']:
                set_clauses.append(f"{field} = ?")
                values.append(value)
        
        if not set_clauses:
            return False
        
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        values.extend([user_id, file_id])
        
        query = f"""
            UPDATE user_files 
            SET {', '.join(set_clauses)}
            WHERE user_id = ? AND id = ?
        """
        
        async with self.get_connection() as conn:
            cursor = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(query, values)
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
            
            updated = cursor.rowcount > 0
            if updated:
                logger.info("User file updated", file_id=file_id, user_id=user_id, fields=list(updates.keys()))
            return updated

    async def delete_user_file(self, user_id: str, file_id: str) -> bool:
        """Delete a user file"""
        async with self.get_connection() as conn:
            cursor = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "DELETE FROM user_files WHERE user_id = ? AND id = ?",
                    (user_id, file_id)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info("User file deleted", file_id=file_id, user_id=user_id)
            return deleted

    async def get_user_files_for_environment(self, user_id: str) -> Dict[str, UserFile]:
        """Get all user files mapped by environment variable name for pod creation"""
        files = await self.get_user_files(user_id)
        return {file.environment_variable_name: file for file in files if file.environment_variable_name is not None}
    """SQLite database manager for CMBCluster with thread-safe operations"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_path
        self._lock = threading.RLock()
        self._initialized = False
        self._init_database()
    
    def _init_database(self):
        """Initialize database with required tables"""
        if self._initialized:
            return
            
        # Ensure directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path, timeout=30.0)
                conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency
                conn.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and performance
                conn.execute("PRAGMA temp_store=memory")  # Store temp tables in memory
                conn.execute("PRAGMA mmap_size=268435456")  # 256MB memory map
                conn.execute("PRAGMA cache_size=10000")  # 10MB page cache
                conn.execute("PRAGMA wal_autocheckpoint=1000")  # Auto checkpoint every 1000 pages
                conn.execute("PRAGMA busy_timeout=30000")  # 30 second busy timeout
                
                # Create users table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        role TEXT NOT NULL DEFAULT 'user',
                        created_at TIMESTAMP NOT NULL,
                        last_login TIMESTAMP,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        promoted_by TEXT,
                        promoted_at TIMESTAMP
                    )
                """)
                
                # Add missing columns to existing users table (migration)
                try:
                    conn.execute("ALTER TABLE users ADD COLUMN promoted_by TEXT")
                    logger.info("Added promoted_by column to users table")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        logger.warning("Could not add promoted_by column", error=str(e))
                
                try:
                    conn.execute("ALTER TABLE users ADD COLUMN promoted_at TIMESTAMP")
                    logger.info("Added promoted_at column to users table")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        logger.warning("Could not add promoted_at column", error=str(e))
                
                # Create environments table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS environments (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        user_email TEXT NOT NULL,
                        env_id TEXT NOT NULL,
                        pod_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        url TEXT,
                        created_at TIMESTAMP NOT NULL,
                        last_activity TIMESTAMP,
                        resource_config TEXT,  -- JSON string
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                
                # Create activity_logs table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS activity_logs (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        details TEXT,
                        timestamp TIMESTAMP NOT NULL,
                        status TEXT NOT NULL DEFAULT 'success',
                        ip_address TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                
                # Create user_storages table for cloud storage management
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_storages (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        bucket_name TEXT UNIQUE NOT NULL,
                        display_name TEXT NOT NULL,
                        storage_type TEXT NOT NULL DEFAULT 'cloud_storage',
                        status TEXT NOT NULL DEFAULT 'creating',
                        created_at TIMESTAMP NOT NULL,
                        last_accessed TIMESTAMP,
                        size_bytes INTEGER DEFAULT 0,
                        object_count INTEGER DEFAULT 0,
                        location TEXT NOT NULL,
                        storage_class TEXT NOT NULL DEFAULT 'STANDARD',
                        versioning_enabled BOOLEAN DEFAULT 1,
                        metadata TEXT,  -- JSON string for additional metadata
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                
                # Create environment_storages table to link environments with storage
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS environment_storages (
                        id TEXT PRIMARY KEY,
                        environment_id TEXT NOT NULL,
                        storage_id TEXT NOT NULL,
                        mount_path TEXT NOT NULL DEFAULT '/workspace',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (environment_id) REFERENCES environments (id),
                        FOREIGN KEY (storage_id) REFERENCES user_storages (id)
                    )
                """)

                # Create user_env_vars table for per-user environment variables
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_env_vars (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        key TEXT NOT NULL,
                        value TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, key),
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)

                # Create user_files table for secure file storage
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_files (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        file_name TEXT NOT NULL,
                        file_type TEXT NOT NULL,
                        encrypted_content BLOB NOT NULL,
                        environment_variable_name TEXT,
                        container_path TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        file_size INTEGER NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                
                # Migration: Update existing user_files table to allow NULL environment_variable_name
                try:
                    # Check if the column constraint needs to be updated
                    cursor = conn.execute("PRAGMA table_info(user_files)")
                    columns = cursor.fetchall()
                    env_var_column = next((col for col in columns if col[1] == 'environment_variable_name'), None)
                    
                    # SQLite doesn't support ALTER COLUMN, so we need to recreate the table if it has NOT NULL constraint
                    if env_var_column and env_var_column[3] == 1:  # notnull is 1
                        # Create new table with correct schema
                        conn.execute("""
                            CREATE TABLE user_files_new (
                                id TEXT PRIMARY KEY,
                                user_id TEXT NOT NULL,
                                file_name TEXT NOT NULL,
                                file_type TEXT NOT NULL,
                                encrypted_content BLOB NOT NULL,
                                environment_variable_name TEXT,
                                container_path TEXT NOT NULL,
                                created_at TIMESTAMP NOT NULL,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                file_size INTEGER NOT NULL,
                                FOREIGN KEY (user_id) REFERENCES users (id)
                            )
                        """)
                        
                        # Copy data from old table
                        conn.execute("""
                            INSERT INTO user_files_new 
                            SELECT id, user_id, file_name, file_type, encrypted_content, 
                                   environment_variable_name, container_path, created_at, 
                                   updated_at, file_size 
                            FROM user_files
                        """)
                        
                        # Drop old table and rename new one
                        conn.execute("DROP TABLE user_files")
                        conn.execute("ALTER TABLE user_files_new RENAME TO user_files")
                except Exception as e:
                    # Migration might have already been applied
                    logger.debug("User files migration might already be applied", error=str(e))
                
                # Create applications table for multi-image support
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS applications (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        summary TEXT,
                        image_path TEXT NOT NULL,
                        port INTEGER DEFAULT 8888,
                        icon_url TEXT,
                        category TEXT DEFAULT 'research',
                        created_at TIMESTAMP NOT NULL,
                        created_by TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT 1,
                        tags TEXT,  -- JSON array as text
                        FOREIGN KEY (created_by) REFERENCES users (id)
                    )
                """)
                
                # Create user_role_changes table for audit trail
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_role_changes (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        changed_by TEXT NOT NULL,
                        old_role TEXT NOT NULL,
                        new_role TEXT NOT NULL,
                        reason TEXT,
                        changed_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        FOREIGN KEY (changed_by) REFERENCES users (id)
                    )
                """)
                
                # Add promoted_by and promoted_at columns to users table
                try:
                    conn.execute("ALTER TABLE users ADD COLUMN promoted_by TEXT")
                    conn.execute("ALTER TABLE users ADD COLUMN promoted_at TIMESTAMP")
                    logger.info("Added role management columns to users table")
                except Exception as e:
                    logger.debug("Role management columns might already exist", error=str(e))

                # Add missing columns to applications table (migration)
                try:
                    conn.execute("ALTER TABLE applications ADD COLUMN port INTEGER DEFAULT 8888")
                    logger.info("Added port column to applications table")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        logger.warning("Could not add port column", error=str(e))
                
                try:
                    conn.execute("ALTER TABLE applications ADD COLUMN icon_url TEXT")
                    logger.info("Added icon_url column to applications table")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        logger.warning("Could not add icon_url column", error=str(e))
                
                try:
                    conn.execute("ALTER TABLE applications ADD COLUMN category TEXT DEFAULT 'research'")
                    logger.info("Added category column to applications table")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        logger.warning("Could not add category column", error=str(e))
                
                try:
                    conn.execute("ALTER TABLE applications ADD COLUMN is_active BOOLEAN DEFAULT 1")
                    logger.info("Added is_active column to applications table")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        logger.warning("Could not add is_active column", error=str(e))
                
                try:
                    conn.execute("ALTER TABLE applications ADD COLUMN tags TEXT")
                    logger.info("Added tags column to applications table")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        logger.warning("Could not add tags column", error=str(e))
                
                # Add application_id and image_path columns to environments table
                try:
                    conn.execute("ALTER TABLE environments ADD COLUMN application_id TEXT")
                    conn.execute("ALTER TABLE environments ADD COLUMN image_path TEXT")
                    logger.info("Added application columns to environments table")
                except Exception as e:
                    logger.debug("Application columns might already exist", error=str(e))
                
                # Add subscription columns with defaults for existing users
                try:
                    conn.execute("ALTER TABLE users ADD COLUMN subscription_tier TEXT DEFAULT 'free'")
                    conn.execute("ALTER TABLE users ADD COLUMN subscription_expires_at TIMESTAMP")
                    conn.execute("ALTER TABLE users ADD COLUMN max_uptime_minutes INTEGER DEFAULT 60")
                    conn.execute("ALTER TABLE users ADD COLUMN auto_shutdown_enabled BOOLEAN DEFAULT 1")
                    logger.info("Added subscription columns to users table")
                except Exception as e:
                    # Columns might already exist
                    logger.debug("Subscription columns might already exist", error=str(e))
                
                # Create indexes for better query performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_environments_user_id ON environments (user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_environments_env_id ON environments (env_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_environments_status ON environments (status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs (user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs (timestamp)")
                
                # Storage-related indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_storages_user_id ON user_storages (user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_storages_bucket_name ON user_storages (bucket_name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_storages_status ON user_storages (status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_environment_storages_env_id ON environment_storages (environment_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_environment_storages_storage_id ON environment_storages (storage_id)")
                
                # User files indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_files_user_id ON user_files (user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_files_type ON user_files (file_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_files_env_var ON user_files (environment_variable_name)")
                
                # Application and role management indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_applications_created_by ON applications (created_by)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_applications_category ON applications (category)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_applications_is_active ON applications (is_active)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_role_changes_user_id ON user_role_changes (user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_role_changes_changed_by ON user_role_changes (changed_by)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_role_changes_changed_at ON user_role_changes (changed_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_environments_application_id ON environments (application_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users (role)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_users_promoted_by ON users (promoted_by)")
                
                conn.commit()
                conn.close()
                
                self._initialized = True
                logger.info("Database initialized successfully", db_path=self.db_path)
                
            except Exception as e:
                logger.error("Failed to initialize database", error=str(e), db_path=self.db_path)
                raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection with proper resource management"""
        conn = None
        try:
            # Create connection in the executor thread to avoid SQLite threading issues
            def create_connection():
                connection = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
                connection.row_factory = sqlite3.Row  # Enable named column access
                # Apply performance optimizations to each connection
                connection.execute("PRAGMA journal_mode=WAL")
                connection.execute("PRAGMA synchronous=NORMAL")
                connection.execute("PRAGMA temp_store=memory")
                connection.execute("PRAGMA cache_size=10000")
                connection.execute("PRAGMA busy_timeout=30000")
                return connection
            
            conn = await asyncio.get_event_loop().run_in_executor(None, create_connection)
            yield conn
        except Exception as e:
            logger.error("Database connection error", error=str(e))
            raise
        finally:
            if conn:
                await asyncio.get_event_loop().run_in_executor(None, conn.close)
    
    # User management methods
    async def create_user(self, user: User) -> User:
        """Create a new user"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """
                    INSERT OR REPLACE INTO users 
                    (id, email, name, role, created_at, last_login, is_active, updated_at,
                     subscription_tier, subscription_expires_at, max_uptime_minutes, auto_shutdown_enabled)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?)
                    """,
                    (user.id, user.email, user.name, user.role.value, 
                     user.created_at.isoformat(), 
                     user.last_login.isoformat() if user.last_login else None,
                     user.is_active,
                     user.subscription_tier.value,
                     user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
                     user.max_uptime_minutes,
                     user.auto_shutdown_enabled)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
            logger.info("User created/updated", user_id=user.id, email=user.email)
            return user
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        async with self.get_connection() as conn:
            row = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """SELECT id, email, name, role, created_at, last_login, is_active,
                              subscription_tier, subscription_expires_at, max_uptime_minutes, auto_shutdown_enabled 
                       FROM users WHERE id = ?""", (user_id,)
                ).fetchone()
            )
            
            if row:
                try:
                    from models import SubscriptionTier
                    # Safely access optional fields by converting row to dict
                    row_dict = dict(row)
                    
                    return User(
                        id=row['id'],
                        email=row['email'],
                        name=row['name'],
                        role=UserRole(row['role']),
                        created_at=datetime.fromisoformat(row['created_at']),
                        last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
                        is_active=bool(row['is_active']),
                        subscription_tier=SubscriptionTier(row_dict.get('subscription_tier', 'free') or 'free'),
                        subscription_expires_at=datetime.fromisoformat(row_dict['subscription_expires_at']) if row_dict.get('subscription_expires_at') else None,
                        max_uptime_minutes=row_dict.get('max_uptime_minutes', 60) or 60,
                        auto_shutdown_enabled=bool(row_dict.get('auto_shutdown_enabled', True))
                    )
                except Exception as e:
                    logger.error("Error processing user row in get_user", user_id=user_id, error=str(e))
                    # Return a basic user object with defaults if subscription columns don't exist
                    from models import SubscriptionTier
                    return User(
                        id=row['id'],
                        email=row['email'],
                        name=row['name'],
                        role=UserRole(row['role']),
                        created_at=datetime.fromisoformat(row['created_at']),
                        last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
                        is_active=bool(row['is_active']),
                        subscription_tier=SubscriptionTier.FREE,
                        subscription_expires_at=None,
                        max_uptime_minutes=60,
                        auto_shutdown_enabled=True
                    )
            return None
    
    async def update_user_login(self, user_id: str) -> None:
        """Update user's last login timestamp"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "UPDATE users SET last_login = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (datetime.utcnow().isoformat(), user_id)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
    
    # Environment management methods
    async def create_environment(self, environment: Environment) -> Environment:
        """Create a new environment"""
        async with self.get_connection() as conn:
            resource_config_json = json.dumps(environment.resource_config) if environment.resource_config else None
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """
                    INSERT INTO environments 
                    (id, user_id, user_email, env_id, pod_name, status, url, 
                     created_at, last_activity, resource_config, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (environment.id, environment.user_id, environment.user_email,
                     environment.env_id, environment.pod_name, environment.status.value,
                     environment.url, environment.created_at.isoformat(),
                     environment.last_activity.isoformat() if environment.last_activity else None,
                     resource_config_json)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
            logger.info("Environment created", env_id=environment.id, user_id=environment.user_id)
            return environment
    
    async def get_user_environments(self, user_id: str) -> List[Environment]:
        """Get all environments for a user"""
        async with self.get_connection() as conn:
            rows = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "SELECT * FROM environments WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,)
                ).fetchall()
            )
            
            environments = []
            for row in rows:
                resource_config = json.loads(row['resource_config']) if row['resource_config'] else {}
                env = Environment(
                    id=row['id'],
                    user_id=row['user_id'],
                    user_email=row['user_email'],
                    env_id=row['env_id'],
                    pod_name=row['pod_name'],
                    status=PodStatus(row['status']),
                    url=row['url'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    last_activity=datetime.fromisoformat(row['last_activity']) if row['last_activity'] else None,
                    resource_config=resource_config
                )
                environments.append(env)
            
            return environments
    
    async def get_environment(self, user_id: str, env_id: str) -> Optional[Environment]:
        """Get specific environment by user_id and env_id"""
        async with self.get_connection() as conn:
            row = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "SELECT * FROM environments WHERE user_id = ? AND env_id = ?",
                    (user_id, env_id)
                ).fetchone()
            )
            
            if row:
                resource_config = json.loads(row['resource_config']) if row['resource_config'] else {}
                return Environment(
                    id=row['id'],
                    user_id=row['user_id'],
                    user_email=row['user_email'],
                    env_id=row['env_id'],
                    pod_name=row['pod_name'],
                    status=PodStatus(row['status']),
                    url=row['url'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    last_activity=datetime.fromisoformat(row['last_activity']) if row['last_activity'] else None,
                    resource_config=resource_config
                )
            return None
    
    async def update_environment_status(self, env_id: str, status: PodStatus) -> None:
        """Update environment status"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "UPDATE environments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE env_id = ?",
                    (status.value, env_id)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
    
    async def update_environment_activity(self, user_id: str) -> None:
        """Update last activity for all user environments"""
        async with self.get_connection() as conn:
            now = datetime.utcnow().isoformat()
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "UPDATE environments SET last_activity = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (now, user_id)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
    
    async def delete_environment(self, user_id: str, env_id: str) -> bool:
        """Delete environment"""
        async with self.get_connection() as conn:
            cursor = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "DELETE FROM environments WHERE user_id = ? AND env_id = ?",
                    (user_id, env_id)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info("Environment deleted", user_id=user_id, env_id=env_id)
            return deleted
    
    # Activity logging methods
    async def log_activity(self, activity: ActivityLog) -> None:
        """Log user activity"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """
                    INSERT INTO activity_logs 
                    (id, user_id, action, details, timestamp, status, ip_address)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (activity.id, activity.user_id, activity.action, activity.details,
                     activity.timestamp.isoformat(), activity.status, activity.ip_address)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
    
    async def get_user_activity(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user activity log"""
        async with self.get_connection() as conn:
            rows = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """
                    SELECT action, details, timestamp, status 
                    FROM activity_logs 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                    """,
                    (user_id, limit)
                ).fetchall()
            )
            
            return [
                {
                    "action": row['action'],
                    "details": row['details'],
                    "timestamp": row['timestamp'],
                    "status": row['status']
                }
                for row in rows
            ]
    
    async def cleanup_old_logs(self, days: int = 30) -> None:
        """Clean up old activity logs"""
        async with self.get_connection() as conn:
            cutoff_date = datetime.utcnow().timestamp() - (days * 24 * 3600)
            
            cursor = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "DELETE FROM activity_logs WHERE timestamp < ?",
                    (datetime.fromtimestamp(cutoff_date).isoformat(),)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
            
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                logger.info("Cleaned up old activity logs", deleted_count=deleted_count)
    
    # Storage management methods
    async def create_storage(self, storage: UserStorage) -> None:
        """Create a new user storage record"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """
                    INSERT INTO user_storages 
                    (id, user_id, bucket_name, display_name, storage_type, status,
                     created_at, last_accessed, size_bytes, object_count, location,
                     storage_class, versioning_enabled, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (storage.id, storage.user_id, storage.bucket_name, storage.display_name,
                     storage.storage_type.value, storage.status.value, storage.created_at.isoformat(),
                     storage.last_accessed.isoformat() if storage.last_accessed else None,
                     storage.size_bytes, storage.object_count, storage.location,
                     storage.storage_class, storage.versioning_enabled, json.dumps(storage.metadata))
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
    
    async def get_user_storages(self, user_id: str) -> List[UserStorage]:
        """Get all storage buckets for a user"""
        async with self.get_connection() as conn:
            rows = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """
                    SELECT * FROM user_storages 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC
                    """,
                    (user_id,)
                ).fetchall()
            )
            
            storages = []
            for row in rows:
                storage = UserStorage(
                    id=row['id'],
                    user_id=row['user_id'],
                    bucket_name=row['bucket_name'],
                    display_name=row['display_name'],
                    storage_type=StorageType(row['storage_type']),
                    status=StorageStatus(row['status']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    last_accessed=datetime.fromisoformat(row['last_accessed']) if row['last_accessed'] else None,
                    size_bytes=row['size_bytes'],
                    object_count=row['object_count'],
                    location=row['location'],
                    storage_class=row['storage_class'],
                    versioning_enabled=bool(row['versioning_enabled']),
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
                storages.append(storage)
            
            return storages
    
    async def get_storage_by_id(self, storage_id: str) -> Optional[UserStorage]:
        """Get storage by ID"""
        async with self.get_connection() as conn:
            row = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "SELECT * FROM user_storages WHERE id = ?",
                    (storage_id,)
                ).fetchone()
            )
            
            if not row:
                return None
            
            return UserStorage(
                id=row['id'],
                user_id=row['user_id'],
                bucket_name=row['bucket_name'],
                display_name=row['display_name'],
                storage_type=StorageType(row['storage_type']),
                status=StorageStatus(row['status']),
                created_at=datetime.fromisoformat(row['created_at']),
                last_accessed=datetime.fromisoformat(row['last_accessed']) if row['last_accessed'] else None,
                size_bytes=row['size_bytes'],
                object_count=row['object_count'],
                location=row['location'],
                storage_class=row['storage_class'],
                versioning_enabled=bool(row['versioning_enabled']),
                metadata=json.loads(row['metadata']) if row['metadata'] else {}
            )
    
    async def update_storage_status(self, storage_id: str, status: StorageStatus) -> bool:
        """Update storage status"""
        async with self.get_connection() as conn:
            cursor = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "UPDATE user_storages SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (status.value, storage_id)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
            return cursor.rowcount > 0
    
    async def update_storage_metadata(self, storage_id: str, size_bytes: int, object_count: int) -> bool:
        """Update storage size and object count"""
        async with self.get_connection() as conn:
            cursor = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """
                    UPDATE user_storages 
                    SET size_bytes = ?, object_count = ?, last_accessed = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (size_bytes, object_count, storage_id)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
            return cursor.rowcount > 0
    
    async def delete_storage(self, storage_id: str) -> bool:
        """Delete storage record"""
        async with self.get_connection() as conn:
            # First delete environment-storage links
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "DELETE FROM environment_storages WHERE storage_id = ?",
                    (storage_id,)
                )
            )
            
            # Then delete the storage record
            cursor = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "DELETE FROM user_storages WHERE id = ?",
                    (storage_id,)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
            return cursor.rowcount > 0
    
    async def link_environment_storage(self, environment_id: str, storage_id: str, mount_path: str = "/workspace") -> None:
        """Link an environment to a storage bucket"""
        link_id = f"{environment_id}-{storage_id}"
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """
                    INSERT OR REPLACE INTO environment_storages 
                    (id, environment_id, storage_id, mount_path)
                    VALUES (?, ?, ?, ?)
                    """,
                    (link_id, environment_id, storage_id, mount_path)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
    
    async def get_environment_storage(self, environment_id: str) -> Optional[str]:
        """Get storage ID linked to an environment"""
        async with self.get_connection() as conn:
            row = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "SELECT storage_id FROM environment_storages WHERE environment_id = ?",
                    (environment_id,)
                ).fetchone()
            )
            return row['storage_id'] if row else None
    
    async def get_all_running_environments(self) -> List[Environment]:
        """Get all running environments across all users"""
        async with self.get_connection() as conn:
            rows = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """SELECT * FROM environments 
                       WHERE status IN ('running', 'pending') 
                       ORDER BY created_at DESC""",
                ).fetchall()
            )
            
            environments = []
            for row in rows:
                resource_config = json.loads(row['resource_config']) if row['resource_config'] else {}
                env = Environment(
                    id=row['id'],
                    user_id=row['user_id'],
                    user_email=row['user_email'],
                    env_id=row['env_id'],
                    pod_name=row['pod_name'],
                    status=PodStatus(row['status']),
                    url=row['url'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    last_activity=datetime.fromisoformat(row['last_activity']) if row['last_activity'] else None,
                    resource_config=resource_config
                )
                environments.append(env)
            
            return environments
    
    # Application Management Methods
    async def create_application(self, application) -> None:
        """Create a new application image"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """INSERT INTO applications 
                       (id, name, summary, image_path, port, icon_url, category, created_at, created_by, is_active, tags)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (application.id, application.name, application.summary, application.image_path,
                     application.port or 8888, application.icon_url, application.category, 
                     application.created_at.isoformat(), application.created_by, application.is_active, 
                     json.dumps(application.tags))
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
    
    async def list_applications(self) -> List:
        """List all applications"""
        from models import ApplicationImage
        async with self.get_connection() as conn:
            rows = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "SELECT * FROM applications WHERE is_active = 1 ORDER BY created_at DESC"
                ).fetchall()
            )
            
            applications = []
            for row in rows:
                try:
                    # Safely access optional fields by checking column names
                    row_dict = dict(row)
                    
                    # Handle tags field safely
                    tags = []
                    if 'tags' in row_dict and row_dict['tags']:
                        try:
                            tags = json.loads(row_dict['tags'])
                        except (json.JSONDecodeError, TypeError):
                            tags = []
                    
                    app = ApplicationImage(
                        id=row['id'],
                        name=row['name'],
                        summary=row['summary'] or "",
                        image_path=row['image_path'],
                        port=row_dict.get('port', 8888),
                        icon_url=row_dict.get('icon_url'),
                        category=row_dict.get('category', 'research'),
                        created_at=datetime.fromisoformat(row['created_at']),
                        created_by=row['created_by'],
                        is_active=bool(row_dict.get('is_active', True)),
                        tags=tags
                    )
                    applications.append(app)
                except Exception as e:
                    try:
                        app_id = row['id'] if 'id' in dict(row) else 'unknown'
                    except:
                        app_id = 'unknown'
                    logger.error("Error processing application row", app_id=app_id, error=str(e))
                    # Skip this row and continue
                    continue
            return applications
    
    async def get_application(self, application_id: str):
        """Get application by ID"""
        from models import ApplicationImage
        async with self.get_connection() as conn:
            row = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "SELECT * FROM applications WHERE id = ?",
                    (application_id,)
                ).fetchone()
            )
            
            if row:
                # Safely access optional fields by checking column names
                row_dict = dict(row)
                return ApplicationImage(
                    id=row['id'],
                    name=row['name'],
                    summary=row['summary'],
                    image_path=row['image_path'],
                    port=row_dict.get('port', 8888),
                    icon_url=row['icon_url'],
                    category=row['category'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    created_by=row['created_by'],
                    is_active=bool(row['is_active']),
                    tags=json.loads(row['tags']) if row['tags'] else []
                )
            return None
    
    async def update_application(self, application) -> None:
        """Update an application"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """UPDATE applications 
                       SET name=?, summary=?, image_path=?, port=?, icon_url=?, category=?, tags=?
                       WHERE id=?""",
                    (application.name, application.summary, application.image_path,
                     application.port or 8888, application.icon_url, application.category, 
                     json.dumps(application.tags), application.id)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
    
    async def delete_application(self, application_id: str) -> None:
        """Delete an application (soft delete)"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "UPDATE applications SET is_active = 0 WHERE id = ?",
                    (application_id,)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
    
    # User Management Methods
    async def list_all_users(self) -> List[User]:
        """List all users (admin only)"""
        async with self.get_connection() as conn:
            rows = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """SELECT * FROM users ORDER BY created_at DESC"""
                ).fetchall()
            )
            
            users = []
            for row in rows:
                try:
                    # Safely access optional fields by checking column names
                    row_dict = dict(row)
                    
                    # Check if optional columns exist by trying to access them
                    promoted_by = None
                    promoted_at = None
                    
                    try:
                        promoted_by = row_dict.get('promoted_by')
                        if row_dict.get('promoted_at'):
                            promoted_at = datetime.fromisoformat(row_dict['promoted_at'])
                    except (KeyError, TypeError):
                        # Columns don't exist or are malformed, use defaults
                        promoted_by = None
                        promoted_at = None
                    
                    user = User(
                        id=row['id'],
                        email=row['email'],
                        name=row['name'],
                        role=UserRole(row['role']),
                        created_at=datetime.fromisoformat(row['created_at']),
                        last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
                        is_active=bool(row['is_active']),
                        promoted_by=promoted_by,
                        promoted_at=promoted_at
                    )
                    users.append(user)
                except Exception as e:
                    try:
                        row_id = row['id'] if 'id' in dict(row) else 'unknown'
                    except:
                        row_id = 'unknown'
                    logger.error("Error processing user row", row_id=row_id, error=str(e))
                    # Skip this row and continue
                    continue
            return users
    
    async def update_user_role(self, user_id: str, new_role: UserRole, promoted_by: str, promoted_at: datetime) -> None:
        """Update user role"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """UPDATE users 
                       SET role=?, promoted_by=?, promoted_at=?
                       WHERE id=?""",
                    (new_role.value, promoted_by, promoted_at.isoformat(), user_id)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
    
    async def update_user_status(self, user_id: str, is_active: bool) -> None:
        """Update user active status"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "UPDATE users SET is_active=? WHERE id=?",
                    (is_active, user_id)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
    
    async def log_role_change(self, change_record: Dict) -> None:
        """Log role change for audit trail"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """INSERT INTO user_role_changes 
                       (id, user_id, changed_by, old_role, new_role, reason, changed_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (change_record['id'], change_record['user_id'], change_record['changed_by'],
                     change_record['old_role'], change_record['new_role'], change_record['reason'],
                     change_record['changed_at'].isoformat())
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
    
    async def get_user_role_history(self, user_id: str) -> List:
        """Get role change history for a user"""
        from models import RoleChangeRecord
        async with self.get_connection() as conn:
            rows = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """SELECT rc.*, u.name as changed_by_name 
                       FROM user_role_changes rc 
                       LEFT JOIN users u ON rc.changed_by = u.id 
                       WHERE rc.user_id = ? 
                       ORDER BY rc.changed_at DESC""",
                    (user_id,)
                ).fetchall()
            )
            
            history = []
            for row in rows:
                record = RoleChangeRecord(
                    id=row['id'],
                    user_id=row['user_id'],
                    changed_by=row['changed_by'],
                    changed_by_name=row['changed_by_name'] or 'Unknown',
                    old_role=row['old_role'],
                    new_role=row['new_role'],
                    reason=row['reason'],
                    changed_at=datetime.fromisoformat(row['changed_at'])
                )
                history.append(record)
            return history

# Global database instance
db_manager: Optional[DatabaseManager] = None

def get_database() -> DatabaseManager:
    """Get the global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager
