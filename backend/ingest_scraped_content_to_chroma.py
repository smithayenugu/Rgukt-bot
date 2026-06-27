import os
import re
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

load_dotenv()

SOURCE_FILE = "rgukt_scraped_content.txt"
PERSIST_DIR = "./rgukt2_db"
EMBED_MODEL = "all-MiniLM-L6-v2"


def normalize_text(s: str) -> str:
    s = s.replace('\r\n', '\n').replace('\r', '\n')
    # collapse excessive whitespace but keep newlines
    s = re.sub(r'[\t ]+', ' ', s)
    return s.strip()


def main():
    if not os.path.exists(SOURCE_FILE):
        raise FileNotFoundError(f"Missing {SOURCE_FILE}")

    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        raw = f.read()

    # Split on section markers we know exist in the file (=== Heading ===)
    parts = re.split(r"\n(?===\s*[^=]+\s*===\n)", raw)
    # Re-attach the separators if the split kept them
    docs_text = []
    if parts:
        # If split retained separators, rebuild logically
        for i, chunk in enumerate(parts):
            if not chunk.strip():
                continue
            if chunk.strip().startswith("==="):
                docs_text.append(chunk)
            else:
                # chunk without marker—prepend previous if needed; keep as is
                docs_text.append(chunk)

    # Fallback: if marker split fails, treat whole file as one document
    if not docs_text:
        docs_text = [raw]

    documents = []
    for idx, txt in enumerate(docs_text):
        txt = normalize_text(txt)
        if not txt:
            continue
        documents.append(Document(page_content=txt, metadata={"source": SOURCE_FILE, "chunk_id": str(idx)}))

    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    # Load existing Chroma index if it exists; otherwise create.
    # Chroma can be updated by adding documents.
    if os.path.exists(PERSIST_DIR) and os.path.exists(os.path.join(PERSIST_DIR, "chroma.sqlite3")):
        vs = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)
        vs.add_documents(documents)
        vs.persist()
        print(f"Appended {len(documents)} documents from {SOURCE_FILE} into {PERSIST_DIR}")
    else:
        vs = Chroma.from_documents(documents=documents, embedding=embeddings, persist_directory=PERSIST_DIR)
        vs.persist()
        print(f"Created {PERSIST_DIR} with {len(documents)} documents from {SOURCE_FILE}")


if __name__ == "__main__":
    main()

