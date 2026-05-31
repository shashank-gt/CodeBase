import os, logging
from dotenv import load_dotenv
load_dotenv()

class Settings:
    # LLM
    LLM_PROVIDER: str      = os.getenv("LLM_PROVIDER", "groq")
    GEMINI_API_KEY: str    = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str      = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GROQ_API_KEY: str      = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str        = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    LOCAL_LLM_URL: str     = os.getenv("LOCAL_LLM_URL", "http://localhost:11434")
    LOCAL_LLM_MODEL: str   = os.getenv("LOCAL_LLM_MODEL", "mistral")
    LLM_TIMEOUT: int       = int(os.getenv("LLM_TIMEOUT", "90"))
    LLM_MAX_TOKENS: int    = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    
    # Embeddings
    EMBEDDING_MODEL: str   = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # Vector DB
    CHROMA_DIR: str        = os.getenv("CHROMA_DIR", "./chroma_db")
    
    # RAG
    TOP_K: int             = int(os.getenv("TOP_K", "20"))
    RERANK_TOP_K: int      = int(os.getenv("RERANK_TOP_K", "8"))
    CHUNK_SIZE: int        = int(os.getenv("CHUNK_SIZE", "400"))
    CHUNK_OVERLAP: int     = int(os.getenv("CHUNK_OVERLAP", "80"))
    MIN_CHUNK_CHARS: int   = int(os.getenv("MIN_CHUNK_CHARS", "50"))
    SCORE_THRESHOLD: float = float(os.getenv("SCORE_THRESHOLD", "0.0"))
    USE_HYDE: bool         = os.getenv("USE_HYDE", "true").lower() == "true"
    USE_RERANK: bool       = os.getenv("USE_RERANK", "false").lower() == "true"
    COHERE_API_KEY: str    = os.getenv("COHERE_API_KEY", "")
    
    # Cache
    CACHE_ENABLED: bool    = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_MAX_SIZE: int    = int(os.getenv("CACHE_MAX_SIZE", "200"))
    
    # Server
    HOST: str              = os.getenv("HOST", "0.0.0.0")
    PORT: int              = int(os.getenv("PORT", "8000"))
    CORS_ORIGINS: str      = os.getenv("CORS_ORIGINS", "*")
    
    # Ingestion
    REPO_TEMP_DIR: str     = os.getenv("REPO_TEMP_DIR", "./tmp_repos")
    MAX_FILE_KB: int       = int(os.getenv("MAX_FILE_KB", "500"))
    GITHUB_TOKEN: str      = os.getenv("GITHUB_TOKEN", "")
    LOG_LEVEL: str         = os.getenv("LOG_LEVEL", "INFO")

    def validate(self):
        if self.LLM_PROVIDER not in ("gemini", "groq", "local"):
            # If user had 'openai' set, force them to gemini
            self.LLM_PROVIDER = "gemini"
        if self.LLM_PROVIDER == "gemini" and not self.GEMINI_API_KEY:
            logging.getLogger(__name__).warning("GEMINI_API_KEY not set in .env")
        if self.LLM_PROVIDER == "groq" and not self.GROQ_API_KEY:
            logging.getLogger(__name__).warning("GROQ_API_KEY not set in .env")
        return self

settings = Settings().validate()
