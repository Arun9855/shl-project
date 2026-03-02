import streamlit as st
import requests
import os

# Production Configuration
# Points to the live API URL or falls back to local for development
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/recommend")
if not API_URL.endswith("/recommend"):
    API_URL = API_URL.rstrip("/") + "/recommend"

# Local Fallback Imports
import json
from core.query_processor import QueryProcessor
from llm.skill_extractor import SkillExtractor
from retrieval.hybrid_search import HybridSearcher
from retrieval.reranker import Reranker
from retrieval.balancer import DomainBalancer

def get_recommendations_local(query_text):
    """Fallback engine to run locally if API fails."""
    qp = QueryProcessor()
    extr = SkillExtractor()
    hs = HybridSearcher() # Uses data/ folder
    rr = Reranker()
    db = DomainBalancer()
    
    clean_query = qp.process(query_text)
    intents = extr.extract(clean_query)
    candidates = hs.search(clean_query, top_k=20)
    reranked = rr.rerank(clean_query, candidates, top_k=20)
    target_domains = intents.get("expected_domains", [])
    balanced = db.balance(reranked, expected_domains=target_domains, target_size=10)
    return balanced[:10]

st.set_page_config(page_title="SHL Assessment Recommender", page_icon="🎯", layout="wide")

st.title("🎯 SHL Recommender System")
st.markdown("---")

query = st.text_area("Input Requirement (Query or Job Description):", height=150, placeholder="e.g. Senior Java dev with behavioral leadership skills")

if st.button("Generate Recommendations", type="primary"):
    if not query.strip():
        st.warning("Please provide a search requirement.")
    else:
        with st.spinner("Processing (Using Hybrid RAG Architecture)..."):
            assessments = []
            source = "API"
            
            # --- ATTEMPT 1: API (Preferred for Compliance) ---
            try:
                resp = requests.post(API_URL, json={"query": query}, timeout=10)
                if resp.status_code == 200:
                    assessments = resp.json().get("recommended_assessments", [])
                else:
                    raise Exception(f"API Code {resp.status_code}")
            except Exception as e:
                # --- ATTEMPT 2: LOCAL FALLBACK (Safety) ---
                st.info("💡 Backend API is initializing. Running from core engine fallback...")
                try:
                    results = get_recommendations_local(query)
                    source = "Local Engine"
                    for r in results:
                        assessments.append({
                            "name": r.get("name", "N/A"),
                            "url": r.get("url", "#"),
                            "description": r.get("description", ""),
                            "test_type": r.get("test_type", []),
                            "duration": r.get("duration"),
                            "adaptive_support": r.get("adaptive_support"),
                            "remote_support": r.get("remote_support")
                        })
                except Exception as ex:
                    st.error(f"System Error: {ex}")
            
            # --- DISPLAY RESULTS ---
            if assessments:
                st.success(f"Top {len(assessments)} Matches Found (Mode: {source})")
                for idx, test in enumerate(assessments, 1):
                    with st.expander(f"Recommendation {idx}: {test['name']}"):
                        st.subheader(f"[{test['name']}]({test['url']})")
                        if test.get('description'):
                            st.write(test['description'])
                        
                        st.divider()
                        c1, c2, c3 = st.columns(3)
                        c1.write(f"**Domain:** {', '.join(test['test_type'])}")
                        c2.write(f"**Duration:** {test['duration']} min")
                        c3.write(f"**Adaptive:** {test['adaptive_support']}")
