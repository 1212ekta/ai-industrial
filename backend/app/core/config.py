from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "IKIP"
    API_V1_STR: str = "/api/v1"
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    
    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    
    # SQLite Database (for metadata)
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./storage/db/ikip.db"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
