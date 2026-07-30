import io
from pypdf import PdfReader

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts plain text from a PDF file provided as bytes using the pypdf library.
    """
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        extracted_text = page.extract_text()
        if extracted_text:
            text += extracted_text + "\n"
    return text

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    """
    Splits the given text into chunks of approximately `chunk_size` words.
    Each chunk contains the last `overlap` words from the previous chunk.
    Returns a list of dictionaries with 'content' and 'chunk_index'.
    """
    words = text.split()
    chunks = []
    
    if not words:
        return chunks
        
    start = 0
    chunk_index = 0
    
    # Ensure step is at least 1 to prevent infinite loops if overlap >= chunk_size
    step = max(1, chunk_size - overlap)
    
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk_content = " ".join(chunk_words)
        
        chunks.append({
            "content": chunk_content,
            "chunk_index": chunk_index
        })
        
        chunk_index += 1
        start += step
        
    return chunks
