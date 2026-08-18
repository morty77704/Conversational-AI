from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 在当前目录的上一级再上一级目录下找文件，然后转成绝对目录
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # 本项目相关配置
    app_name: str = "Conversational AI"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    cors_origin: str = "http://localhost:8080"
    # 向量化模型配置
    embedding_model: str = "BAAI/bge-base-zh-v1.5"
    embedding_device: str = "cuda"
    embedding_normalize: bool = True
    embedding_query_prefix: str = "为这个句子生成表示以用于检索相关文章："
    embedding_expected_dimension: int = 768
    # 向量数据库配置
    collection_name: str = "abc_kb_bge_v1"
    chroma_path: Path = BASE_DIR.parent / "runtime" / "chroma"
    # 离线知识库构建使用的 OCR 配置
    tesseract_cmd: Path = Path(r"D:\ocr\Tesseract\tesseract.exe")
    ocr_languages: str = "chi_sim+eng"
    # 重排序模型配置
    reranker_model_path: Path
    reranker_device: str = "cuda"
    reranker_use_fp16: bool = True
    reranker_batch_size: int = 4
    reranker_max_length: int = 512
    reranker_top_n: int = 3
    # 意图识别模型配置
    intent_model: str = "qwen3:1.7b"
    ollama_base_url: str = "http://127.0.0.1:11434"
    # 大模型配置
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""
    llm_temperature: float = 0
    # 数据库配置
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = ""
    mysql_password: str = ""
    mysql_database: str = ""
    mysql_charset: str = "utf8mb4"
    mysql_connect_timeout: int = 5
    # jwt配置
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    # redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_connect_timeout: int = 5
    redis_socket_timeout: int = 5
    # SMTP 邮件配置
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_sender_email: str = ""
    smtp_use_ssl: bool = False
    smtp_timeout: int = 10

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",              # 保证从不同工作目录启动时仍能找到 .env。
        env_file_encoding="utf-8",
        extra="ignore",                          # 如果出现暂未声明的配置时不会报错
    )


@lru_cache                           # 只创建一次，不再每次请求时重新读取配置
def get_settings() -> Settings:
    return Settings()
