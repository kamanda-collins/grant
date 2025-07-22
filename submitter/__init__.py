"""
Submission module for handling the final submission of grant applications.
"""

import time
import logging
from typing import Dict, List, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import json
import os
from datetime import datetime

class SubmissionError(Exception):
    """Custom exception for submission errors."""
    pass

class ApplicationSubmitter:
    """Handles the submission of filled application forms."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.submission_log = []
        
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
            logging.info("WebDriver setup successful for submission")
        except Exception as e:
            logging.error(f"Failed to setup WebDriver: {e}")
            raise SubmissionError(f"WebDriver setup failed: {e}")
    
    def close_driver(self):
        """Close WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def submit_application(self, form_result: Dict[str, Any], 
                          dry_run: bool = True) -> Dict[str, Any]:
        """
        Submit a single application.
        
        Args:
            form_result: Result from form filling
            dry_run: If True, don't actually submit, just validate
            
        Returns:
            Dictionary with submission results
        """
        submission_result = {
            'url': form_result.get('url', ''),
            'opportunity': form_result.get('opportunity', {}),
            'submitted': False,
            'submission_id': None,
            'confirmation_message': None,
            'errors': [],
            'timestamp': datetime.now().isoformat(),
            'dry_run': dry_run
        }
        
        try:
            if not form_result.get('success', False):
                submission_result['errors'].append("Form filling was not successful")
                return submission_result
            
            url = form_result['url']
            logging.info(f"{'DRY RUN: ' if dry_run else ''}Submitting application to: {url}")
            
            if not self.driver:
                self.setup_driver()
            
            # Navigate to the form
            self.driver.get(url)
            time.sleep(2)
            
            # Re-fill the form (in case session was lost)
            if not dry_run:
                self._refill_form_if_needed(form_result)
            
            # Find and validate submission elements
            submission_elements = self._find_submission_elements()
            
            if not submission_elements:
                submission_result['errors'].append("No submission button found")
                return submission_result
            
            # Perform pre-submission validation
            validation_result = self._validate_before_submission()
            if not validation_result['valid']:
                submission_result['errors'].extend(validation_result['errors'])
                return submission_result
            
            if dry_run:
                submission_result['submitted'] = True
                submission_result['confirmation_message'] = "DRY RUN: Would have submitted successfully"
                logging.info("DRY RUN: Form validation passed, would submit")
                return submission_result
            
            # Actually submit the form
            submit_button = submission_elements[0]
            submit_button.click()
            
            # Wait for submission confirmation
            confirmation = self._wait_for_confirmation()
            
            if confirmation:
                submission_result['submitted'] = True
                submission_result['confirmation_message'] = confirmation['message']
                submission_result['submission_id'] = confirmation.get('id')
                logging.info(f"Successfully submitted application: {confirmation['message']}")
            else:
                submission_result['errors'].append("No confirmation received after submission")
            
        except Exception as e:
            error_msg = f"Error during submission: {str(e)}"
            submission_result['errors'].append(error_msg)
            logging.error(error_msg)
        
        return submission_result
    
    def _find_submission_elements(self) -> List:
        """Find form submission buttons."""
        submission_selectors = [
            "input[type='submit']",
            "button[type='submit']", 
            "button:contains('Submit')",
            "button:contains('Apply')",
            "button:contains('Send')",
            ".submit-btn",
            ".apply-btn"
        ]
        
        for selector in submission_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    return elements
            except:
                continue
        
        return []
    
    def _validate_before_submission(self) -> Dict[str, Any]:
        """Validate form before submission."""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check for required fields that are empty
            required_fields = self.driver.find_elements(By.CSS_SELECTOR, 
                "input[required], select[required], textarea[required]")
            
            for field in required_fields:
                if not field.get_attribute('value'):
                    field_name = (field.get_attribute('name') or 
                                field.get_attribute('id') or 
                                'Unknown field')
                    validation_result['errors'].append(f"Required field is empty: {field_name}")
                    validation_result['valid'] = False
            
            # Check for validation errors on the page
            error_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                ".error, .validation-error, .field-error")
            
            for error_elem in error_elements:
                if error_elem.is_displayed():
                    validation_result['errors'].append(f"Validation error: {error_elem.text}")
                    validation_result['valid'] = False
            
        except Exception as e:
            validation_result['warnings'].append(f"Could not complete validation: {str(e)}")
        
        return validation_result
    
    def _wait_for_confirmation(self, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Wait for submission confirmation."""
        try:
            # Common confirmation indicators
            confirmation_selectors = [
                ".success", ".confirmation", ".thank-you",
                "[class*='success']", "[class*='confirm']",
                "h1:contains('Thank')", "h2:contains('Success')",
                "div:contains('submitted')", "div:contains('received')"
            ]
            
            # Wait for any confirmation element
            for selector in confirmation_selectors:
                try:
                    element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    
                    if element.is_displayed():
                        return {
                            'message': element.text.strip(),
                            'id': self._extract_submission_id(element.text)
                        }
                except TimeoutException:
                    continue
            
            # Check if URL changed (often indicates successful submission)
            current_url = self.driver.current_url
            if any(keyword in current_url.lower() for keyword in 
                   ['success', 'confirmation', 'thank', 'submitted']):
                return {
                    'message': f"Redirected to confirmation page: {current_url}",
                    'id': None
                }
            
            return None
            
        except Exception as e:
            logging.warning(f"Error waiting for confirmation: {e}")
            return None
    
    def _extract_submission_id(self, text: str) -> Optional[str]:
        """Extract submission ID from confirmation text."""
        import re
        
        # Common patterns for submission IDs
        patterns = [
            r'ID[:\s]+([A-Z0-9\-]+)',
            r'Reference[:\s]+([A-Z0-9\-]+)',
            r'Number[:\s]+([A-Z0-9\-]+)',
            r'#([A-Z0-9\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _refill_form_if_needed(self, form_result: Dict[str, Any]):
        """Re-fill form if session was lost or fields are empty."""
        # This is a simplified version - in practice, you'd re-run the form filler
        pass
    
    def save_submission_log(self, log_file: str = "logs/submissions.json"):
        """Save submission log to file."""
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            # Load existing log
            existing_log = []
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    existing_log = json.load(f)
            
            # Append new submissions
            existing_log.extend(self.submission_log)
            
            # Save updated log
            with open(log_file, 'w') as f:
                json.dump(existing_log, f, indent=2)
            
            logging.info(f"Submission log saved to {log_file}")
            
        except Exception as e:
            logging.error(f"Error saving submission log: {e}")

def submit_applications(form_results: List[Dict[str, Any]], 
                       dry_run: bool = True) -> List[Dict[str, Any]]:
    """
    Submit multiple applications.
    
    Args:
        form_results: List of form filling results
        dry_run: If True, validate but don't actually submit
        
    Returns:
        List of submission results
    """
    submitter = ApplicationSubmitter(headless=True)
    submission_results = []
    
    try:
        for form_result in form_results:
            try:
                opportunity_title = form_result.get('opportunity', {}).get('title', 'Unknown')
                logging.info(f"Processing submission for: {opportunity_title}")
                
                result = submitter.submit_application(form_result, dry_run)
                submission_results.append(result)
                submitter.submission_log.append(result)
                
                # Add delay between submissions
                if not dry_run:
                    time.sleep(10)  # Longer delay for actual submissions
                else:
                    time.sleep(2)   # Shorter delay for dry runs
                
            except Exception as e:
                error_result = {
                    'url': form_result.get('url', ''),
                    'opportunity': form_result.get('opportunity', {}),
                    'submitted': False,
                    'errors': [str(e)],
                    'timestamp': datetime.now().isoformat(),
                    'dry_run': dry_run
                }
                submission_results.append(error_result)
                logging.error(f"Error processing submission: {e}")
        
        # Save submission log
        submitter.save_submission_log()
        
    finally:
        submitter.close_driver()
    
    return submission_results

def generate_submission_report(submission_results: List[Dict[str, Any]]) -> str:
    """Generate a human-readable submission report."""
    report_lines = [
        "GRANT APPLICATION SUBMISSION REPORT",
        "=" * 40,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]
    
    successful = [r for r in submission_results if r.get('submitted', False)]
    failed = [r for r in submission_results if not r.get('submitted', False)]
    
    report_lines.extend([
        f"Total applications processed: {len(submission_results)}",
        f"Successfully submitted: {len(successful)}",
        f"Failed submissions: {len(failed)}",
        ""
    ])
    
    if successful:
        report_lines.extend([
            "SUCCESSFUL SUBMISSIONS:",
            "-" * 25
        ])
        for result in successful:
            opp = result.get('opportunity', {})
            report_lines.extend([
                f"• {opp.get('title', 'Unknown')}",
                f"  URL: {result['url']}",
                f"  Confirmation: {result.get('confirmation_message', 'N/A')}",
                f"  ID: {result.get('submission_id', 'N/A')}",
                ""
            ])
    
    if failed:
        report_lines.extend([
            "FAILED SUBMISSIONS:",
            "-" * 20
        ])
        for result in failed:
            opp = result.get('opportunity', {})
            report_lines.extend([
                f"• {opp.get('title', 'Unknown')}",
                f"  URL: {result['url']}",
                f"  Errors: {'; '.join(result.get('errors', []))}",
                ""
            ])
    
    return "\n".join(report_lines)

if __name__ == "__main__":
    # Test the submitter
    logging.basicConfig(level=logging.INFO)
    
    # Test with sample form results
    test_form_results = [
        {
            'url': 'https://example.com/grant-form',
            'success': True,
            'fields_filled': 5,
            'opportunity': {
                'title': 'Test Grant',
                'source': 'Test Source'
            }
        }
    ]
    
    results = submit_applications(test_form_results, dry_run=True)
    
    report = generate_submission_report(results)
    print(report)
