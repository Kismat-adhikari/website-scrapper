"""
Email Discovery Verification System

This module provides comprehensive verification that all email discovery steps
were completed properly. It does NOT scrape - it only verifies the scraping process.

Usage:
    from email_verification import EmailVerificationTracker
    
    tracker = EmailVerificationTracker(url)
    tracker.mark_homepage_scanned()
    tracker.mark_page_scanned("contact")
    tracker.mark_data_source_checked("visible_text")
    tracker.add_email("test@example.com")
    
    report = tracker.generate_report()
    print(report)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from datetime import datetime
from enum import Enum


class CheckStatus(Enum):
    """Status of a verification check"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class FailureReason(Enum):
    """Reasons for check failures"""
    PAGE_BLOCKED = "page_blocked"
    TIMEOUT = "timeout"
    UNREACHABLE = "unreachable"
    ANTI_BOT = "anti_bot_triggered"
    FORM_UNREADABLE = "form_unreadable"
    JAVASCRIPT_ERROR = "javascript_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


@dataclass
class PageScanResult:
    """Result of scanning a single page"""
    page_name: str
    url: str
    status: CheckStatus
    failure_reason: Optional[FailureReason] = None
    emails_found: int = 0
    scan_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DataSourceCheck:
    """Result of checking a data source"""
    source_name: str
    status: CheckStatus
    emails_found: int = 0
    failure_reason: Optional[FailureReason] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class EmailVerificationTracker:
    """
    Tracks and verifies all steps of the email discovery process.
    
    This class ensures that:
    1. All required pages are scanned
    2. All data sources are checked
    3. All steps produce results
    4. Failures are tracked
    5. Final status is clear
    """
    
    # Required pages to scan
    REQUIRED_PAGES = [
        "homepage",
        "contact",
        "about",
        "support",
        "help",
        "legal",
        "team",
        "privacy",
        "terms"
    ]
    
    # Required data sources to check
    REQUIRED_DATA_SOURCES = [
        "visible_text",
        "dom_text",
        "inline_javascript",
        "meta_tags",
        "schema_org_jsonld",
        "mailto_links",
        "contact_forms",
        "social_links"
    ]
    
    def __init__(self, base_url: str):
        """
        Initialize verification tracker.
        
        Args:
            base_url: The base URL being scraped
        """
        self.base_url = base_url
        self.start_time = datetime.now()
        
        # Page scanning tracking
        self.homepage_scanned = False
        self.pages_scanned: Dict[str, PageScanResult] = {}
        self.internal_links_depth_2_checked = False
        self.internal_links_found: List[str] = []
        
        # Data source tracking
        self.data_sources_checked: Dict[str, DataSourceCheck] = {}
        
        # Email tracking
        self.emails_found: Set[str] = set()
        self.emails_cleaned = False
        self.no_email_reason: Optional[str] = None
        
        # Failure tracking
        self.failures: List[Dict] = []
        self.slow_operations: List[Dict] = []
        self.repeated_failures: Dict[str, int] = {}
        
        # Overall status
        self.completed = False
        self.completion_time: Optional[datetime] = None
    
    # ========================================================================
    # PAGE SCANNING TRACKING
    # ========================================================================
    
    def mark_homepage_scanned(self, success: bool = True, 
                             failure_reason: Optional[FailureReason] = None,
                             scan_time: float = 0.0):
        """Mark homepage as scanned"""
        self.homepage_scanned = success
        self.pages_scanned["homepage"] = PageScanResult(
            page_name="homepage",
            url=self.base_url,
            status=CheckStatus.COMPLETED if success else CheckStatus.FAILED,
            failure_reason=failure_reason,
            scan_time=scan_time
        )
        
        if not success:
            self._track_failure("homepage", failure_reason)
    
    def mark_page_scanned(self, page_name: str, url: str, 
                         success: bool = True,
                         failure_reason: Optional[FailureReason] = None,
                         emails_found: int = 0,
                         scan_time: float = 0.0):
        """Mark a specific page as scanned"""
        self.pages_scanned[page_name] = PageScanResult(
            page_name=page_name,
            url=url,
            status=CheckStatus.COMPLETED if success else CheckStatus.FAILED,
            failure_reason=failure_reason,
            emails_found=emails_found,
            scan_time=scan_time
        )
        
        if not success:
            self._track_failure(page_name, failure_reason)
        
        # Track slow operations
        if scan_time > 10.0:  # More than 10 seconds
            self.slow_operations.append({
                'operation': f'scan_{page_name}',
                'time': scan_time,
                'url': url
            })
    
    def mark_internal_links_checked(self, links_found: List[str]):
        """Mark internal links up to depth 2 as checked"""
        self.internal_links_depth_2_checked = True
        self.internal_links_found = links_found
    
    # ========================================================================
    # DATA SOURCE TRACKING
    # ========================================================================
    
    def mark_data_source_checked(self, source_name: str, 
                                 success: bool = True,
                                 emails_found: int = 0,
                                 failure_reason: Optional[FailureReason] = None):
        """Mark a data source as checked"""
        self.data_sources_checked[source_name] = DataSourceCheck(
            source_name=source_name,
            status=CheckStatus.COMPLETED if success else CheckStatus.FAILED,
            emails_found=emails_found,
            failure_reason=failure_reason
        )
        
        if not success:
            self._track_failure(f"data_source_{source_name}", failure_reason)
    
    # ========================================================================
    # EMAIL TRACKING
    # ========================================================================
    
    def add_email(self, email: str):
        """Add a found email"""
        self.emails_found.add(email.lower().strip())
    
    def add_emails(self, emails: List[str]):
        """Add multiple found emails"""
        for email in emails:
            self.add_email(email)
    
    def mark_emails_cleaned(self):
        """Mark emails as cleaned and formatted"""
        self.emails_cleaned = True
    
    def set_no_email_reason(self, reason: str):
        """Set reason for no emails found"""
        self.no_email_reason = reason
    
    # ========================================================================
    # FAILURE TRACKING
    # ========================================================================
    
    def _track_failure(self, operation: str, reason: Optional[FailureReason]):
        """Track a failure"""
        self.failures.append({
            'operation': operation,
            'reason': reason.value if reason else 'unknown',
            'timestamp': datetime.now().isoformat()
        })
        
        # Track repeated failures
        key = f"{operation}_{reason.value if reason else 'unknown'}"
        self.repeated_failures[key] = self.repeated_failures.get(key, 0) + 1
    
    # ========================================================================
    # VERIFICATION METHODS
    # ========================================================================
    
    def verify_website_scan_complete(self) -> Dict:
        """Verify that website scan is fully complete"""
        checks = {
            'homepage_scanned': self.homepage_scanned,
            'internal_links_checked': self.internal_links_depth_2_checked,
            'target_pages_checked': {}
        }
        
        # Check each required page
        for page in self.REQUIRED_PAGES:
            if page == "homepage":
                checks['target_pages_checked'][page] = self.homepage_scanned
            else:
                checks['target_pages_checked'][page] = page in self.pages_scanned
        
        checks['all_pages_complete'] = all(checks['target_pages_checked'].values())
        
        return checks
    
    def verify_data_sources_complete(self) -> Dict:
        """Verify that all data sources were reviewed"""
        checks = {}
        
        for source in self.REQUIRED_DATA_SOURCES:
            checks[source] = source in self.data_sources_checked
        
        checks['all_sources_complete'] = all(checks.values())
        
        return checks
    
    def verify_results_produced(self) -> Dict:
        """Verify that each step produced a result"""
        return {
            'emails_found': len(self.emails_found) > 0,
            'emails_cleaned': self.emails_cleaned if len(self.emails_found) > 0 else True,
            'no_email_reason_provided': self.no_email_reason is not None if len(self.emails_found) == 0 else True,
            'no_steps_skipped': len(self.failures) == 0
        }
    
    def get_completion_status(self) -> str:
        """Get overall completion status"""
        website_scan = self.verify_website_scan_complete()
        data_sources = self.verify_data_sources_complete()
        results = self.verify_results_produced()
        
        if (website_scan['all_pages_complete'] and 
            data_sources['all_sources_complete'] and 
            all(results.values())):
            return "COMPLETED: All checks completed successfully"
        else:
            return "INCOMPLETE: Some checks were not completed"
    
    def get_incomplete_steps(self) -> List[str]:
        """Get list of incomplete steps"""
        incomplete = []
        
        # Check pages
        website_scan = self.verify_website_scan_complete()
        if not website_scan['homepage_scanned']:
            incomplete.append("Homepage not scanned")
        if not website_scan['internal_links_checked']:
            incomplete.append("Internal links (depth 2) not checked")
        
        for page, checked in website_scan['target_pages_checked'].items():
            if not checked:
                incomplete.append(f"Page '{page}' not scanned")
        
        # Check data sources
        data_sources = self.verify_data_sources_complete()
        for source, checked in data_sources.items():
            if source != 'all_sources_complete' and not checked:
                incomplete.append(f"Data source '{source}' not checked")
        
        # Check results
        results = self.verify_results_produced()
        if not results['emails_cleaned'] and len(self.emails_found) > 0:
            incomplete.append("Emails found but not cleaned/formatted")
        if not results['no_email_reason_provided'] and len(self.emails_found) == 0:
            incomplete.append("No emails found but no reason provided")
        
        return incomplete
    
    def get_failed_steps(self) -> List[Dict]:
        """Get list of failed steps with details"""
        failed = []
        
        # Check page failures
        for page_name, result in self.pages_scanned.items():
            if result.status == CheckStatus.FAILED:
                failed.append({
                    'type': 'page_scan',
                    'name': page_name,
                    'url': result.url,
                    'reason': result.failure_reason.value if result.failure_reason else 'unknown'
                })
        
        # Check data source failures
        for source_name, check in self.data_sources_checked.items():
            if check.status == CheckStatus.FAILED:
                failed.append({
                    'type': 'data_source',
                    'name': source_name,
                    'reason': check.failure_reason.value if check.failure_reason else 'unknown'
                })
        
        return failed
    
    def get_diagnostics(self) -> Dict:
        """Get internal diagnostics"""
        diagnostics = {
            'total_pages_scanned': len(self.pages_scanned),
            'total_data_sources_checked': len(self.data_sources_checked),
            'total_emails_found': len(self.emails_found),
            'total_failures': len(self.failures),
            'slow_operations': len(self.slow_operations),
            'repeated_failures': self.repeated_failures,
            'recommendations': []
        }
        
        # Generate recommendations
        if len(self.failures) > 5:
            diagnostics['recommendations'].append("High failure rate - consider checking network/proxy")
        
        if len(self.slow_operations) > 3:
            diagnostics['recommendations'].append("Multiple slow operations - consider increasing timeout")
        
        for key, count in self.repeated_failures.items():
            if count > 2:
                diagnostics['recommendations'].append(f"Repeated failure: {key} ({count} times) - needs investigation")
        
        incomplete = self.get_incomplete_steps()
        if incomplete:
            diagnostics['recommendations'].append(f"Retry incomplete steps: {', '.join(incomplete[:3])}")
        
        return diagnostics
    
    # ========================================================================
    # REPORT GENERATION
    # ========================================================================
    
    def generate_report(self) -> str:
        """Generate comprehensive verification report"""
        self.completion_time = datetime.now()
        elapsed = (self.completion_time - self.start_time).total_seconds()
        
        report = []
        report.append("=" * 80)
        report.append("EMAIL DISCOVERY VERIFICATION REPORT")
        report.append("=" * 80)
        report.append(f"URL: {self.base_url}")
        report.append(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"End Time: {self.completion_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Duration: {elapsed:.2f} seconds")
        report.append("")
        
        # Overall Status
        report.append("=" * 80)
        report.append("OVERALL STATUS")
        report.append("=" * 80)
        status = self.get_completion_status()
        report.append(f"Status: {status}")
        report.append("")
        
        # Website Scan Verification
        report.append("=" * 80)
        report.append("1. WEBSITE SCAN VERIFICATION")
        report.append("=" * 80)
        website_scan = self.verify_website_scan_complete()
        report.append(f"✓ Homepage Scanned: {'YES' if website_scan['homepage_scanned'] else 'NO'}")
        report.append(f"✓ Internal Links (Depth 2) Checked: {'YES' if website_scan['internal_links_checked'] else 'NO'}")
        if website_scan['internal_links_checked']:
            report.append(f"  - Links Found: {len(self.internal_links_found)}")
        report.append("")
        report.append("Target Pages:")
        for page, checked in website_scan['target_pages_checked'].items():
            status_icon = "✓" if checked else "✗"
            report.append(f"  {status_icon} {page}: {'CHECKED' if checked else 'NOT CHECKED'}")
        report.append("")
        
        # Data Sources Verification
        report.append("=" * 80)
        report.append("2. DATA SOURCES VERIFICATION")
        report.append("=" * 80)
        data_sources = self.verify_data_sources_complete()
        for source in self.REQUIRED_DATA_SOURCES:
            checked = data_sources[source]
            status_icon = "✓" if checked else "✗"
            emails_found = ""
            if checked and source in self.data_sources_checked:
                count = self.data_sources_checked[source].emails_found
                if count > 0:
                    emails_found = f" ({count} emails found)"
            report.append(f"  {status_icon} {source}: {'CHECKED' if checked else 'NOT CHECKED'}{emails_found}")
        report.append("")
        
        # Results Verification
        report.append("=" * 80)
        report.append("3. RESULTS VERIFICATION")
        report.append("=" * 80)
        results = self.verify_results_produced()
        report.append(f"✓ Emails Found: {len(self.emails_found)}")
        if len(self.emails_found) > 0:
            report.append(f"✓ Emails Cleaned/Formatted: {'YES' if results['emails_cleaned'] else 'NO'}")
            report.append("  Found Emails:")
            for email in sorted(self.emails_found):
                report.append(f"    - {email}")
        else:
            report.append(f"✓ No Email Reason Provided: {'YES' if results['no_email_reason_provided'] else 'NO'}")
            if self.no_email_reason:
                report.append(f"  Reason: {self.no_email_reason}")
        report.append("")
        
        # Failures
        if self.failures:
            report.append("=" * 80)
            report.append("4. FAILURES TRACKED")
            report.append("=" * 80)
            failed_steps = self.get_failed_steps()
            for failure in failed_steps:
                report.append(f"  ✗ {failure['type']}: {failure['name']}")
                report.append(f"    Reason: {failure['reason']}")
                if 'url' in failure:
                    report.append(f"    URL: {failure['url']}")
            report.append("")
        
        # Incomplete Steps
        incomplete = self.get_incomplete_steps()
        if incomplete:
            report.append("=" * 80)
            report.append("5. INCOMPLETE STEPS")
            report.append("=" * 80)
            for step in incomplete:
                report.append(f"  ⚠ {step}")
            report.append("")
        
        # Diagnostics
        report.append("=" * 80)
        report.append("6. DIAGNOSTICS")
        report.append("=" * 80)
        diagnostics = self.get_diagnostics()
        report.append(f"Total Pages Scanned: {diagnostics['total_pages_scanned']}")
        report.append(f"Total Data Sources Checked: {diagnostics['total_data_sources_checked']}")
        report.append(f"Total Emails Found: {diagnostics['total_emails_found']}")
        report.append(f"Total Failures: {diagnostics['total_failures']}")
        report.append(f"Slow Operations: {diagnostics['slow_operations']}")
        
        if diagnostics['slow_operations'] > 0:
            report.append("\nSlow Operations:")
            for op in self.slow_operations:
                report.append(f"  - {op['operation']}: {op['time']:.2f}s")
        
        if diagnostics['repeated_failures']:
            report.append("\nRepeated Failures:")
            for key, count in diagnostics['repeated_failures'].items():
                report.append(f"  - {key}: {count} times")
        
        if diagnostics['recommendations']:
            report.append("\nRecommendations:")
            for rec in diagnostics['recommendations']:
                report.append(f"  → {rec}")
        report.append("")
        
        # Final Summary
        report.append("=" * 80)
        report.append("FINAL SUMMARY")
        report.append("=" * 80)
        report.append(f"Status: {status}")
        report.append(f"Emails Found: {len(self.emails_found)}")
        report.append(f"Pages Scanned: {len(self.pages_scanned)}/{len(self.REQUIRED_PAGES)}")
        report.append(f"Data Sources Checked: {len(self.data_sources_checked)}/{len(self.REQUIRED_DATA_SOURCES)}")
        report.append(f"Failures: {len(self.failures)}")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_report(self, filename: str = None):
        """Save report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"email_verification_{timestamp}.txt"
        
        report = self.generate_report()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return filename


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example usage
    tracker = EmailVerificationTracker("https://example.com")
    
    # Mark homepage scanned
    tracker.mark_homepage_scanned(success=True, scan_time=2.5)
    
    # Mark pages scanned
    tracker.mark_page_scanned("contact", "https://example.com/contact", 
                             success=True, emails_found=2, scan_time=3.1)
    tracker.mark_page_scanned("about", "https://example.com/about", 
                             success=True, scan_time=2.8)
    tracker.mark_page_scanned("support", "https://example.com/support", 
                             success=False, failure_reason=FailureReason.PAGE_BLOCKED)
    
    # Mark internal links checked
    tracker.mark_internal_links_checked([
        "https://example.com/products",
        "https://example.com/services"
    ])
    
    # Mark data sources checked
    tracker.mark_data_source_checked("visible_text", success=True, emails_found=1)
    tracker.mark_data_source_checked("mailto_links", success=True, emails_found=2)
    tracker.mark_data_source_checked("contact_forms", success=True)
    tracker.mark_data_source_checked("meta_tags", success=True)
    
    # Add emails
    tracker.add_emails(["contact@example.com", "support@example.com"])
    tracker.mark_emails_cleaned()
    
    # Generate and print report
    print(tracker.generate_report())
    
    # Save to file
    filename = tracker.save_report()
    print(f"\nReport saved to: {filename}")
