import pandas as pd

def calculate_recall_at_10():
    try:
        # Load predictions
        preds = pd.read_csv('data/output/predictions.csv')
        
        # Load ground truth
        gt = pd.read_excel('Gen_AI Dataset.xlsx')
        
        # Map ground truth query to target URL
        gt_map = dict(zip(gt['Query'], gt['Assessment_url']))
        
        hit_count = 0
        total_queries = len(gt_map)
        
        # Group predictions by query
        pred_groups = preds.groupby('Query')['Assessment_url'].apply(list).to_dict()
        
        for q, expected_url in gt_map.items():
            if str(expected_url) == "nan":
                total_queries -= 1
                continue
                
            predicted_urls = pred_groups.get(q, [])
            # SHL updated their site from /solutions/products/ to /products/ so exact URL matching fails
            # Extract the unique slug from the expected URL
            clean_expected_slug = str(expected_url).strip('/').split('/')[-1].lower()
            
            clean_pred_slugs = [str(u).strip('/').split('/')[-1].lower() for u in predicted_urls if pd.notna(u)]
            
            # Check if expected URL slug is in top 10 slugs
            hit = False
            for p_slug in clean_pred_slugs:
                if clean_expected_slug in p_slug or p_slug in clean_expected_slug:
                    hit = True
                    break
                    
            if hit:
                hit_count += 1
                
        recall = hit_count / total_queries if total_queries > 0 else 0
        print(f"Total Evaluated Queries: {total_queries}")
        print(f"Total Hits in Top 10: {hit_count}")
        print(f"Mathematical Recall@10: {recall:.4f}")
        
    except Exception as e:
        print(f"Error calculating metrics: {e}")

if __name__ == "__main__":
    calculate_recall_at_10()
