"""
add_to_vectorstore.py
Adds the scraped RGUKT content into the existing Chroma vector store
(rgukt2_db) without wiping out what's already there (the academic
regulations handbook).

Usage:
    python add_to_vectorstore.py
"""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

def main():
    print("Loading scraped content...")
    with open("rgukt_scraped_content.txt", "r", encoding="utf-8") as f:
        raw_text = f.read()

    print("Splitting into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", "!", "?"],
        chunk_size=1000,
        chunk_overlap=50,
        length_function=len,
    )
    chunks = splitter.split_text(raw_text)
    documents = [Document(page_content=chunk, metadata={"source": "rgukt_scraped_content.txt"}) for chunk in chunks]
    print(f"Created {len(documents)} chunks.")

    print("Loading embeddings model (may take a moment)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("Opening existing vector store...")
    db = Chroma(persist_directory="./rgukt2_db", embedding_function=embeddings)

    print("Adding new documents to vector store...")
    db.add_documents(documents)

    print(f"Done. Added {len(documents)} chunks to rgukt2_db.")

if __name__ == "__main__":
    main()
