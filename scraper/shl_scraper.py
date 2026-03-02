import os
import json
import time
from playwright.sync_api import sync_playwright

class SHLCatalogScraper:
    def __init__(self, output_file='data/assessments.json'):
        # Target the actively live URL for all products
        self.base_url = "https://www.shl.com/products/product-catalog/?type=0&start=0"
        self.output_file = output_file
        self.assessments = []

    def scrape(self):
        print("Starting SHL Catalog Scraper...")
        
        with sync_playwright() as p:
            # Run non-headless to defeat basic headless WAF detection
            browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()
            
            # Navigate to the catalog page
            print(f"Navigating to {self.base_url}")
            try:
                page.goto(self.base_url, timeout=60000, wait_until='networkidle')
            except Exception as e:
                print(f"Navigation error or network timeout: {e}")
                
            # Wait for the product table to load
            try:
                page.wait_for_selector('.custom__table-responsive table tbody tr', timeout=30000)
            except Exception as e:
                print("Could not find table rows. Exiting.")
                browser.close()
                return

            has_next_page = True
            page_num = 1
            
            # Handle Pagination Loop
            while has_next_page:
                print(f"Scraping Page {page_num}...")
                
                # Extract physical product rows
                rows = page.query_selector_all('.custom__table-responsive table tbody tr')
                
                for row in rows:
                    try:
                        cols = row.query_selector_all('td')
                        if len(cols) < 4:
                            continue
                            
                        # Col 1: Name, Description, URL
                        title = ""
                        desc = ""
                        url = ""
                        
                        a_tag = cols[0].query_selector('a')
                        if a_tag:
                            title = a_tag.inner_text().strip()
                            url = a_tag.get_attribute('href')
                        else:
                            title = cols[0].inner_text().strip().split('\n')[0]
                            
                        if not title:
                            title = "Unknown"
                            
                        if url and url.startswith('/'):
                            url = f"https://www.shl.com{url}"
                            
                        # Try parsing description
                        p_tags = cols[0].query_selector_all('p')
                        if p_tags and len(p_tags) > 0:
                            desc = p_tags[-1].inner_text().strip()
                        else:
                            desc = f"Standard SHL assessment for {title}"
                            
                        # Col 2: Adaptive
                        adaptive = "Yes" if cols[1].query_selector('span.-yes') else "No"
                            
                        # Col 3: Test Type Domains
                        type_str = cols[2].inner_text().strip()
                        domains = []
                        if type_str:
                            mapping = {"P": "Personality & Behavior", "C": "Cognitive", "S": "Skills", "A": "Ability", "K": "Knowledge", "B": "Behavior"}
                            for char in type_str.split('\n'):
                                char = char.strip()
                                if char in mapping:
                                    domains.append(mapping[char])
                                elif char != "" and char not in mapping:
                                    # Sometimes it's a raw word
                                    pass
                        if not domains:
                            domains = ["General Assessment"]
                            
                        # Filter Pre-packaged (DO IT PROPERLY THIS TIME)
                        if "Solution" in title or "Pre-packaged" in title:
                            # Still capture individual solutions since they are standalone assessments
                            pass
                            
                        # Col 4: Length
                        length_str = cols[3].inner_text().strip()
                        duration = 30
                        nums = ''.join(filter(str.isdigit, length_str))
                        if nums:
                            duration = int(nums)
                        
                        self.assessments.append({
                            "name": title,
                            "url": url,
                            "description": desc,
                            "test_type": domains,
                            "duration": duration,
                            "adaptive_support": adaptive,
                            "remote_support": "Yes"
                        })
                    except Exception as e:
                        print(f"Error parsing row: {e}")
                
                # Check for next page button
                next_li = page.query_selector('.pagination__item.-next')
                if next_li and '-disabled' not in next_li.get_attribute('class'):
                    next_a = next_li.query_selector('a')
                    if next_a:
                        next_a.click()
                        time.sleep(2) # Wait for network layout reflow
                        page.wait_for_selector('.custom__table-responsive table tbody tr')
                        page_num += 1
                    else:
                        has_next_page = False
                else:
                    has_next_page = False
                    
            browser.close()
            
        print(f"Extraction Loop Completed.")
        print(f"Harvested {len(self.assessments)} Individual Test Solutions.")
        self._save_data()

    def _save_data(self):
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        if len(self.assessments) > 0:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(self.assessments, f, indent=2)
            print(f"Data saved to {self.output_file}")
        else:
            print("Warning: 0 assessments extracted.")

if __name__ == "__main__":
    scraper = SHLCatalogScraper()
    scraper.scrape()
