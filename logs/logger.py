CONTINUE P"""
Enhanced logging module for comprehensive application tracking.
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

class GrantApplicationLogger:
    """Specialized logger for grant application process."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup different log files
        self.main_log = self.log_dir / "app.log"
        self.error_log = self.log_dir / "errors.log"
        self.scraping_log = self.log_dir / "scraping.log"
        self.form_filling_log = self.log_dir / "form_filling.log"
        self.submission_log = self.log_dir / "submissions.log"
        self.activity_log = self.log_dir / "activity.json"
        
        self._setup_loggers()
        
    def _setup_loggers(self):
        """Setup different loggers for different components."""
        
        # Main application logger
        self.main_logger = logging.getLogger('grant_app_main')
        self.main_logger.setLevel(logging.INFO)
        
        main_handler = logging.FileHandler(self.main_log)
        main_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        main_handler.setFormatter(main_formatter)
        
        if not self.main_logger.handlers:
            self.main_logger.addHandler(main_handler)
        
        # Error logger
        self.error_logger = logging.getLogger('grant_app_errors')
        self.error_logger.setLevel(logging.ERROR)
        
        error_handler = logging.FileHandler(self.error_log)
        error_formatter = logging.Formatter(
            '%(asctime)s - ERROR - %(name)s - %(message)s - %(pathname)s:%(lineno)d'
        )
        error_handler.setFormatter(error_formatter)
        
        if not self.error_logger.handlers:
            self.error_logger.addHandler(error_handler)
        
        # Component-specific loggers
        self._setup_component_logger('scraper', self.scraping_log)
        self._setup_component_logger('form_filler', self.form_filling_log)
        self._setup_component_logger('submitter', self.submission_log)
        
    def _setup_component_logger(self, component: str, log_file: Path):
        """Setup logger for a specific component."""
        logger = logging.getLogger(f'grant_app_{component}')
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            f'%(asctime)s - {component.upper()} - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        if not logger.handlers:
            logger.addHandler(handler)
    
    def log_activity(self, activity_type: str, data: Dict[str, Any]):
        """Log structured activity data."""
        activity = {
            'timestamp': datetime.now().isoformat(),
            'type': activity_type,
            'data': data
        }
        
        # Load existing activities
        activities = []
        if self.activity_log.exists():
            try:
                with open(self.activity_log, 'r') as f:
                    activities = json.load(f)
            except:
                activities = []
        
        # Add new activity
        activities.append(activity)
        
        # Save activities (keep only last 1000 entries)
        activities = activities[-1000:]
        
        with open(self.activity_log, 'w') as f:
            json.dump(activities, f, indent=2)
    
    def log_opportunity_discovery(self, opportunities: List[Dict[str, Any]]):
        """Log discovered opportunities."""
        self.main_logger.info(f"Discovered {len(opportunities)} opportunities")
        
        for opp in opportunities:
            self.main_logger.info(f"Found: {opp.get('title', 'Unknown')} from {opp.get('source', 'Unknown')}")
        
        self.log_activity('opportunity_discovery', {
            'count': len(opportunities),
            'opportunities': opportunities
        })
    
    def log_form_filling_start(self, opportunity: Dict[str, Any]):
        """Log start of form filling process."""
        self.main_logger.info(f"Starting form filling for: {opportunity.get('title', 'Unknown')}")
        
        self.log_activity('form_filling_start', {
            'opportunity': opportunity
        })
    
    def log_form_filling_result(self, result: Dict[str, Any]):
        """Log form filling results."""
        success = result.get('success', False)
        fields_filled = result.get('fields_filled', 0)
        total_fields = result.get('total_fields', 0)
        
        if success:
            self.main_logger.info(f"Form filling successful: {fields_filled}/{total_fields} fields filled")
        else:
            self.main_logger.warning(f"Form filling failed: {result.get('errors', [])}")
        
        self.log_activity('form_filling_result', result)
    
    def log_submission_attempt(self, opportunity: Dict[str, Any], dry_run: bool = True):
        """Log submission attempt."""
        mode = "DRY RUN" if dry_run else "LIVE"
        self.main_logger.info(f"[{mode}] Attempting submission for: {opportunity.get('title', 'Unknown')}")
        
        self.log_activity('submission_attempt', {
            'opportunity': opportunity,
            'dry_run': dry_run
        })
    
    def log_submission_result(self, result: Dict[str, Any]):
        """Log submission results."""
        submitted = result.get('submitted', False)
        dry_run = result.get('dry_run', True)
        
        if submitted:
            mode = "DRY RUN" if dry_run else "LIVE"
            self.main_logger.info(f"[{mode}] Submission successful: {result.get('confirmation_message', 'No message')}")
        else:
            self.main_logger.error(f"Submission failed: {result.get('errors', [])}")
        
        self.log_activity('submission_result', result)
    
    def log_error(self, component: str, error: str, context: Dict[str, Any] = None):
        """Log errors with context."""
        self.error_logger.error(f"[{component}] {error}")
        
        if context:
            self.error_logger.error(f"Context: {json.dumps(context, indent=2)}")
        
        self.log_activity('error', {
            'component': component,
            'error': error,
            'context': context or {}
        })
    
    def generate_session_report(self) -> str:
        """Generate a report for the current session."""
        if not self.activity_log.exists():
            return "No activity logged yet."
        
        try:
            with open(self.activity_log, 'r') as f:
                activities = json.load(f)
        except:
            return "Error reading activity log."
        
        # Get today's activities
        today = datetime.now().strftime('%Y-%m-%d')
        today_activities = [a for a in activities if a['timestamp'].startswith(today)]
        
        if not today_activities:
            return "No activities logged today."
        
        # Count different activity types
        activity_counts = {}
        for activity in today_activities:
            activity_type = activity['type']
            activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1
        
        # Generate report
        report_lines = [
            f"GRANT APPLICATION SESSION REPORT - {today}",
            "=" * 50,
            ""
        ]
        
        for activity_type, count in activity_counts.items():
            report_lines.append(f"{activity_type.replace('_', ' ').title()}: {count}")
        
        report_lines.extend([
            "",
            "Recent Activities:",
            "-" * 20
        ])
        
        # Show last 10 activities
        recent_activities = today_activities[-10:]
        for activity in recent_activities:
            timestamp = activity['timestamp'].split('T')[1][:8]  # Just time
            activity_type = activity['type'].replace('_', ' ').title()
            report_lines.append(f"{timestamp} - {activity_type}")
        
        return "\n".join(report_lines)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get application statistics."""
        stats = {
            'total_opportunities_discovered': 0,
            'forms_filled_successfully': 0,
            'forms_filled_failed': 0,
            'submissions_successful': 0,
            'submissions_failed': 0,
            'errors_count': 0
        }
        
        if not self.activity_log.exists():
            return stats
        
        try:
            with open(self.activity_log, 'r') as f:
                activities = json.load(f)
        except:
            return stats
        
        for activity in activities:
            activity_type = activity['type']
            data = activity.get('data', {})
            
            if activity_type == 'opportunity_discovery':
                stats['total_opportunities_discovered'] += data.get('count', 0)
            elif activity_type == 'form_filling_result':
                if data.get('success', False):
                    stats['forms_filled_successfully'] += 1
                else:
                    stats['forms_filled_failed'] += 1
            elif activity_type == 'submission_result':
                if data.get('submitted', False) and not data.get('dry_run', True):
                    stats['submissions_successful'] += 1
                elif not data.get('submitted', False):
                    stats['submissions_failed'] += 1
            elif activity_type == 'error':
                stats['errors_count'] += 1
        
        return stats

# Global logger instance
app_logger = GrantApplicationLogger()

def get_logger(component: str = 'main') -> logging.Logger:
    """Get logger for a specific component."""
    return logging.getLogger(f'grant_app_{component}')

def log_activity(activity_type: str, data: Dict[str, Any]):
    """Log activity using global logger."""
    app_logger.log_activity(activity_type, data)

def log_error(component: str, error: str, context: Dict[str, Any] = None):
    """Log error using global logger."""
    app_logger.log_error(component, error, context)

def get_session_report() -> str:
    """Get session report from global logger."""
    return app_logger.generate_session_report()

def get_statistics() -> Dict[str, Any]:
    """Get statistics from global logger."""
    return app_logger.get_statistics()
