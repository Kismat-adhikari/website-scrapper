# Implementation Plan

- [x] 1. Set up project structure and dependencies



  - Create scraper.py as the main single-file application
  - Create requirements.txt with playwright, pytest, and hypothesis
  - Add installation instructions in comments
  - _Requirements: 9.2, 9.3_

- [x] 2. Implement proxy management system


  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_

- [ ] 2.1 Create proxy parsing and loading functions
  - Write `load_proxies()` to read from proxies.txt


  - Write `parse_proxy_line()` to detect and parse all four proxy formats
  - Write `format_proxy_for_playwright()` to convert to Playwright config


  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 2.2 Write property test for proxy format parsing



  - **Property 19: Proxy format parsing completeness**
  - **Validates: Requirements 5.2, 5.3, 5.4, 5.5**

- [x] 2.3 Implement proxy rotation logic


  - Write `get_next_proxy()` with rotation index tracking
  - Implement retry logic for failed proxy connections
  - _Requirements: 5.6, 5.7_



- [x] 2.4 Write property test for proxy rotation

  - **Property 20: Proxy rotation sequence**
  - **Validates: Requirements 5.6**

- [ ] 3. Implement URL validation and user input
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 3.1 Create URL validation function





  - Write `validate_url()` using regex for URL format checking
  - Support http:// and https:// protocols
  - _Requirements: 1.2_




- [x] 3.2 Write property test for URL validation

  - **Property 1: URL validation correctness**
  - **Validates: Requirements 1.2**

- [x] 3.3 Implement user input handling

  - Write `get_user_input()` to prompt for URL
  - Add error handling and re-prompting for invalid URLs
  - _Requirements: 1.1, 1.3, 1.4_


- [x] 4. Implement browser management with Playwright

  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 6.2, 6.8_

- [ ] 4.1 Create browser launch and configuration
  - Write `launch_browser()` with headful mode (headless=False)
  - Apply proxy configuration to browser context

  - Set 30-second timeout
  - _Requirements: 2.1, 5.8, 6.2_




- [ ] 4.2 Implement page loading with retry logic
  - Write `load_page()` with up to 3 retry attempts
  - Wait for network idle state before proceeding
  - Add exponential backoff between retries
  - _Requirements: 2.3, 6.1_


- [ ] 4.3 Implement smooth scrolling functionality
  - Write `scroll_to_bottom()` with incremental scrolling
  - Add delays between scroll increments (100-200ms)
  - Trigger lazy-loaded content
  - _Requirements: 2.4_



- [ ] 4.4 Add browser cleanup
  - Implement browser close in finally block
  - Ensure cleanup on both success and failure
  - _Requirements: 6.8_

- [ ] 5. Implement core data extraction functions
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12_

- [ ] 5.1 Create basic extraction functions
  - Write `extract_url()` to capture current page URL

  - Write `extract_title()` to get page title
  - Write `extract_metadata()` for meta description
  - Write timestamp generation in ISO format
  - _Requirements: 3.1, 3.2, 3.7, 3.12_


- [ ] 5.2 Write property tests for basic extraction
  - **Property 2: URL extraction preservation**
  - **Property 3: Title extraction completeness**
  - **Property 8: Meta description extraction**
  - **Property 13: Timestamp format correctness**
  - **Validates: Requirements 3.1, 3.2, 3.7, 3.12**


- [ ] 5.3 Implement contact information extraction
  - Write `extract_emails()` using regex pattern matching
  - Write `extract_phones()` for various phone formats
  - Write `extract_address()` for location text

  - _Requirements: 3.3, 3.4, 3.9_

- [ ] 5.4 Write property tests for contact extraction
  - **Property 4: Email extraction completeness**
  - **Property 5: Phone number extraction completeness**
  - **Property 10: Address extraction**
  - **Validates: Requirements 3.3, 3.4, 3.9**



- [ ] 5.5 Implement link extraction and classification
  - Write `extract_social_links()` for all specified platforms

  - Write `extract_external_links()` to filter external vs internal
  - Write `extract_messaging_links()` for WhatsApp and Telegram
  - _Requirements: 3.5, 3.6, 3.10, 3.11_

