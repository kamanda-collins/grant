def main():
    st.set_page_config(
        page_title="Grant Application Bot", 
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 Grant Application Bot")
    st.markdown("*Automated grant and accelerator applications for KamandaLabs*")
    
    # Initialize bot
    if 'bot' not in st.session_state:
        st.session_state.bot = GrantApplicationBot()
    
    bot = st.session_state.bot
    
    # Sidebar for master data management
    with st.sidebar:
        st.header("📄 Master Document")
        
        # Option 1: Upload JSON file
        uploaded_file = st.file_uploader("Upload Master Document JSON", type=['json'])
        if uploaded_file:
            json_content = uploaded_file.read().decode('utf-8')
            if bot.load_master_data(json_data=json_content):
                st.success("✅ Master data loaded from file!")
        
        # Option 2: Paste JSON directly
        st.markdown("**Or paste JSON directly:**")
        json_input = st.text_area("Master Document JSON", height=200, placeholder="""{
    "company_info": {
        "name": "KamandaLabs",
        "tagline": "Building Africa's compliance ecosystem",
        ...
    },
    "founder": {...},
    ...
}""")
        
        if st.button("Load JSON Data") and json_input.strip():
            if bot.load_master_data(json_data=json_input):
                st.success("✅ Master data loaded!")
        
        # Display loaded data summary
        if bot.master_data:
            st.markdown("**Loaded Data:**")
            if "company_info" in bot.master_data:
                st.write(f"• **Company:** {bot.master_data['company_info'].get('name', 'N/A')}")
            if "founder" in bot.master_data:
                st.write(f"• **Founder:** {bot.master_data['founder'].get('name', 'N/A')}")
            st.write(f"• **Data sections:** {len(bot.master_data)} sections")
    
    # Main content area
    if not bot.master_data:
        st.warning("⚠️ Please load your master document JSON in the sidebar to continue.")
        st.markdown("""
        ### Getting Started
        1. **Upload** your master document JSON file, or **paste** the JSON content in the sidebar
        2. **Review** the filtered opportunities below
        3. **Select** opportunities to apply to
        4. **Run** the application bot (dry run first recommended)
        """)
        
        # Show sample JSON structure
        with st.expander("📋 Expected JSON Structure"):
            st.code("""{
    "company_info": {
        "name": "Your Company Name",
        "tagline": "Your tagline",
        "industry": "Your industry",
        "location": "Your location",
        "website": "yourwebsite.com",
        "founded": "2024"
    },
    "founder": {
        "name": "Founder Name", 
        "title": "CEO/Founder",
        "education": "Educational background",
        "experience": "Work experience"
    },
    "executive_summary": "Brief company description...",
    "problem_statement": "Problem you're solving...",
    "solution": "Your solution...",
    "products": [...],
    "financials": {
        "funding_sought": "50000-200000",
        "revenue": "Pre-revenue",
        "use_of_funds": [...]
    },
    "traction": [...],
    "target_market": [...],
    "tech_stack": {...},
    "impact": {...}
}""", language="json")
        return
    
    # Opportunities Dashboard
    st.header("🎯 Relevant Opportunities")
    
    # Filter opportunities
    filtered_opportunities = bot.filter_opportunities_by_relevance(bot.opportunities)
    
    # Display opportunities in cards
    cols = st.columns(2)
    selected_opportunities = []
    
    for i, opp in enumerate(filtered_opportunities[:10]):  # Show top 10
        col = cols[i % 2]
        
        with col:
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin: 10px 0;">
                    <h4>{opp['name']}</h4>
                    <p><strong>Type:</strong> {opp.get('type', 'N/A')}</p>
                    <p><strong>Focus:</strong> {', '.join(opp.get('focus', []))}</p>
                    <p><strong>Deadline:</strong> {opp['deadline']}</p>
                    <p><strong>Relevance Score:</strong> {opp.get('relevance_score', 0)}/10</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.checkbox(f"Select {opp['name']}", key=f"select_{i}"):
                    selected_opportunities.append(opp)
    
    # Application Actions
    if selected_opportunities:
        st.header("🤖 Application Bot")
        
        col1, col2 = st.columnsimport streamlit as st
import pandas as pd
import json
import requests
from datetime import datetime, timedelta
import re
from fuzzywuzzy import fuzz, process
from typing import Dict, List, Any, Optional
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Scraped opportunities data
TOP_OPPS = [
    {
        "name": "Google for Startups Accelerator Africa – Climate",
        "url": "https://startup.google.com/programs/accelerator-africa/",
        "apply_link_selector": "a[href*='apply'][href*='climate']",
        "deadline": "2025-08-30",
        "type": "Accelerator",
        "focus": ["Climate", "Technology", "Africa"]
    },
    {
        "name": "UNDP-AFCIA (Climate Innovation)",
        "url": "https://www.africaclimateinnovation.org/apply",
        "apply_link_selector": "a[href*='typeform']",
        "deadline": "2025-09-15",
        "type": "Grant",
        "focus": ["Climate Innovation", "Development"]
    },
    {
        "name": "Antler Nairobi – Residency Cohort",
        "url": "https://www.antler.co/apply/nairobi",
        "apply_link_selector": "a[href*='forms.gle']",
        "deadline": "2025-08-10",
        "type": "Accelerator",
        "focus": ["Early Stage", "Africa"]
    },
    {
        "name": "Future Africa Seed Fund",
        "url": "https://future.africa/seedfund",
        "apply_link_selector": "a[href*='seedfund-apply']",
        "deadline": "2025-09-01",
        "type": "Seed Funding",
        "focus": ["African Startups", "Technology"]
    },
    {
        "name": "GSMA Innovation Fund – Climate Resilience",
        "url": "https://www.gsma.com/mobilefordevelopment/innovation-fund",
        "apply_link_selector": "a[href*='apply'][href*='climate']",
        "deadline": "2025-08-25",
        "type": "Innovation Fund",
        "focus": ["Climate Resilience", "Mobile Technology"]
    },
    {
        "name": "FSD Africa – RegTech for Climate",
        "url": "https://fsdafrica.org/programmes/regtech-for-climate/",
        "apply_link_selector": "a[href*='typeform']",
        "deadline": "2025-08-31",
        "type": "Grant",
        "focus": ["RegTech", "Climate", "Financial Services"]
    },
    {
        "name": "Mining Indaba "Investment Battlefield"",
        "url": "https://www.miningindaba.com/investment-battlefield",
        "apply_link_selector": "a[href*='apply']",
        "deadline": "2025-10-01",
        "type": "Competition",
        "focus": ["Mining", "Investment", "Africa"]
    },
    {
        "name": "Shell LiveWIRE Uganda",
        "url": "https://shell.com.ug/livewire",
        "apply_link_selector": "a[href*='livewire-uganda']",
        "deadline": "2025-08-20",
        "type": "Entrepreneurship Program",
        "focus": ["Uganda", "Energy", "Entrepreneurship"]
    },
    {
        "name": "Total Energies Startupper Challenge",
        "url": "https://startupper.totalenergies.com",
        "apply_link_selector": "a[href*='apply'][href*='uganda']",
        "deadline": "2025-09-05",
        "type": "Competition",
        "focus": ["Energy", "Uganda", "Innovation"]
    },
    {
        "name": "ClimateLaunchpad East Africa",
        "url": "https://climatelaunchpad.org/eastafrica",
        "apply_link_selector": "a[href*='apply']",
        "deadline": "2025-08-15",
        "type": "Accelerator",
        "focus": ["Climate", "East Africa", "Cleantech"]
    }
]

class GrantApplicationBot:
    def __init__(self):
        self.master_data = None
        self.opportunities = TOP_OPPS
        self.field_mappings = self.create_field_mappings()
        
    def load_master_data(self, file_path: str = None, json_data: str = None) -> Dict[str, Any]:
        """Load master document from JSON file or JSON string"""
        try:
            if json_data:
                self.master_data = json.loads(json_data)
            elif file_path and os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.master_data = json.load(f)
            else:
                st.error("Please provide either a file path or JSON data")
                return None
            
            logger.info("Master data loaded successfully")
            return self.master_data
        except Exception as e:
            logger.error(f"Error loading master data: {e}")
            st.error(f"Error loading master data: {e}")
            return None
    def create_field_mappings(self) -> Dict[str, List[str]]:
        """
        Map common form field labels to paths in master_profile.json
        """
        return {
            "company_name": ["company_info", "name"],
            "company_tagline": ["company_info", "tagline"],
            "founder_name": ["founder", "name"],
            "founder_email": ["founder", "email"],
            "problem": ["problem_statement"],
            "solution": ["solution"],
            "funding_amount": ["financials", "funding_sought"],
            "use_of_funds": ["financials", "use_of_funds"],
            "website": ["company_info", "website"],
            "location": ["company_info", "location"],
            "pitch_deck": ["urls", "pitch_deck"],
            "linkedin": ["founder", "linkedin"],
            "phone": ["founder", "phone"],
            "dob": ["founder", "dob"],
            "gender": ["founder", "gender"],
            "nationality": ["founder", "nationality"],
        }

    def get_value(self, path: List[str]) -> Any:
        """Helper to safely traverse nested dict"""
        d = self.master_data
        for key in path:
            d = d.get(key, {})
        return d if d != {} else None

    def fill_form_field(self, label: str) -> Optional[str]:
        """Return value for a given label using fuzzy match + mapping"""
        label_clean = re.sub(r"[^\w\s]", "", label.lower())
        best, score = process.extractOne(
            label_clean, self.field_mappings.keys(), scorer=fuzz.partial_ratio
        )
        if score < 70:
            return None
        return self.get_value(self.field_mappings[best])

    def filter_opportunities_by_relevance(self, opps: List[Dict]) -> List[Dict]:
        """Boost opportunities whose focus tags intersect with our keywords"""
        keywords = set(
            [
                "climate",
                "mining",
                "compliance",
                "govtech",
                "africa",
                "energy",
                "environment",
                "regtech",
                "saas",
            ]
        )
        enriched = []
        for opp in opps:
            focus_set = {f.lower() for f in opp.get("focus", [])}
            overlap = len(keywords & focus_set)
            opp["relevance_score"] = min(10, 2 + overlap * 2)
            enriched.append(opp)
        return sorted(enriched, key=lambda x: x["relevance_score"], reverse=True)

    def apply_to_opportunity(self, opp: Dict, dry_run: bool = True) -> Dict:
        """Visit apply link, auto-fill, and optionally submit"""
        logger.info(f"{'[DRY-RUN]' if dry_run else '[LIVE]'} Processing {opp['name']}")
        opts = Options()
        opts.add_argument("--headless")
        driver = webdriver.Chrome(options=opts)
        try:
            driver.get(opp["url"])
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Example: locate text inputs and fill
            inputs = driver.find_elements(By.TAG_NAME, "input")
            filled = 0
            for inp in inputs:
                label = inp.get_attribute("placeholder") or inp.get_attribute("name") or ""
                value = self.fill_form_field(label)
                if value and inp.is_enabled() and inp.get_attribute("type") != "file":
                    inp.clear()
                    inp.send_keys(str(value))
                    filled += 1

            # Handle file uploads (pitch deck etc.)
            file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            for fi in file_inputs:
                label = fi.get_attribute("name") or ""
                if "pitch" in label.lower():
                    deck_path = self.get_value(["urls", "pitch_deck"])
                    if deck_path and os.path.exists(deck_path):
                        fi.send_keys(os.path.abspath(deck_path))

            status = {
                "name": opp["name"],
                "filled_fields": filled,
                "dry_run": dry_run,
                "status": "success",
                "url": opp["url"],
            }

            if not dry_run:
                submit_btn = driver.find_element(
                    By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"
                )
                submit_btn.click()
                status["submitted"] = True
            else:
                status["submitted"] = False

            return status
        except Exception as e:
            logger.exception(e)
            return {"name": opp["name"], "status": "error", "error": str(e)}
        finally:
            driver.quit()


# ---------------- MAIN UI (CONTINUED) ----------------
def main():
    st.set_page_config(
        page_title="Grant Application Bot",
        page_icon="🚀",
        layout="wide",
    )

    st.title("🚀 KamandaLabs Grant-Bot")
    st.markdown("*Auto-fill & submit climate / mining / gov-tech grants*")

    if "bot" not in st.session_state:
        st.session_state.bot = GrantApplicationBot()
    bot = st.session_state.bot

    # Sidebar loader (unchanged)
    with st.sidebar:
        st.header("📄 Master Document")
        uploaded_file = st.file_uploader("Upload JSON", type=["json"])
        if uploaded_file:
            json_content = uploaded_file.read().decode("utf-8")
            bot.load_master_data(json_data=json_content)
            st.success("✅ Master data loaded from file!")

        json_input = st.text_area(
            "Or paste JSON",
            height=200,
            placeholder='{"company_info": {...}, "founder": {...}, ...}',
        )
        if st.button("Load JSON") and json_input.strip():
            bot.load_master_data(json_data=json_input)
            st.success("✅ Master data loaded!")

    if not bot.master_data:
        st.warning("⚠️ Load your master_profile.json in the sidebar first.")
        return

    # Opportunities Dashboard
    st.header("🎯 Opportunities")
    filtered = bot.filter_opportunities_by_relevance(bot.opportunities)

    selected = st.multiselect(
        "Select to apply:",
        options=filtered,
        format_func=lambda x: f"{x['name']} — {x['deadline']} ({x['type']})",
    )

    if selected:
        dry = st.checkbox("Dry-run (preview only)", value=True)
        if st.button("🚀 Apply to selected"):
            results = []
            progress = st.progress(0)
            for i, opp in enumerate(selected):
                progress.progress((i + 1) / len(selected))
                res = bot.apply_to_opportunity(opp, dry_run=dry)
                results.append(res)
            st.success("Done!")
            st.json(results)


if __name__ == "__main__":
    main()