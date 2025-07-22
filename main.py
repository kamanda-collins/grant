"""
Main entry point for the Grant & Incubator Auto-Application System.
"""

import argparse
import sys
from typing import List, Dict, Any
from config.master_document import load_master_document, load_config
from scraper import discover_opportunities
from form_filler import fill_forms
from submitter import submit_applications, generate_submission_report
from logs.logger import get_logger, log_activity, get_session_report, get_statistics

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description='Grant & Incubator Auto-Application System')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Run in dry-run mode (no actual submissions)')
    parser.add_argument('--max-applications', type=int, default=10,
                       help='Maximum number of applications to process')
    parser.add_argument('--keywords', nargs='+', 
                       default=['tech', 'startup', 'environmental', 'innovation'],
                       help='Keywords to search for opportunities')
    parser.add_argument('--report-only', action='store_true',
                       help='Generate report from previous runs without processing new applications')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = get_logger('main')
    logger.info("=" * 60)
    logger.info("STARTING GRANT AUTO-APPLICATION SYSTEM")
    logger.info("=" * 60)
    
    try:
        # Handle report-only mode
        if args.report_only:
            print("\n" + get_session_report())
            print("\nSTATISTICS:")
            print("-" * 20)
            stats = get_statistics()
            for key, value in stats.items():
                print(f"{key.replace('_', ' ').title()}: {value}")
            return
        
        # Load configuration and master document
        logger.info("Loading configuration and master document...")
        config = load_config()
        master_doc = load_master_document()
        
        log_activity('application_start', {
            'dry_run': args.dry_run,
            'max_applications': args.max_applications,
            'keywords': args.keywords
        })
        
        print(f"🚀 Starting Grant Auto-Application for: {master_doc.company.name}")
        print(f"📧 Contact: {master_doc.founder.email}")
        print(f"💰 Seeking: {master_doc.financial.funding_amount_requested}")
        print(f"🎯 Mode: {'DRY RUN' if args.dry_run else 'LIVE SUBMISSION'}")
        print(f"🔍 Keywords: {', '.join(args.keywords)}")
        print("-" * 60)
        
        # Step 1: Discover opportunities
        print("\n📊 STEP 1: Discovering grant and incubator opportunities...")
        logger.info("Starting opportunity discovery")
        
        opportunities = discover_opportunities(
            keywords=args.keywords,
            max_results=args.max_applications
        )
        
        if not opportunities:
            print("❌ No opportunities found. Try different keywords or check your internet connection.")
            logger.warning("No opportunities discovered")
            return
        
        print(f"✅ Found {len(opportunities)} relevant opportunities")
        for i, opp in enumerate(opportunities[:5], 1):
            print(f"   {i}. {opp['title']} ({opp['source']})")
        
        if len(opportunities) > 5:
            print(f"   ... and {len(opportunities) - 5} more")
        
        # Step 2: Fill forms
        print(f"\n📝 STEP 2: Filling application forms...")
        logger.info(f"Starting form filling for {len(opportunities)} opportunities")
        
        form_results = fill_forms(opportunities, submit=False)
        
        successful_forms = [r for r in form_results if r.get('success', False)]
        failed_forms = [r for r in form_results if not r.get('success', False)]
        
        print(f"✅ Successfully filled: {len(successful_forms)} forms")
        print(f"❌ Failed to fill: {len(failed_forms)} forms")
        
        if failed_forms:
            print("\nFailed forms:")
            for result in failed_forms[:3]:
                errors = '; '.join(result.get('errors', [])[:2])
                print(f"   • {result.get('opportunity', {}).get('title', 'Unknown')}: {errors}")
        
        if not successful_forms:
            print("❌ No forms were successfully filled. Check the logs for details.")
            return
        
        # Step 3: Submit applications
        print(f"\n🚀 STEP 3: {'Validating' if args.dry_run else 'Submitting'} applications...")
        logger.info(f"Starting application submission (dry_run={args.dry_run})")
        
        submission_results = submit_applications(successful_forms, dry_run=args.dry_run)
        
        successful_submissions = [r for r in submission_results if r.get('submitted', False)]
        failed_submissions = [r for r in submission_results if not r.get('submitted', False)]
        
        print(f"✅ {'Validated' if args.dry_run else 'Submitted'}: {len(successful_submissions)} applications")
        print(f"❌ Failed: {len(failed_submissions)} applications")
        
        # Step 4: Generate and display report
        print(f"\n📋 FINAL REPORT")
        print("=" * 60)
        
        report = generate_submission_report(submission_results)
        print(report)
        
        # Save summary to logs
        summary = {
            'opportunities_found': len(opportunities),
            'forms_filled': len(successful_forms),
            'applications_processed': len(submission_results),
            'successful_submissions': len(successful_submissions),
            'failed_submissions': len(failed_submissions),
            'dry_run': args.dry_run
        }
        
        log_activity('application_complete', summary)
        
        print(f"\n💾 All logs saved to 'logs/' directory")
        print(f"📊 Run with --report-only to see statistics from all sessions")
        
        if args.dry_run:
            print(f"\n⚠️  This was a DRY RUN. Re-run without --dry-run to actually submit applications.")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Application stopped by user.")
        logger.info("Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.error(f"Application error: {str(e)}")
        raise
    finally:
        logger.info("Grant auto-application session ended")
        print(f"\n🏁 Session completed. Check logs for detailed information.")

if __name__ == "__main__":
    main()