- [ ] 5.6 Write property tests for link extraction
  - **Property 6: Social media link extraction completeness**
  - **Property 7: External link classification correctness**
  - **Property 11: WhatsApp link extraction**
  - **Property 12: Telegram link extraction**
  - **Validates: Requirements 3.5, 3.6, 3.10, 3.11**

- [ ] 5.7 Implement description extraction
  - Write `extract_descriptions()` to find visible description text

  - Look for common description patterns (about, description sections)


  - _Requirements: 3.8_

- [ ] 5.8 Write property test for description extraction
  - **Property 9: Description text extraction**
  - **Validates: Requirements 3.8**

- [ ] 6. Implement business intelligence inference
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 6.1 Create inference and detection functions
  - Write `infer_industry()` using keyword analysis
  - Write `detect_contact_form()` to find form elements
  - Write `calculate_word_count()` for visible text

  - Write `detect_blog()` to identify blog indicators
  - Write `detect_products_services()` for product/service keywords

  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 6.2 Write property tests for business intelligence
  - **Property 14: Industry inference**
  - **Property 15: Contact form detection**
  - **Property 16: Word count accuracy**
  - **Property 17: Blog detection**
  - **Property 18: Product/service detection**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

- [ ] 7. Implement data cleaning and normalization
  - _Requirements: 6.3, 6.4, 6.5, 6.6_

- [x] 7.1 Create cleaning and normalization functions

  - Write `clean_text()` to strip whitespace and remove duplicates
  - Write `normalize_data()` for consistent email and link formatting
  - Implement "NONE" default for missing emails and phones
  - _Requirements: 6.3, 6.4, 6.5, 6.6_

- [ ] 7.2 Write property tests for data cleaning
  - **Property 21: Missing data default values**
  - **Property 22: Text cleaning consistency**
  - **Property 23: Data normalization consistency**
  - **Validates: Requirements 6.3, 6.4, 6.5, 6.6**

- [x] 8. Implement CSV export functionality


  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [ ] 8.1 Create CSV export functions
  - Write `save_to_csv()` to save data to results.csv
  - Write `format_list_field()` to convert lists to semicolon-delimited strings
  - Implement append mode to preserve existing data
  - Use correct column order as specified
  - Add proper CSV escaping for special characters


  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 8.2 Write property tests for CSV operations
  - **Property 24: CSV append preservation**
  - **Property 25: CSV escaping correctness**
  - **Validates: Requirements 7.2, 7.4**

- [ ] 8.3 Add CSV error handling
  - Verify write operations succeeded

  - Display error messages on write failure
  - _Requirements: 7.5, 7.6_

- [ ] 9. Implement terminal output and display
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.6_

- [x] 9.1 Create display functions

  - Write `display_summary()` to show extracted data
  - Format output with proper spacing
  - Show "None detected" for missing data categories
  - Display clean success message on completion
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 9.2 Write property test for summary display
  - **Property 26: Summary display completeness**

  - **Validates: Requirements 8.3**

- [ ] 9.3 Implement error message formatting
  - Ensure no stack traces shown to users
  - Display clear, user-friendly error messages
  - _Requirements: 8.6_


- [ ] 10. Implement error handling and resilience
  - _Requirements: 6.7_

- [ ] 10.1 Add comprehensive error handling
  - Wrap extraction functions in try-except blocks
  - Log errors and continue with remaining fields
  - Implement graceful degradation throughout
  - _Requirements: 6.7_

- [ ] 11. Integrate all components into main workflow
  - _Requirements: 9.1_

- [ ] 11.1 Create main orchestration function
  - Write `main()` to coordinate entire scraping workflow
  - Integrate: input → proxy → browser → extract → clean → export → display
  - Ensure single-command execution (no CLI arguments needed)
  - Add proper error handling at each step
  - _Requirements: 9.1_

- [ ] 11.2 Add code documentation
  - Include comments explaining key functionality
  - Document each major function
  - Add usage instructions at top of file
  - _Requirements: 9.4_

- [ ] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise
