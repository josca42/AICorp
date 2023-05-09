import chromadb
from dotenv import dotenv_values
from chromadb.utils import embedding_functions
from chromadb.config import Settings


chroma_client = chromadb.Client(
    Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory="/Users/josca/projects/AICorp/data",  # Optional, defaults to .chromadb/ in the current directory
    )
)

openai_api_key = dotenv_values()["OPENAI_API_KEY"]
emb_fn = embedding_functions.OpenAIEmbeddingFunction(
    api_key=openai_api_key, model_name="text-embedding-ada-002"
)

docs_db = chroma_client.get_collection("docs", embedding_function=emb_fn)

if __name__ == "__main__":
    chroma_client.create_collection("docs", embedding_function=emb_fn)
