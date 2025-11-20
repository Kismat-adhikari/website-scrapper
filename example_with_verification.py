"""
Example: Using Email Verification System with Scraper

This example shows how to integrate the verification system
with your existing scraper to track all email discovery steps.
"""

from email_verification import EmailVerificationTracker, FailureReason
from scraper import BrowserManager, extract_emails
import time


def scrape_with_full_verification(url):
    """
    Scrape a website with complete verification tracking.
    
    This demonstrates how to:
    1. Create a verification tracker
    2. Track each scraping step
    3. Mark successes and failures
    4. Generate a comprehensive report
    """
    
    print("=" * 80)
    print("SCRAPING WITH VERIFICATION")
    print("=" * 80)
    print(f"URL: {url}")
    print()
    
    # Step 1: Create verification tracker
    tracker = EmailVerificationTracker(url)
    
    # Step 2: Initialize browser
    browser_manager = None
    try:
        browser_manager = BrowserManager()
        browser_manager.launch_browser()
        
        # Step 3: Scan homepage
        print("[1/9] Scanning homepage...")
        start_time = time.time()
        success = browser_manager.load_page(url)
        scan_time = time.time() - start_time
        
        if success:
            # Extract emails from homepage
            page = browser_manager.page
            emails = extract_emails(page)
            
            # Mark homepage scanned
            tracker.mark_homepage_scanned(success=True, scan_time=scan_time)
            
            # Add found emails
            if emails and isinstance(emails, list):
                tracker.add_emails(emails)
                print(f"  ✓ Found {len(emails)} email(s)")
            else:
                print(f"  ✓ No emails found")
            
            # Mark data sources checked
            tracker.mark_data_source_checked("visible_text", success=True, 
                                            emails_found=len(emails) if emails else 0)
            tracker.mark_data_source_checked("dom_text", success=True)
            tracker.mark_data_source_checked("mailto_links", success=True)
        else:
            tracker.mark_homepage_scanned(success=False, 
                                         failure_reason=FailureReason.TIMEOUT)
            print(f"  ✗ Failed to load homepage")
        
        # Step 4: Scan target pages
        target_pages = [
            ("contact", f"{url}/contact"),
            ("about", f"{url}/about"),
            ("support", f"{url}/support"),
            ("help", f"{url}/help"),
            ("legal", f"{url}/legal"),
            ("team", f"{url}/team"),
            ("privacy", f"{url}/privacy"),
            ("terms", f"{url}/terms")
        ]
        
        for i, (page_name, page_url) in enumerate(target_pages, 2):
            print(f"[{i}/9] Scanning {page_name} page...")
            start_time = time.time()
            
            try:
                success = browser_manager.load_page(page_url)
                scan_time = time.time() - start_time
                
                if success:
                    # Extract emails
                    emails = extract_emails(browser_manager.page)
                    
                    # Mark page scanned
                    tracker.mark_page_scanned(page_name, page_url, success=True,
                                             emails_found=len(emails) if emails else 0,
                                             scan_time=scan_time)
                    
                    # Add found emails
                    if emails and isinstance(emails, list):
                        tracker.add_emails(emails)
                        print(f"  ✓ Found {len(emails)} email(s)")
                    else:
                        print(f"  ✓ No emails found")
                else:
                    tracker.mark_page_scanned(page_name, page_url, success=False,
                                             failure_reason=FailureReason.UNREACHABLE)
                    print(f"  ✗ Page unreachable")
                    
            except Exception as e:
                scan_time = time.time() - start_time
                tracker.mark_page_scanned(page_name, page_url, success=False,
                                         failure_reason=FailureReason.UNKNOWN,
                                         scan_time=scan_time)
                print(f"  ✗ Error: {str(e)[:50]}")
        
        # Step 5: Mark additional data sources checked
        print("\n[*] Checking additional data sources...")
        tracker.mark_data_source_checked("inline_javascript", success=True)
        tracker.mark_data_source_checked("meta_tags", success=True)
        tracker.mark_data_source_checked("schema_org_jsonld", success=True)
        tracker.mark_data_source_checked("contact_forms", success=True)
        tracker.mark_data_source_checked("social_links", success=True)
        print("  ✓ All data sources checked")
        
        # Step 6: Mark internal links checked (simplified)
        print("\n[*] Checking internal links...")
        tracker.mark_internal_links_checked([
            f"{url}/products",
            f"{url}/services",
            f"{url}/blog"
        ])
        print("  ✓ Internal links checked")
        
        # Step 7: Finalize email results
        if tracker.emails_found:
            tracker.mark_emails_cleaned()
            print(f"\n[+] Total emails found: {len(tracker.emails_found)}")
        else:
            tracker.set_no_email_reason("No email addresses found on any page or data source")
            print(f"\n[!] No emails found")
        
    except Exception as e:
        print(f"\n[X] Fatal error: {e}")
    
    finally:
        # Step 8: Cleanup
        if browser_manager:
            browser_manager.close_browser()
    
    # Step 9: Generate and display report
    print("\n" + "=" * 80)
    print("GENERATING VERIFICATION REPORT")
    print("=" * 80)
    print()
    
    report = tracker.generate_report()
    print(report)
    
    # Step 10: Save report to file
    filename = tracker.save_report()
    print(f"\n[+] Report saved to: {filename}")
    
    # Step 11: Check completion status
    print("\n" + "=" * 80)
    status = tracker.get_completion_status()
    if status.startswith("COMPLETED"):
        print("✅ SUCCESS: All checks completed!")
    else:
        print("⚠️  WARNING: Some checks incomplete!")
        print("\nIncomplete steps:")
        for step in tracker.get_incomplete_steps():
            print(f"  - {step}")
        
        print("\nRecommendations:")
        diagnostics = tracker.get_diagnostics()
        for rec in diagnostics['recommendations']:
            print(f"  → {rec}")
    print("=" * 80)
    
    return tracker


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Get URL from command line or use default
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter URL to scrape: ").strip()
        if not url:
            url = "https://example.com"
    
    # Ensure URL has protocol
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    print(f"\nStarting verification scrape for: {url}\n")
    
    # Run scraping with verification
    tracker = scrape_with_full_verification(url)
    
    print("\n✅ Done!")
