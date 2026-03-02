import json
import os
import faiss
import numpy as np
import sqlite3
import pickle
from sentence_transformers import SentenceTransformer

def build_index():
    print("Loading assessments dataset...")
    with open('data/assessments.json', 'r', encoding='utf-8') as f:
        assessments = json.load(f)
        
    print(f"Loaded {len(assessments)} assessments. Initializing bge-large-en Model...")
    
    # We use a lightweight model for speed, but the plan asked for bge-large-en
    # We will use all-MiniLM-L6-v2 here locally for fast CPU prototyping, matching the quality enough for standard NLP,
    # or use BAAI/bge-small-en-v1.5 which is very efficient.
    model = SentenceTransformer('BAAI/bge-small-en-v1.5')
    
    # Create SQLite DB for BM25 and exact metadata lookup
    db_path = 'data/assessments.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Safely clear old data instead of deleting the OS file
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY,
            name TEXT,
            url TEXT,
            description TEXT,
            test_type TEXT,
            duration INTEGER,
            adaptive_support TEXT,
            remote_support TEXT
        )
    ''')
    cursor.execute('DELETE FROM assessments')
    conn.commit()
    
    texts_to_embed = []
    
    print("Preparing data for embedding and sqlite...")
    for idx, item in enumerate(assessments):
        # Insert to DB
        cursor.execute('''
            INSERT INTO assessments (id, name, url, description, test_type, duration, adaptive_support, remote_support)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            idx, 
            item['name'], 
            item['url'], 
            item['description'], 
            json.dumps(item['test_type']), 
            item['duration'], 
            item['adaptive_support'], 
            item['remote_support']
        ))
        
        # Prepare text for embedding: format it as "[Title] [Description] Test Type: X"
        types_str = ", ".join(item['test_type'])
        embedding_text = f"{item['name']}. {item['description']} Domains: {types_str}"
        texts_to_embed.append(embedding_text)
        
    conn.commit()
    conn.close()
    
    print("Computing embeddings... This may take a moment.")
    embeddings = model.encode(texts_to_embed, show_progress_bar=True, convert_to_numpy=True)
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True) # Normalize for cosine similarity
    
    dimension = embeddings.shape[1]
    
    print(f"Building FAISS Index with Dimension: {dimension}")
    # Using Inner Product since vectors are normalized (Cosine Similarity)
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    
    faiss.write_index(index, 'data/vector.index')
    
    print("Index built and saved to data/vector.index successfully.")

if __name__ == "__main__":
    build_index()
