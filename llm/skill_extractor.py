import os
import json
import google.generativeai as genai

class SkillExtractor:
    def __init__(self, api_key=None):
        # Allow passing API key or reading from env. In dev without key, this returns deterministic stubs.
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            print("WARNING: Gemini API Key not set. Skill Extractor will use heuristics.")

    def extract(self, query_text):
        if not self.model:
            return self._heuristic_extract(query_text)
            
        prompt = f"""
        Analyze the following Job Description or Hiring Query. Extract the required Skills and identify the most relevant Assessment Domains.
        
        Possible Domains to choose from: 
        ["Knowledge & Skills", "Personality & Behavior", "Cognitive", "Situational Judgment", "Language"]
        
        Query:
        "{query_text}"
        
        Return ONLY a strict JSON object exactly matching this format:
        {{
            "hard_skills": ["skill1", "skill2"],
            "soft_skills": ["skill3", "skill4"],
            "expected_domains": ["domain1", "domain2"]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Find JSON block
            text = response.text
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != 0:
                return json.loads(text[start:end])
            return self._heuristic_extract(query_text)
        except Exception as e:
            print(f"LLM Extraction failed: {e}")
            return self._heuristic_extract(query_text)

    def _heuristic_extract(self, text):
        # Fallback if API fails or no key
        text_lower = text.lower()
        hard = []
        soft = []
        domains = set(["Knowledge & Skills"])
        
        if "java" in text_lower: hard.append("Java")
        if "python" in text_lower: hard.append("Python")
        if "sql" in text_lower: hard.append("SQL")
        
        if "collaborat" in text_lower or "team" in text_lower: 
            soft.append("Collaboration")
            domains.add("Personality & Behavior")
        if "lead" in text_lower:
            soft.append("Leadership")
            domains.add("Personality & Behavior")
        if "reason" in text_lower or "cognitive" in text_lower:
            domains.add("Cognitive")
            
        return {
            "hard_skills": hard,
            "soft_skills": soft,
            "expected_domains": list(domains)
        }

if __name__ == "__main__":
    extr = SkillExtractor()
    print(extr.extract("Need a Java developer who is good in collaborating with external teams."))
