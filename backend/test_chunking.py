import os
from services.chunking import extract_text_from_pdf, chunk_text

def test_chunking():
    pdf_path = os.path.join("test_files", "ApexDynamics_Kurumsal_Bilgi_Dokumani.pdf")
    
    print(f"Reading PDF from: {pdf_path}")
    # Read bytes
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
        
    print(f"Read PDF file, size: {len(file_bytes)} bytes")
    
    # Extract text
    text = extract_text_from_pdf(file_bytes)
    print(f"Extracted text length: {len(text)} characters")
    print("-" * 50)
    print(f"Preview of text (first 200 chars):\n{text[:200]}")
    print("-" * 50)
    
    # Chunk text
    # Using a smaller chunk size for demonstration purposes
    chunks = chunk_text(text, chunk_size=30, overlap=5)
    print(f"Total chunks generated: {len(chunks)}")
    
    # Print the first 3 chunks to verify
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n--- Chunk {chunk['chunk_index']} ---")
        print(f"Word count: {len(chunk['content'].split())}")
        print(f"Content:\n{chunk['content']}")

if __name__ == "__main__":
    test_chunking()
