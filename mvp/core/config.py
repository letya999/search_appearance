"""
Centralized configuration management using Pydantic Settings.
"""
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get project root directory (search_appearance/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class ProviderConfig(BaseSettings):
    """Configuration for a single VLM provider."""
    name: str
    enabled: bool = True
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    max_retries: int = 3
    timeout: int = 60
    rate_limit_rpm: Optional[int] = None  # Requests per minute
    priority: int = 0  # Higher = higher priority in fallback chain
    
    model_config = SettingsConfigDict(env_prefix="", extra="allow")


class DatabaseConfig(BaseSettings):
    """Database configuration."""
    # SQLite
    sqlite_path: str = "data/search_appearance.db"
    
    # LanceDB (for vector storage)
    lancedb_path: str = "data/lancedb"
    
    # Redis (for caching)
    redis_enabled: bool = False
    redis_url: str = "redis://localhost:6379"
    redis_ttl: int = 3600  # 1 hour default
    
    model_config = SettingsConfigDict(env_prefix="DB_")


class EmbeddingConfig(BaseSettings):
    """Embedding model configuration."""
    model_name: str = "openai/clip-vit-base-patch32"
    device: str = "cpu"
    batch_size: int = 32
    
    model_config = SettingsConfigDict(env_prefix="EMBEDDING_")


class SearchConfig(BaseSettings):
    """Search configuration."""
    default_top_k: int = 20
    min_similarity_threshold: float = 0.0
    duplicate_threshold: float = 0.9
    
    # Ranking weights
    weight_exact_match: float = 2.0
    weight_partial_match: float = 1.0
    weight_negative_penalty: float = -1.5
    
    model_config = SettingsConfigDict(env_prefix="SEARCH_")


class APIConfig(BaseSettings):
    """API server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    workers: int = 1
    
    # CORS
    cors_origins: List[str] = ["*"]
    
    # File upload
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: List[str] = [".jpg", ".jpeg", ".png", ".webp"]
    
    model_config = SettingsConfigDict(env_prefix="API_")


class Settings(BaseSettings):
    """Main application settings."""
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Data paths
    data_dir: Path = Field(default=Path("data"), env="DATA_DIR")
    metadata_file: Path = Field(default=Path("data/wiki_1000_metadata.json"), env="METADATA_FILE")
    images_dir: Path = Field(default=Path("data/raw_1000"), env="IMAGES_DIR")
    
    # Provider configurations
    providers: Dict[str, ProviderConfig] = {}
    
    # Sub-configs
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    
    # Provider API keys (for backward compatibility)
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    openrouter_api_key: Optional[str] = Field(default=None, env="OPENROUTER_API_KEY")
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Debug: Show which .env file is being used
        if os.getenv("DEBUG_CONFIG"):
            print(f"Loading config from: {ENV_FILE}")
            print(f"  .env exists: {ENV_FILE.exists()}")
            print(f"  OPENAI_API_KEY: {'✓' if self.openai_api_key else '✗'}")
            print(f"  ANTHROPIC_API_KEY: {'✓' if self.anthropic_api_key else '✗'}")
            print(f"  GOOGLE_API_KEY: {'✓' if self.google_api_key else '✗'}")
            print(f"  OPENROUTER_API_KEY: {'✓' if self.openrouter_api_key else '✗'}")
        self._load_provider_configs()
    
    def _load_provider_configs(self):
        """Load provider configurations from environment and YAML."""
        # Try to load from YAML if it exists
        config_file = PROJECT_ROOT / "config" / "providers.yaml"
        if config_file.exists():
            import yaml
            with open(config_file, 'r') as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config and 'providers' in yaml_config:
                    for name, config in yaml_config['providers'].items():
                        self.providers[name] = ProviderConfig(name=name, **config)
        
        # Override/add API keys from environment variables
        # This allows YAML to define defaults, but env vars to provide keys
        if self.openai_api_key:
            if 'openai' in self.providers:
                # Update existing config with API key
                self.providers['openai'].api_key = self.openai_api_key
            else:
                # Create new config
                self.providers['openai'] = ProviderConfig(
                    name='openai',
                    api_key=self.openai_api_key,
                    default_model='gpt-4o',
                    priority=100
                )
        
        if self.anthropic_api_key:
            if 'anthropic' in self.providers:
                self.providers['anthropic'].api_key = self.anthropic_api_key
            else:
                self.providers['anthropic'] = ProviderConfig(
                    name='anthropic',
                    api_key=self.anthropic_api_key,
                    default_model='claude-3-5-sonnet-20241022',
                    priority=90
                )
        
        if self.google_api_key:
            if 'gemini' in self.providers:
                self.providers['gemini'].api_key = self.google_api_key
            else:
                self.providers['gemini'] = ProviderConfig(
                    name='gemini',
                    api_key=self.google_api_key,
                    default_model='gemini-2.0-flash-exp',
                    priority=80
                )
        
        if self.openrouter_api_key:
            if 'openrouter' in self.providers:
                self.providers['openrouter'].api_key = self.openrouter_api_key
            else:
                self.providers['openrouter'] = ProviderConfig(
                    name='openrouter',
                    api_key=self.openrouter_api_key,
                    base_url='https://openrouter.ai/api/v1',
                    default_model='qwen/qwen-2.5-vl-72b-instruct:free',
                    priority=70
                )
    
    def get_enabled_providers(self) -> List[ProviderConfig]:
        """Get list of enabled providers sorted by priority."""
        enabled = [p for p in self.providers.values() if p.enabled and p.api_key]
        return sorted(enabled, key=lambda p: p.priority, reverse=True)


# Global settings instance
settings = Settings()
