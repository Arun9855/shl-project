class DomainBalancer:
    def __init__(self):
        pass

    def balance(self, candidates, expected_domains, target_size=10):
        if not expected_domains or not candidates:
            return candidates[:target_size]
            
        # Ensure at least one test from each expected domain is present in top N
        final_list = []
        domain_representation = {domain: 0 for domain in expected_domains}
        
        # First pass: collect best match for each required domain
        used_ids = set()
        for domain in expected_domains:
            for c in candidates:
                if c['id'] not in used_ids and domain in set(c['test_type']):
                    final_list.append(c)
                    used_ids.add(c['id'])
                    domain_representation[domain] += 1
                    break
        
        # Second pass: fill the rest of the slots up to target_size based on rank
        for c in candidates:
            if len(final_list) >= target_size:
                break
            if c['id'] not in used_ids:
                final_list.append(c)
                used_ids.add(c['id'])
                
        # Return sorted by original rank if we want, or keep the forced domains at top.
        # Actually, keeping it by their rerank_score is best:
        final_list.sort(key=lambda x: x.get('rerank_score', 0), reverse=True)
        return final_list[:target_size]

if __name__ == "__main__":
    db = DomainBalancer()
    docs = [
        {"id": 1, "test_type": ["Knowledge & Skills"], "rerank_score": 0.9},
        {"id": 2, "test_type": ["Knowledge & Skills"], "rerank_score": 0.8},
        {"id": 3, "test_type": ["Personality & Behavior"], "rerank_score": 0.3}
    ]
    res = db.balance(docs, ["Knowledge & Skills", "Personality & Behavior"], target_size=2)
    print("Balanced Results:", [r['id'] for r in res])  # Expected: [1, 3] regardless of 3's rank
