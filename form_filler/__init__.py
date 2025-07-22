"""
Form filling module for automatically filling grant and incubator application forms.
"""

import time
import logging
from typing import Dict, List, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
from config.master_document import MasterDocument, load_master_document

class FormFillerError(Exception):
    """Custom exception for form filling errors."""
    pass

class FormField:
    """Represents a form field and its mapping to master document data."""
    
    def __init__(self, element, field_type: str, label: str = ""):
        self.element = element
        self.field_type = field_type  # text, email, textarea, select, radio, checkbox
        self.label = label
        self.is_required = self._check_if_required()
    
    def _check_if_required(self) -> bool:
        """Check if field is required."""
        try:
            required_indicators = ['required', 'mandatory', '*']
            
            # Check element attributes
            if self.element.get_attribute('required'):
                return True
            
            # Check for asterisks or "required" text in labels
            if self.label:
                for indicator in required_indicators:
                    if indicator in self.label.lower():
                        return True
            
            return False
        except:
            return False

class IntelligentFormFiller:
    """AI-powered form filler that maps master document data to form fields."""
    
    def __init__(self, master_document: MasterDocument, headless: bool = True):
        self.master_doc = master_document
        self.headless = headless
        self.driver = None
        
        # Field mapping strategies
        self.field_mappings = self._create_field_mappings()
        
        # Common field patterns
        self.field_patterns = {
            'company_name': ['company', 'organization', 'business', 'startup', 'entity'],
            'founder_name': ['name', 'founder', 'applicant', 'contact', 'representative'],
            'email': ['email', 'e-mail', 'contact'],
            'phone': ['phone', 'telephone', 'mobile', 'contact'],
            'website': ['website', 'url', 'web', 'site'],
            'description': ['description', 'about', 'summary', 'overview', 'pitch'],
            'funding_amount': ['amount', 'funding', 'request', 'investment', 'money'],
            'industry': ['industry', 'sector', 'category', 'field'],
            'location': ['location', 'address', 'city', 'country', 'region'],
            'stage': ['stage', 'phase', 'level', 'status']
        }
    
    def _create_field_mappings(self) -> Dict[str, Any]:
        """Create mappings from field types to master document data."""
        return {
            'company_name': self.master_doc.company.name,
            'organization_name': self.master_doc.company.name,
            'business_name': self.master_doc.company.name,
            'startup_name': self.master_doc.company.name,
            
            'founder_name': self.master_doc.founder.name,
            'applicant_name': self.master_doc.founder.name,
            'contact_name': self.master_doc.founder.name,
            'representative_name': self.master_doc.founder.name,
            
            'email': self.master_doc.founder.email,
            'contact_email': self.master_doc.founder.email,
            'email_address': self.master_doc.founder.email,
            
            'phone': self.master_doc.founder.phone,
            'phone_number': self.master_doc.founder.phone,
            'telephone': self.master_doc.founder.phone,
            'mobile': self.master_doc.founder.phone,
            
            'website': self.master_doc.company.website,
            'company_website': self.master_doc.company.website,
            'url': self.master_doc.company.website,
            
            'description': self.master_doc.company.description,
            'company_description': self.master_doc.company.description,
            'business_description': self.master_doc.company.description,
            'about': self.master_doc.company.description,
            'summary': self.master_doc.executive_summary,
            'overview': self.master_doc.executive_summary,
            'pitch': self.master_doc.executive_summary,
            
            'funding_amount': self.master_doc.financial.funding_amount_requested,
            'funding_request': self.master_doc.financial.funding_amount_requested,
            'investment_amount': self.master_doc.financial.funding_amount_requested,
            'amount_requested': self.master_doc.financial.funding_amount_requested,
            
            'industry': self.master_doc.company.industry,
            'sector': self.master_doc.company.industry,
            'category': self.master_doc.company.industry,
            
            'location': self.master_doc.company.location,
            'country': self.master_doc.company.location,
            'city': self.master_doc.company.location,
            
            'stage': self.master_doc.company.stage,
            'company_stage': self.master_doc.company.stage,
            'business_stage': self.master_doc.company.stage,
            
            'use_of_funds': "; ".join(self.master_doc.financial.use_of_funds),
            'funding_purpose': "; ".join(self.master_doc.financial.use_of_funds),
            
            'revenue': self.master_doc.financial.current_revenue,
            'current_revenue': self.master_doc.financial.current_revenue,
            
            'background': self.master_doc.founder.background,
            'founder_background': self.master_doc.founder.background,
            'experience': self.master_doc.founder.background,
        }
    
    def setup_driver(self):
        """Setup Selenium WebDriver."""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            logging.info("WebDriver setup successful for form filling")
        except Exception as e:
            logging.error(f"Failed to setup WebDriver: {e}")
            raise FormFillerError(f"WebDriver setup failed: {e}")
    
    def close_driver(self):
        """Close WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def fill_form(self, form_url: str, submit: bool = False) -> Dict[str, Any]:
        """
        Fill a form at the given URL using master document data.
        
        Args:
            form_url: URL of the form to fill
            submit: Whether to submit the form after filling
            
        Returns:
            Dictionary with filling results
        """
        result = {
            'url': form_url,
            'success': False,
            'fields_filled': 0,
            'total_fields': 0,
            'errors': [],
            'submitted': False
        }
        
        try:
            if not self.driver:
                self.setup_driver()
            
            logging.info(f"Loading form at: {form_url}")
            self.driver.get(form_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "form"))
            )
            
            # Find all forms on the page
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            
            if not forms:
                result['errors'].append("No forms found on the page")
                return result
            
            # Process the first form (or most relevant one)
            form = forms[0]
            fields = self._extract_form_fields(form)
            result['total_fields'] = len(fields)
            
            # Fill each field
            for field in fields:
                try:
                    if self._fill_field(field):
                        result['fields_filled'] += 1
                        logging.info(f"Filled field: {field.label}")
                    time.sleep(0.5)  # Small delay between fields
                except Exception as e:
                    error_msg = f"Error filling field '{field.label}': {str(e)}"
                    result['errors'].append(error_msg)
                    logging.warning(error_msg)
            
            result['success'] = result['fields_filled'] > 0
            
            # Submit form if requested
            if submit and result['success']:
                try:
                    submit_result = self._submit_form(form)
                    result['submitted'] = submit_result
                except Exception as e:
                    result['errors'].append(f"Error submitting form: {str(e)}")
            
        except Exception as e:
            result['errors'].append(f"General error: {str(e)}")
            logging.error(f"Error filling form: {e}")
        
        return result
    
    def _extract_form_fields(self, form) -> List[FormField]:
        """Extract all fillable fields from a form."""
        fields = []
        
        # Find input fields
        inputs = form.find_elements(By.TAG_NAME, "input")
        for input_elem in inputs:
            input_type = input_elem.get_attribute('type') or 'text'
            if input_type in ['text', 'email', 'tel', 'url', 'number']:
                label = self._get_field_label(input_elem)
                fields.append(FormField(input_elem, input_type, label))
        
        # Find textarea fields
        textareas = form.find_elements(By.TAG_NAME, "textarea")
        for textarea in textareas:
            label = self._get_field_label(textarea)
            fields.append(FormField(textarea, 'textarea', label))
        
        # Find select fields
        selects = form.find_elements(By.TAG_NAME, "select")
        for select in selects:
            label = self._get_field_label(select)
            fields.append(FormField(select, 'select', label))
        
        return fields
    
    def _get_field_label(self, element) -> str:
        """Get the label for a form field."""
        try:
            # Try to find associated label
            field_id = element.get_attribute('id')
            if field_id:
                label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{field_id}']")
                return label.text.strip()
        except:
            pass
        
        try:
            # Try placeholder text
            placeholder = element.get_attribute('placeholder')
            if placeholder:
                return placeholder.strip()
        except:
            pass
        
        try:
            # Try name attribute
            name = element.get_attribute('name')
            if name:
                return name.replace('_', ' ').replace('-', ' ').title()
        except:
            pass
        
        return "Unknown Field"
    
    def _fill_field(self, field: FormField) -> bool:
        """Fill a single form field."""
        try:
            # Determine what data to fill based on field label/type
            field_data = self._determine_field_data(field)
            
            if not field_data:
                return False
            
            # Fill based on field type
            if field.field_type in ['text', 'email', 'tel', 'url', 'number']:
                self._fill_input_field(field.element, field_data)
                return True
            
            elif field.field_type == 'textarea':
                self._fill_textarea_field(field.element, field_data)
                return True
            
            elif field.field_type == 'select':
                return self._fill_select_field(field.element, field_data)
            
            return False
            
        except Exception as e:
            logging.warning(f"Error filling field: {e}")
            return False
    
    def _determine_field_data(self, field: FormField) -> Optional[str]:
        """Determine what data to fill in a field based on its label."""
        label_lower = field.label.lower()
        
        # Direct mapping lookup
        for key, value in self.field_mappings.items():
            if key in label_lower:
                return str(value)
        
        # Pattern matching
        for pattern_type, patterns in self.field_patterns.items():
            for pattern in patterns:
                if pattern in label_lower:
                    mapping_key = f"{pattern_type}_name" if pattern_type in ['company', 'founder'] else pattern_type
                    if mapping_key in self.field_mappings:
                        return str(self.field_mappings[mapping_key])
        
        # Special cases for email fields
        if field.field_type == 'email' or 'email' in label_lower:
            return self.master_doc.founder.email
        
        # Special cases for phone fields
        if field.field_type == 'tel' or any(word in label_lower for word in ['phone', 'tel', 'mobile']):
            return self.master_doc.founder.phone
        
        # Special cases for URL fields
        if field.field_type == 'url' or any(word in label_lower for word in ['website', 'url', 'web']):
            return self.master_doc.company.website
        
        return None
    
    def _fill_input_field(self, element, data: str):
        """Fill an input field."""
        element.clear()
        element.send_keys(data)
    
    def _fill_textarea_field(self, element, data: str):
        """Fill a textarea field."""
        element.clear()
        element.send_keys(data)
    
    def _fill_select_field(self, element, data: str) -> bool:
        """Fill a select field."""
        try:
            select = Select(element)
            options = [option.text.lower() for option in select.options]
            
            # Try to find matching option
            data_lower = data.lower()
            for i, option_text in enumerate(options):
                if data_lower in option_text or option_text in data_lower:
                    select.select_by_index(i)
                    return True
            
            return False
        except Exception as e:
            logging.warning(f"Error filling select field: {e}")
            return False
    
    def _submit_form(self, form) -> bool:
        """Submit the form."""
        try:
            # Look for submit button
            submit_buttons = form.find_elements(By.CSS_SELECTOR, 
                "input[type='submit'], button[type='submit'], button:contains('Submit')")
            
            if submit_buttons:
                submit_buttons[0].click()
                time.sleep(2)  # Wait for submission
                return True
            
            # Try submitting the form directly
            form.submit()
            time.sleep(2)
            return True
            
        except Exception as e:
            logging.error(f"Error submitting form: {e}")
            return False

def fill_forms(opportunities: List[Dict[str, Any]], submit: bool = False) -> List[Dict[str, Any]]:
    """
    Fill forms for multiple opportunities.
    
    Args:
        opportunities: List of opportunity dictionaries with URLs
        submit: Whether to submit forms after filling
        
    Returns:
        List of form filling results
    """
    master_doc = load_master_document()
    form_filler = IntelligentFormFiller(master_doc, headless=True)
    results = []
    
    try:
        for opportunity in opportunities:
            try:
                url = opportunity.get('url', '')
                if not url:
                    continue
                
                logging.info(f"Filling form for: {opportunity.get('title', 'Unknown')}")
                result = form_filler.fill_form(url, submit)
                result['opportunity'] = opportunity
                results.append(result)
                
                # Add delay between forms
                time.sleep(5)
                
            except Exception as e:
                error_result = {
                    'url': opportunity.get('url', ''),
                    'success': False,
                    'error': str(e),
                    'opportunity': opportunity
                }
                results.append(error_result)
                logging.error(f"Error processing opportunity: {e}")
    
    finally:
        form_filler.close_driver()
    
    return results

if __name__ == "__main__":
    # Test the form filler
    logging.basicConfig(level=logging.INFO)
    
    # Test with a sample opportunity
    test_opportunities = [
        {
            'title': 'Test Grant Application',
            'url': 'https://example.com/grant-form',
            'source': 'Test'
        }
    ]
    
    results = fill_forms(test_opportunities, submit=False)
    
    for result in results:
        print(f"Form: {result['url']}")
        print(f"Success: {result['success']}")
        print(f"Fields filled: {result.get('fields_filled', 0)}")
        print()
