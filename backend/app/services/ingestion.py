import io
from pypdf import PdfReader
from docx import Document as DocxDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter

def extract_text_from_file(file_bytes: bytes, filename: str) -> list[dict]:
    """
    Reads file bytes and extracts text page-by-page.
    Returns: [{"text": "...", "page": 1}]
    """
    ext = filename.split(".")[-1].lower()
    pages_data = []

    if ext == "pdf":
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages_data.append({"text": text, "page": idx + 1})

    elif ext == "docx":
        docx_file = io.BytesIO(file_bytes)
        doc = DocxDocument(docx_file)
        full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        pages_data.append({"text": full_text, "page": 1})

    elif ext == "txt":
        try:
            text = file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1")
        pages_data.append({"text": text, "page": 1})

    else:
        raise ValueError(f"Unsupported file format: {ext}")

    return pages_data


def chunk_document_pages(pages_data: list[dict], chunk_size: int = 1500, overlap: int = 300) -> list[dict]:
    """
    Splits text into smaller chunks while keeping track of page numbers.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    all_chunks = []

    for item in pages_data:
        chunks = splitter.split_text(item["text"])
        for chunk in chunks:
            all_chunks.append({
                "content": chunk,
                "page": item["page"]
            })

    return all_chunks