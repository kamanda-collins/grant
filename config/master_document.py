"""
Configuration module for the Grant Auto-Application System.
Handles master document parsing and application settings.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os

class CompanyInfo(BaseModel):
    """Company/Organization information from master document."""
    name: str = "KamandaLabs"
    description: str = "Uganda's first automated environmental-compliance platform"
    industry: str = "Environmental Technology / GreenTech"
    stage: str = "Early Stage / MVP"
    location: str = "Uganda"
    website: str = "https://kamandalabs.me"
    demo_url: str = "https://nema.kamandalabs.me"
    
class FounderInfo(BaseModel):
    """Founder/Team information."""
    name: str = "Kamanda Collins"
    title: str = "Founder"
    email: str = "kamandacollins004@gmail.com"
    phone: str = "+256 771 594 776"
    background: str = "Final-year Petroleum and Mineral Geoscience student at Nkumba University"
    linkedin: Optional[str] = None
    
class FinancialInfo(BaseModel):
    """Financial and funding information."""
    current_revenue: str = "No revenue currently"
    funding_amount_requested: str = "$7,500"
    funding_type: str = "Non-dilutive"
    use_of_funds: List[str] = [
        "Complete cloud and deployment infrastructure",
        "Pay for NEMA legal review and formal environmental validation", 
        "Host user onboarding workshops",
        "Cover basic tech operations (internet, computer maintenance)",
        "Convert pilot users into paid subscriptions by Q4 2025"
    ]
    
class TractionInfo(BaseModel):
    """Traction and milestones."""
    key_metrics: List[str] = [
        "1 highly engaged consulting lead",
        "Multiple outreach responses from environmental consultant network",
        "Tools deployed and active at nema.kamandalabs.me",
        "Uganda Clays accepted pilot letter and project proposal",
        "Rwenzori Green and NEMA expressed interest in advising"
    ]
    timeline: Dict[str, str] = {
        "Jun 2024": "Beta tool live at nema.kamandalabs.me",
        "Jul 2024": "Streamlined UI + demo video",
        "Jul 2024": "6 consultant replies, 1 highly engaged lead",
        "Jul 2024": "Uganda Clays accepted pilot",
        "Jul 2024": "Rwenzori Green & NEMA advisory support"
    }

class ProblemSolution(BaseModel):
    """Problem statement and solution details."""
    problem_statement: str = "ESIA wetland mapping delays averaging 21-28 days, with 34 mining/infrastructure projects stalled yearly in Uganda"
    solution_description: str = "Automated environmental-compliance platform that slashes ESIA preparation time from 4 weeks to 3 days"
    unique_advantage: List[str] = [
        "Founder-Builder-User: Geoscientist, developer, and early tester",
        "Offline-friendly tech built for Ugandan connectivity realities", 
        "No competitors offering auto-generated Word+PNG+Markdown reports",
        "Tied to national needs: NEMA compliance, extractives growth"
    ]

class MasterDocument(BaseModel):
    """Complete master document structure."""
    company: CompanyInfo = CompanyInfo()
    founder: FounderInfo = FounderInfo()
    financial: FinancialInfo = FinancialInfo()
    traction: TractionInfo = TractionInfo()
    problem_solution: ProblemSolution = ProblemSolution()
    
    executive_summary: str = """KamandaLabs is Uganda's first automated environmental-compliance platform, built by Kamanda Collins — a final-year Petroleum and Mineral Geoscience student at Nkumba University — to slash ESIA preparation time from 4 weeks to 3 days. While we currently have no revenue, we have strong traction with 1 highly engaged consulting lead, multiple outreach responses, and tools already deployed. We are seeking $7,500 in non-dilutive funding."""
    
    roadmap_6_months: Dict[str, str] = {
        "Month 1": "Final pilot client - Full field use, paid test",
        "Month 2": "NEMA lawyer engagement - Legal compliance report", 
        "Month 3": "Feature upgrade (alerts, UI) - Integrated WhatsApp/SMS reminders",
        "Month 4": "Kenya & Rwanda outreach - NGOs onboarded (2)",
        "Month 5": "Video & referral campaign - 15 new signups",
        "Month 6": "First MRR ($250+) - 2-3 recurring paid clients"
    }

class ApplicationConfig(BaseModel):
    """Configuration for application process."""
    max_applications_per_day: int = 5
    delay_between_applications: int = 30  # seconds
    timeout_per_form: int = 120  # seconds
    retry_attempts: int = 3
    log_level: str = "INFO"
    
    # Filtering criteria
    funding_range_min: int = 1000
    funding_range_max: int = 50000
    target_industries: List[str] = ["tech", "greentech", "environmental", "startup", "early-stage"]
    exclude_keywords: List[str] = ["enterprise", "series-a", "late-stage"]

def load_master_document(file_path: str = "config/master_document.json") -> MasterDocument:
    """Load master document from JSON file or return default."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
            return MasterDocument(**data)
        else:
            # Create default master document
            master_doc = MasterDocument()
            save_master_document(master_doc, file_path)
            return master_doc
    except Exception as e:
        print(f"Error loading master document: {e}")
        return MasterDocument()

def save_master_document(master_doc: MasterDocument, file_path: str = "config/master_document.json"):
    """Save master document to JSON file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(master_doc.dict(), f, indent=2)

def load_config(file_path: str = "config/app_config.json") -> ApplicationConfig:
    """Load application configuration."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
            return ApplicationConfig(**data)
        else:
            config = ApplicationConfig()
            save_config(config, file_path)
            return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return ApplicationConfig()

def save_config(config: ApplicationConfig, file_path: str = "config/app_config.json"):
    """Save application configuration."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(config.dict(), f, indent=2)
