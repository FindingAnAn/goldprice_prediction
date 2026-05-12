import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class FSConfig:
    """Cấu hình file system"""
    incoming_dir: Path
    saved_dir: Path
    
    @classmethod
    def from_env(cls) -> 'FSConfig':
        """Load từ environment variables"""
        incoming = Path(os.getenv('INCOMING_DIR', './data/incoming'))
        saved = Path(os.getenv('SAVED_DIR', './data/saved'))
        
        return cls(incoming_dir=incoming, saved_dir=saved)
    
    def validate(self) -> bool:
        """Validate cấu hình"""
        try:
            self.incoming_dir.mkdir(parents=True, exist_ok=True)
            self.saved_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False


@dataclass
class PostgresConfig:
    """Cấu hình PostgreSQL"""
    host: str
    port: int
    database: str
    username: str
    password: str
    
    @classmethod
    def from_env(cls) -> 'PostgresConfig':
        """Load từ environment variables"""
        return cls(
            host=os.getenv('PG_HOST', 'localhost'),
            port=int(os.getenv('PG_PORT', '5432')),
            database=os.getenv('PG_DATABASE', 'postgres'),
            username=os.getenv('PG_USERNAME', 'postgres'),
            password=os.getenv('PG_PASSWORD', '')
        )
    
    @property
    def connection_string(self) -> str:
        """Tạo connection string"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"