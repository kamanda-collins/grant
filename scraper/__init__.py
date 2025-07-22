"""
Web scraper module for discovering grant and incubator opportunities.
"""

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Dict, Any
import time
import logging
from urllib.parse import urljoin, urlparse
import re

class OpportunityScraperError(Exception):
    """Custom exception for scraper errors."""
    pass

class Opportunity:
    """Represents a grant or incubator opportunity."""
    
    def __init__(self, title: str, url: str, description: str = "", 
                 deadline: str = "", funding_amount: str = "", 
                 eligibility: str = "", source: str = ""):
        self.title = title
        self.url = url
        self.description = description
        self.deadline = deadline
        self.funding_amount = funding_amount
        self.eligibility = eligibility
        self.source = source
        self.discovered_at = time.strftime("%Y-%m-%d %H:%M:%S")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'url': self.url,
            'description': self.description,
            'deadline': self.deadline,
            'funding_amount': self.funding_amount,
            'eligibility': self.eligibility,
            'source': self.source,
            'discovered_at': self.discovered_at
        }

class OpportunityScraper:
    """Main scraper class for finding grant and incubator opportunities."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.opportunities = []
        
        # Common grant/incubator sources
        self.sources = [
            {
                'name': 'Grants.gov',
                'url': 'https://www.grants.gov/search-grants',
                'type': 'government'
            },
            {
                'name': 'AngelList',
                'url': 'https://angel.co/accelerators',
                'type': 'incubator'
            },
            {
                'name': 'Techstars',
                'url': 'https://www.techstars.com/accelerators',
                'type': 'incubator'
            },
            {
                'name': 'Y Combinator',
                'url': 'https://www.ycombinator.com/apply',
                'type': 'incubator'
            },
            {
                'name': 'SBIR',
                'url': 'https://www.sbir.gov/opportunities',
                'type': 'government'
            }
        ]
    
    def setup_driver(self):
        """Setup Selenium WebDriver."""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            logging.info("WebDriver setup successful")
        except Exception as e:
            logging.error(f"Failed to setup WebDriver: {e}")
            raise OpportunityScraperError(f"WebDriver setup failed: {e}")
    
    def close_driver(self):
        """Close WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def discover_opportunities(self, keywords: List[str] = None, 
                             max_opportunities: int = 50) -> List[Opportunity]:
        """
        Main method to discover grant and incubator opportunities.
        
        Args:
            keywords: List of keywords to search for (e.g., ['tech', 'environment', 'startup'])
            max_opportunities: Maximum number of opportunities to return
            
        Returns:
            List of Opportunity objects
        """
        if keywords is None:
            keywords = ['tech', 'startup', 'environmental', 'innovation']
        
        self.opportunities = []
        
        try:
            self.setup_driver()
            
            # Scrape from each source
            for source in self.sources:
                try:
                    logging.info(f"Scraping {source['name']}...")
                    if source['name'] == 'Grants.gov':
                        self._scrape_grants_gov(keywords)
                    elif source['name'] == 'AngelList':
                        self._scrape_angellist()
                    elif source['name'] == 'Techstars':
                        self._scrape_techstars()
                    elif source['name'] == 'Y Combinator':
                        self._scrape_ycombinator()
                    elif source['name'] == 'SBIR':
                        self._scrape_sbir(keywords)
                        
                    # Add delay between sources
                    time.sleep(2)
                    
                except Exception as e:
                    logging.error(f"Error scraping {source['name']}: {e}")
                    continue
            
        finally:
            self.close_driver()
        
        # Filter and return top opportunities
        filtered_opportunities = self._filter_opportunities(keywords)
        return filtered_opportunities[:max_opportunities]
    
    def _scrape_grants_gov(self, keywords: List[str]):
        """Scrape opportunities from Grants.gov."""
        try:
            search_url = "https://www.grants.gov/web/grants/search-grants.html"
            self.driver.get(search_url)
            
            # Wait for page load and search for opportunities
            time.sleep(3)
            
            # Look for grant listings (this is a simplified example)
            grant_elements = self.driver.find_elements(By.CLASS_NAME, "grant-title")
            
            for element in grant_elements[:10]:  # Limit to 10 per source
                try:
                    title = element.text.strip()
                    url = element.get_attribute('href') or search_url
                    
                    opportunity = Opportunity(
                        title=title,
                        url=url,
                        source="Grants.gov",
                        description="Government grant opportunity"
                    )
                    self.opportunities.append(opportunity)
                    
                except Exception as e:
                    logging.warning(f"Error parsing grant element: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error scraping Grants.gov: {e}")
    
    def _scrape_techstars(self):
        """Scrape Techstars accelerator programs."""
        try:
            url = "https://www.techstars.com/accelerators"
            self.driver.get(url)
            time.sleep(3)
            
            # Look for accelerator programs
            program_elements = self.driver.find_elements(By.CSS_SELECTOR, ".program-card, .accelerator-card")
            
            for element in program_elements[:5]:
                try:
                    title_elem = element.find_element(By.TAG_NAME, "h3")
                    title = title_elem.text.strip()
                    
                    link_elem = element.find_element(By.TAG_NAME, "a")
                    url = link_elem.get_attribute('href')
                    
                    opportunity = Opportunity(
                        title=f"Techstars {title}",
                        url=url,
                        source="Techstars",
                        description="Techstars accelerator program"
                    )
                    self.opportunities.append(opportunity)
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            logging.error(f"Error scraping Techstars: {e}")
    
    def _scrape_ycombinator(self):
        """Scrape Y Combinator application info."""
        try:
            url = "https://www.ycombinator.com/apply"
            
            opportunity = Opportunity(
                title="Y Combinator Startup Accelerator",
                url=url,
                source="Y Combinator",
                description="Leading startup accelerator program",
                funding_amount="$500,000",
                deadline="Check website for application deadlines"
            )
            self.opportunities.append(opportunity)
            
        except Exception as e:
            logging.error(f"Error adding Y Combinator: {e}")
    
    def _scrape_angellist(self):
        """Scrape AngelList for accelerators."""
        try:
            # AngelList doesn't allow easy scraping, so we'll add known programs
            known_programs = [
                {
                    'title': 'AngelList Accelerator Programs',
                    'url': 'https://angel.co/accelerators',
                    'description': 'Various startup accelerator programs'
                }
            ]
            
            for program in known_programs:
                opportunity = Opportunity(
                    title=program['title'],
                    url=program['url'],
                    source="AngelList",
                    description=program['description']
                )
                self.opportunities.append(opportunity)
                
        except Exception as e:
            logging.error(f"Error adding AngelList programs: {e}")
    
    def _scrape_sbir(self, keywords: List[str]):
        """Scrape SBIR opportunities."""
        try:
            url = "https://www.sbir.gov/opportunities"
            
            # Add SBIR as a known opportunity
            opportunity = Opportunity(
                title="SBIR/STTR Small Business Innovation Research",
                url=url,
                source="SBIR",
                description="Federal R&D funding for small businesses",
                funding_amount="Phase I: $50,000-$300,000, Phase II: $750,000-$1,500,000"
            )
            self.opportunities.append(opportunity)
            
        except Exception as e:
            logging.error(f"Error adding SBIR: {e}")
    
    def _filter_opportunities(self, keywords: List[str]) -> List[Opportunity]:
        """Filter opportunities based on keywords and relevance."""
        if not keywords:
            return self.opportunities
        
        filtered = []
        keywords_lower = [k.lower() for k in keywords]
        
        for opp in self.opportunities:
            # Check if any keyword appears in title or description
            text_to_search = f"{opp.title} {opp.description}".lower()
            
            if any(keyword in text_to_search for keyword in keywords_lower):
                filtered.append(opp)
            # Also include all opportunities if they're from reputable sources
            elif opp.source in ['Y Combinator', 'Techstars']:
                filtered.append(opp)
        
        return filtered

def discover_opportunities(keywords: List[str] = None, max_results: int = 20) -> List[Dict[str, Any]]:
    """
    Main function to discover grant and incubator opportunities.
    
    Args:
        keywords: Search keywords
        max_results: Maximum number of results to return
        
    Returns:
        List of opportunity dictionaries
    """
    scraper = OpportunityScraper(headless=True)
    
    try:
        opportunities = scraper.discover_opportunities(keywords, max_results)
        return [opp.to_dict() for opp in opportunities]
    except Exception as e:
        logging.error(f"Error in discover_opportunities: {e}")
        return []
    finally:
        scraper.close_driver()

if __name__ == "__main__":
    # Test the scraper
    logging.basicConfig(level=logging.INFO)
    keywords = ['tech', 'startup', 'environmental']
    opportunities = discover_opportunities(keywords, 10)
    
    print(f"Found {len(opportunities)} opportunities:")
    for opp in opportunities:
        print(f"- {opp['title']} ({opp['source']})")
        print(f"  URL: {opp['url']}")
        print()
