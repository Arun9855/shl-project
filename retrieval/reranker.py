from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self):
        print("Loading CrossEncoder (ms-marco-MiniLM-L-6-v2)...")
        self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', max_length=512)
        
    def rerank(self, query, candidates, top_k=10):
        if not candidates: return []
        
        # Construct pairs (Query, DocumentText)
        pairs = []
        for c in candidates:
            doc_text = f"{c['name']}. {c['description']} Types: {', '.join(c['test_type'])}"
            pairs.append([query, doc_text])
            
        scores = self.model.predict(pairs)
        
        # Associate score and sort
        scored_candidates = []
        for score, candidate in zip(scores, candidates):
            candidate['rerank_score'] = float(score)
            scored_candidates.append(candidate)
            
        scored_candidates.sort(key=lambda x: x['rerank_score'], reverse=True)
        return scored_candidates[:top_k]

if __name__ == "__main__":
    r = Reranker()
    print("Reranker loaded.")
