"""
Ingest specific PDFs into the Chroma vector store
Usage: venv\Scripts\python ingest_pdfs.py
"""

import os
import re
import json
import sys
import hashlib
import pdfplumber
from pypdf import PdfReader
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n\n--- Page {page_num} ---\n\n{page_text}"
    except Exception as e1:
        try:
            reader = PdfReader(file_path)
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n\n--- Page {page_num} ---\n\n{page_text}"
        except Exception as e2:
            logger.error(f"Error extracting PDF {file_path}: {e1}, {e2}")
    return text

def chunk_text(text: str, metadata: Dict, chunk_size: int = 1000, overlap: int = 150) -> List[Dict]:
    """Split text into chunks"""
    chunks = []
    paragraphs = text.split('\n\n')
    current_chunk = ""
    chunk_id = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) > chunk_size and current_chunk:
            chunk_metadata = {
                "document_id": metadata["id"],
                "chunk_id": f"{metadata['id']}_chunk_{chunk_id}",
                "title": metadata["title"],
                "category": metadata["category"],
                "year": metadata["year"],
                "source_url": metadata["source_url"],
                "content": current_chunk.strip()
            }
            chunks.append(chunk_metadata)
            chunk_id += 1

            words = current_chunk.split()
            overlap_words = words[-int(overlap/5):]
            current_chunk = " ".join(overlap_words) + "\n\n" + para
        else:
            current_chunk += "\n\n" + para if current_chunk else para

    if current_chunk.strip():
        chunk_metadata = {
            "document_id": metadata["id"],
            "chunk_id": f"{metadata['id']}_chunk_{chunk_id}",
            "title": metadata["title"],
            "category": metadata["category"],
            "year": metadata["year"],
            "source_url": metadata["source_url"],
            "content": current_chunk.strip()
        }
        chunks.append(chunk_metadata)

    return chunks

def index_chunks(chunks: List[Dict]):
    """Index chunks into Chroma vector store"""
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain.schema import Document

    logger.info(f"Indexing {len(chunks)} chunks...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    documents = []
    for chunk in chunks:
        doc = Document(
            page_content=chunk["content"],
            metadata={
                "document_id": chunk["document_id"],
                "chunk_id": chunk["chunk_id"],
                "title": chunk["title"],
                "category": chunk["category"],
                "year": chunk["year"],
                "source_url": chunk["source_url"]
            }
        )
        documents.append(doc)

    vector_store = Chroma(
        persist_directory="./rgukt2_db",
        embedding_function=embeddings
    )

    batch_size = 50
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        vector_store.add_documents(batch)
        logger.info(f"Indexed batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")

    logger.info(f"Successfully indexed {len(chunks)} chunks")

def main():
    pdfs = [
        {
            "path": r"C:\Users\sidda\Downloads\e prospectus 2024.pdf",
            "title": "RGUKT Basar UG Admission Prospectus 2024-25",
            "year": "2024",
            "category": "admission",
            "source_url": "https://www.rgukt.ac.in/assets/docs/prospectus_2024.pdf"
        },
        {
            "path": r"C:\Users\sidda\Downloads\prospectus2023.pdf",
            "title": "RGUKT Basar UG Admission Prospectus 2023-24",
            "year": "2023",
            "category": "admission",
            "source_url": "https://www.rgukt.ac.in/assets/docs/prospectus_2023.pdf"
        }
    ]

    all_chunks = []

    for pdf in pdfs:
        if not os.path.exists(pdf["path"]):
            logger.error(f"File not found: {pdf['path']}")
            continue

        logger.info(f"Processing: {pdf['title']}")
        
        # Extract text
        text = extract_text_from_pdf(pdf["path"])
        
        if not text.strip():
            logger.warning(f"No text extracted from {pdf['path']}")
            continue

        logger.info(f"Extracted {len(text)} characters from {pdf['title']}")

        # Generate metadata
        pdf["id"] = hashlib.md5(pdf["title"].encode()).hexdigest()[:16]
        
        # Chunk
        chunks = chunk_text(text, pdf)
        all_chunks.extend(chunks)
        logger.info(f"Generated {len(chunks)} chunks from {pdf['title']}")

    if all_chunks:
        logger.info(f"Total chunks: {len(all_chunks)}")
        
        # Save chunks to file
        with open("ingested_chunks.jsonl", "w", encoding="utf-8") as f:
            for chunk in all_chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
        logger.info("Chunks saved to ingested_chunks.jsonl")

        # Index to vector store
        index_chunks(all_chunks)
        logger.info("All PDFs indexed successfully!")
    else:
        logger.error("No chunks generated!")

if __name__ == "__main__":
    main()