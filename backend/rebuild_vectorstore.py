"""
rebuild_vectorstore.py
Rebuilds rgukt2_db from scratch using BOTH the original Academic
Regulations Handbook PDF AND the scraped website content, avoiding
duplicate chunks from repeated incremental additions.

Usage:
    python rebuild_vectorstore.py
"""

import shutil
import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_community.document_loaders import PyPDFLoader

PERSIST_DIR = "./rgukt2_db"
PDF_PATH = "Academic_Regulations_Hand_Book.pdf"
SCRAPED_TXT_PATH = "rgukt_scraped_content.txt"

def main():
    if os.path.exists(PERSIST_DIR):
        print(f"Removing old vector store at {PERSIST_DIR}...")
        shutil.rmtree(PERSIST_DIR)

    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", "!", "?"],
        chunk_size=1000,
        chunk_overlap=50,
        length_function=len,
    )

    all_documents = []

    if os.path.exists(PDF_PATH):
        print(f"Loading {PDF_PATH}...")
        loader = PyPDFLoader(PDF_PATH)
        pdf_docs = loader.load()
        pdf_chunks = splitter.split_documents(pdf_docs)
        all_documents.extend(pdf_chunks)
        print(f"  -> {len(pdf_chunks)} chunks from handbook")
    else:
        print(f"WARNING: {PDF_PATH} not found, skipping.")

    if os.path.exists(SCRAPED_TXT_PATH):
        print(f"Loading {SCRAPED_TXT_PATH}...")
        with open(SCRAPED_TXT_PATH, "r", encoding="utf-8") as f:
            raw_text = f.read()
        text_chunks = splitter.split_text(raw_text)
        scraped_docs = [
            Document(page_content=chunk, metadata={"source": SCRAPED_TXT_PATH})
            for chunk in text_chunks
        ]
        all_documents.extend(scraped_docs)
        print(f"  -> {len(scraped_docs)} chunks from scraped content")
    else:
        print(f"WARNING: {SCRAPED_TXT_PATH} not found, skipping.")

    print(f"\nTotal chunks to embed: {len(all_documents)}")

    print("Loading embeddings model...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("Building fresh vector store (this may take a minute)...")
    db = Chroma.from_documents(
        documents=all_documents,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
    )

    print(f"\nDone. Rebuilt {PERSIST_DIR} with {len(all_documents)} total chunks.")

if __name__ == "__main__":
    main()