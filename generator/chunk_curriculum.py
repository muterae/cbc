from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path



# Skip all regex cleaning functions and split directly
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n\n", "\n", ". ", " "]
)

with open("output.txt", 'r', encoding='utf-8') as f:
    raw = f.read()


chunks = text_splitter.split_text(raw)
print(f"Chunks generated without cleaning: {len(chunks)}")
print(f"Total chunks generated: {len(chunks)}")
print("\n---------------- Sample Chunk 1 -------------------------------")
print(chunks[0])
print("\n---------------------------------------------------------------")
