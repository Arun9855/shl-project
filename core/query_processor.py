import re
import urllib.request as urllib2
from bs4 import BeautifulSoup

class QueryProcessor:
    def __init__(self):
        pass

    def is_url(self, text):
        return text.startswith("http://") or text.startswith("https://")

    def fetch_url_text(self, url):
        try:
            req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            html = urllib2.urlopen(req, timeout=10).read().decode('utf-8')
            soup = BeautifulSoup(html, "html.parser")
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text(separator=' ')
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text[:2000] # Limit to 2000 chars for LLM context
        except Exception as e:
            print(f"Error fetching JD URL {url}: {e}")
            return ""

    def process(self, raw_input):
        raw_input = raw_input.strip()
        
        # Check if the entire query is just a URL
        if self.is_url(raw_input):
            jd_text = self.fetch_url_text(raw_input)
            if jd_text:
                return f"Job Description URL Content:\n{jd_text}"
        
        # Extract any URL embedded inside the text
        url_match = re.search(r'(https?://[^\s]+)', raw_input)
        if url_match:
            jd_url = url_match.group(1)
            jd_text = self.fetch_url_text(jd_url)
            raw_input = raw_input.replace(jd_url, "")
            raw_input += f" \n[Extracted JD Content: {jd_text}]"
            
        # Normalize casing and basic noise
        normalized = re.sub(r'\s+', ' ', raw_input).strip()
        return normalized

if __name__ == "__main__":
    qp = QueryProcessor()
    res = qp.process("Need a Java developer who is good in collaborating with external teams.")
    print("Processed:", res)
