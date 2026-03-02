import os
from typing import Annotated, List, Any
from fastapi import FastAPI, Body
from pydantic import BaseModel, HttpUrl

from core.query_processor import QueryProcessor
from llm.skill_extractor import SkillExtractor
from retrieval.hybrid_search import HybridSearcher
from retrieval.reranker import Reranker
from retrieval.balancer import DomainBalancer

app = FastAPI(title="SHL Assessment Recommender API")

print("Initializing AI components...")
qp = QueryProcessor()
extr = SkillExtractor()
hs = HybridSearcher()
rr = Reranker()
db = DomainBalancer()
print("All components loaded successfully.")

class RecommendRequest(BaseModel):
    query: str

class Assessment(BaseModel):
    name: str
    url: str
    description: str | None = None
    duration: int | None = None
    adaptive_support: str | None = None
    remote_support: str | None = None
    test_type: List[str]

class RecommendResponse(BaseModel):
    recommended_assessments: List[Assessment]

@app.get("/health")
def health_check():
    # Exactly as requested in some systems:
    return {"status": "healthy"}

@app.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest) -> Any:
    # 1. Process query
    clean_query = qp.process(request.query)
    
    # 2. Extract intents/skills
    intents = extr.extract(clean_query)
    
    # Enrich the search query slightly with hard and soft skills, but keep original for context
    # 3. Hybrid search (Top 20)
    # Use the clean clinical query for the most accurate search matches
    candidates = hs.search(clean_query, top_k=20)
    
    # 4. Cross-Encoder Rerank
    # The reranker will use the original query to ensure the highest quality results match the hiring profile
    reranked = rr.rerank(clean_query, candidates, top_k=20)
    
    # 5. Domain Balance
    # Filter and reorder based on the extracted domains from the LLM
    target_domains = intents.get("expected_domains", [])
    balanced = db.balance(reranked, expected_domains=target_domains, target_size=10)
    
    # Ensure minimum 1 and maximum 10
    final_results = balanced[:10]
    
    # Map to schema
    output = []
    for r in final_results:
        output.append(Assessment(
            name=r.get("name", "Unknown"),
            url=r.get("url", ""),
            description=r.get("description"),
            duration=r.get("duration"),
            adaptive_support=r.get("adaptive_support"),
            remote_support=r.get("remote_support"),
            test_type=r.get("test_type", [])
        ))
        
    return RecommendResponse(recommended_assessments=output)
