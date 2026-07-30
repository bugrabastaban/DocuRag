from services.embedding import embed_batch

def test_embed():
    sample_texts = [
        "Yapay zeka teknolojileri her geçen gün gelişiyor.",
        "RAG sistemleri, LLM'lerin bilgiye erişimini kolaylaştırır.",
        "Ankara'da bugün hava güneşli ve sıcak."
    ]
    
    print(f"Embedding {len(sample_texts)} sentences using embed_batch...")
    embeddings = embed_batch(sample_texts)
    
    print(f"\nReturned embeddings count: {len(embeddings)}")
    
    for i, emb in enumerate(embeddings):
        print(f"\nSentence {i+1}: '{sample_texts[i]}'")
        print(f"Vector dimension: {len(emb)}")
        
        if len(emb) == 768:
            print("  [OK] Dimension exactly matches 768.")
        else:
            print(f"  [FAIL] Dimension is {len(emb)}, expected 768.")
            
        print(f"  Preview of vector: {emb[:5]} ...")

if __name__ == "__main__":
    test_embed()
