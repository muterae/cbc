import os
import time
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

load_dotenv()


PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
INDEX_NAME = "cbc-curriculum-rag"
TXT_FILE = "output.txt"

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY is not set in your .env file.")

if not os.path.exists(TXT_FILE):
    raise FileNotFoundError(f"Could not find {TXT_FILE}.")
