import faiss
import json
import sqlite3
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

class HybridSearcher:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        print("Loading local BGE embedding model...")
        self.model = SentenceTransformer('BAAI/bge-small-en-v1.5')
        
        print("Loading vector index...")
        self.index = faiss.read_index(f"{data_dir}/vector.index")
        
        print("Loading SQLite DB for metadata...")
        self.conn = sqlite3.connect(f"{data_dir}/assessments.db", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        print("Building BM25 corpus...")
        self._build_bm25()

    def _build_bm25(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, test_type, description FROM assessments")
        rows = cursor.fetchall()
        
        self.bm25_corpus = []
        self.id_map = []
        
        for r in rows:
            self.id_map.append(r['id'])
            # Create a rich text for BM25
            text = f"{r['name']} {r['test_type']} {r['description']}".lower()
            self.bm25_corpus.append(text.split())
            
        self.bm25 = BM25Okapi(self.bm25_corpus)
        
    def _fetch_metadata(self, doc_ids):
        if not doc_ids: return []
        placeholders = ','.join('?' for _ in doc_ids)
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM assessments WHERE id IN ({placeholders})", doc_ids)
        rows = cursor.fetchall()
        
        # Sort returned rows by the requested doc_ids order
        row_dict = {r['id']: dict(r) for r in rows}
        results = []
        for d_id in doc_ids:
            if d_id in row_dict:
                # parse test_type JSON
                r = row_dict[d_id]
                r['test_type'] = json.loads(r['test_type'])
                results.append(r)
        return results

    def search(self, query, top_k=20):
        # 1. Vector Search
        query_emb = self.model.encode([query], convert_to_numpy=True)
        query_emb = query_emb / np.linalg.norm(query_emb, axis=1, keepdims=True)
        
        vec_k = min(top_k * 2, self.index.ntotal)
        distances, indices = self.index.search(query_emb, vec_k)
        
        vector_results = [(int(idx), float(dist)) for idx, dist in zip(indices[0], distances[0]) if idx != -1]
        
        # 2. BM25 Lexical Search
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        # get top elements
        top_bm25_idx = np.argsort(bm25_scores)[::-1][:vec_k]
        bm25_results = [(self.id_map[i], bm25_scores[i]) for i in top_bm25_idx if bm25_scores[i] > 0]
        
        # 3. Reciprocal Rank Fusion (RRF)
        rrf_k = 60
        rrf_scores = {}
        
        for rank, (doc_id, _) in enumerate(vector_results):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (rrf_k + rank + 1)
            
        for rank, (doc_id, _) in enumerate(bm25_results):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (rrf_k + rank + 1)
            
        # Sort by RRF
        fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        fused_ids = [d_id for d_id, score in fused]
        
        # Fetch detailed records
        metadata = self._fetch_metadata(fused_ids)
        return metadata

if __name__ == "__main__":
    hs = HybridSearcher()
    res = hs.search("Need Java and Python developers", top_k=5)
    for r in res:
        print(f"[{r['id']}] {r['name']} - {r['test_type']}")
