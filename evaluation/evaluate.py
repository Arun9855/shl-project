import pandas as pd
import requests
import time
import os

API_URL = "http://127.0.0.1:8000/recommend"

def evaluate():
    print("Loading Gen_AI Dataset (Test-Set)...")
    try:
        df = pd.read_excel('Gen_AI Dataset.xlsx', sheet_name='Test-Set')
    except Exception:
        print("Test-Set sheet not found, falling back to default.")
        df = pd.read_excel('Gen_AI Dataset.xlsx')
    
    # Extract unique queries to be tested
    test_queries = df['Query'].dropna().unique()
    print(f"Found {len(test_queries)} unique queries in the test set.")
    
    # We will generate predictions for all
    predictions = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}/{len(test_queries)}] Query: {query[:80]}...")
        
        try:
            resp = requests.post(API_URL, json={'query': query}, timeout=30)
            if resp.status_code == 200:
                recs = resp.json().get('recommended_assessments', [])
                if not recs:
                    print("  -> Empty results!")
                for r in recs:
                    predictions.append({
                        "Query": query,
                        "Assessment_url": r['url']
                    })
                print(f"  -> Generated {len(recs)} recommendations.")
            else:
                print(f"  -> API Error: {resp.status_code}")
        except Exception as e:
            print(f"  -> Request Failed: {e}")
            
        time.sleep(2) # Be nice to the API/Gemini limits
        
    pred_df = pd.DataFrame(predictions)
    
    # Ensure mandatory columns for Appendix 3
    pred_df = pred_df[['Query', 'Assessment_url']]
    
    csv_path = 'arun_kumar.csv'
    pred_df.to_csv(csv_path, index=False)
    
    print(f"\nDone! Evaluation finished. Generated {len(pred_df)} rows in {csv_path}")
    print(pred_df.head(10))

if __name__ == "__main__":
    evaluate()

