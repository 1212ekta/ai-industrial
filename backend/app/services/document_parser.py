import fitz  # PyMuPDF
import docx
import pandas as pd
from typing import List, Dict, Any

def parse_pdf(file_path: str) -> List[Dict[str, Any]]:
    doc = fitz.open(file_path)
    chunks = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        if text.strip():
            chunks.append({
                "page_number": page_num + 1,
                "text": text.strip()
            })
    return chunks

def parse_docx(file_path: str) -> List[Dict[str, Any]]:
    doc = docx.Document(file_path)
    # Simple chunking by paragraphs for docx (grouping could be added)
    text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    # Treating as one page for simplicity in MVP, could split by length
    return [{"page_number": 1, "text": text}] if text else []

def parse_txt(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return [{"page_number": 1, "text": text.strip()}] if text.strip() else []

def parse_excel(file_path: str) -> List[Dict[str, Any]]:
    df = pd.read_excel(file_path)
    text = df.to_csv(index=False)
    return [{"page_number": 1, "text": text}]

def parse_document(file_path: str, file_type: str) -> List[Dict[str, Any]]:
    if file_type == "application/pdf":
        return parse_pdf(file_path)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return parse_docx(file_path)
    elif file_type == "text/plain":
        return parse_txt(file_path)
    elif file_type in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
        return parse_excel(file_path)
    else:
        # Default fallback
        try:
            return parse_txt(file_path)
        except:
            return []
