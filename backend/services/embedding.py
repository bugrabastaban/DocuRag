import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("Warning: GEMINI_API_KEY not found in environment variables.")
else:
    genai.configure(api_key=API_KEY)

# Use the gemini-embedding-001 model
MODEL_NAME = "models/gemini-embedding-001"

def embed_text(text: str) -> list[float]:
    """
    Embeds a single text string into a 768-dimensional vector using Gemini.
    """
    result = genai.embed_content(
        model=MODEL_NAME,
        content=text,
        task_type="retrieval_document",
        output_dimensionality=768
    )
    return result['embedding']

def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Embeds a list of texts into vectors.
    Uses Gemini's native batch support, but processes in chunks
    with a slight delay to respect rate limits.
    """
    if not texts:
        return []
        
    embeddings = []
    # Process in batches of 100 to stay within typical API limits
    batch_size = 100
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        try:
            # Gemini's embed_content natively supports a list of strings
            result = genai.embed_content(
                model=MODEL_NAME,
                content=batch,
                task_type="retrieval_document",
                output_dimensionality=768
            )
            embeddings.extend(result['embedding'])
            
            # Small delay to prevent hitting rate limits when processing many batches
            if i + batch_size < len(texts):
                time.sleep(1)
                
        except Exception as e:
            print(f"Batch embedding error: {e}. Falling back to sequential embedding...")
            # Fallback: embed sequentially if batch request fails
            for text in batch:
                embeddings.append(embed_text(text))
                time.sleep(1) # Add delay between sequential calls to avoid rate limits
                
    return embeddings
