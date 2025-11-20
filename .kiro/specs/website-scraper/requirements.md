# Requirements Document

## Introduction

This document specifies the requirements for a Python-based website scraper that extracts comprehensive business and contact information from websites. The Scraper System uses Playwright for browser automation, supports proxy rotation, and exports data to CSV format for commercial use.

## Glossary

- **Scraper System**: The Python-based application that automates website data extraction
- **Playwright Browser**: The headful browser automation tool used for page rendering and interaction
- **Proxy Rotator**: The component that manages and rotates proxy connections from proxies.txt
- **CSV Exporter**: The component that formats and saves extracted data to results.csv
- **Data Extractor**: The component that identifies and extracts specific information from web pages
- **User**: The person operating the Scraper System via command line

## Requirements

### Requirement 1

**User Story:** As a User, I want to input a website URL via terminal prompt, so that I can specify which website to scrape

#### Acceptance Criteria

1. WHEN the Scraper System starts, THE Scraper System SHALL display the prompt "Enter the website URL to scrape:" in the terminal
2. WHEN the User enters a URL, THE Scraper System SHALL validate the URL format before proceeding
3. IF the URL format is invalid, THEN THE Scraper System SHALL display an error message and re-prompt the User
4. WHEN a valid URL is received, THE Scraper System SHALL initiate the browser automation process

### Requirement 2

**User Story:** As a User, I want to see the browser visibly operating, so that I can monitor the scraping process in real-time

#### Acceptance Criteria

1. WHEN the Scraper System launches the browser, THE Scraper System SHALL launch the Playwright Browser in headful mode
2. WHEN the page loads, THE Scraper System SHALL display the browser window to the User
3. WHILE the page is loading, THE Scraper System SHALL wait for network idle state before extraction
4. WHEN content is dynamic, THE Scraper System SHALL scroll smoothly to the bottom of the page to trigger lazy-loaded content
5. WHEN scrolling completes, THE Scraper System SHALL wait between 20 and 30 seconds maximum for all content to appear

### Requirement 3

**User Story:** As a User, I want the system to extract all contact and business information, so that I can obtain sellable lead data

#### Acceptance Criteria

1. WHEN the page is fully loaded, THE Data Extractor SHALL extract the website URL from the browser
2. WHEN extracting text data, THE Data Extractor SHALL extract the page title or business name
3. WHEN scanning page content, THE Data Extractor SHALL extract all email addresses using pattern matching
4. WHEN scanning page content, THE Data Extractor SHALL extract all phone numbers in various formats
5. WHEN identifying social media, THE Data Extractor SHALL extract links for Facebook, Instagram, Twitter, TikTok, LinkedIn, YouTube, Pinterest, and Snapchat
6. WHEN analyzing links, THE Data Extractor SHALL extract all external links excluding internal navigation links
7. WHEN reading metadata, THE Data Extractor SHALL extract the meta description tag content
8. WHEN scanning visible content, THE Data Extractor SHALL extract description sections from the page body
9. WHEN identifying location data, THE Data Extractor SHALL extract address or location text
10. WHEN finding contact methods, THE Data Extractor SHALL extract WhatsApp links
11. WHEN finding contact methods, THE Data Extractor SHALL extract Telegram links
12. WHEN extraction completes, THE Data Extractor SHALL record the scrape timestamp in ISO format

### Requirement 4

**User Story:** As a User, I want the system to infer additional business intelligence, so that I can increase the value of the extracted data

#### Acceptance Criteria

1. WHEN analyzing page content, THE Data Extractor SHALL infer the industry or category using keyword analysis
2. WHEN scanning page elements, THE Data Extractor SHALL detect the presence of contact forms and record true or false
3. WHEN processing page text, THE Data Extractor SHALL calculate the estimated word count of visible content
4. WHEN analyzing site structure, THE Data Extractor SHALL detect if a blog section exists and record true or false
5. WHEN analyzing page content, THE Data Extractor SHALL detect if products or services are mentioned and record true or false

### Requirement 5

**User Story:** As a User, I want to use rotating proxies from a file, so that I can avoid IP blocking and rate limiting

#### Acceptance Criteria

1. WHEN the Scraper System initializes, THE Proxy Rotator SHALL read proxy configurations from proxies.txt in the working directory
2. WHEN parsing proxy entries, THE Proxy Rotator SHALL detect and parse format "ip:port"
3. WHEN parsing proxy entries, THE Proxy Rotator SHALL detect and parse format "ip:port:user:pass"
4. WHEN parsing proxy entries, THE Proxy Rotator SHALL detect and parse format "http://ip:port"
5. WHEN parsing proxy entries, THE Proxy Rotator SHALL detect and parse format "http://user:pass@ip:port"
6. WHEN selecting a proxy, THE Proxy Rotator SHALL rotate to the next proxy for each scraping run
7. IF a proxy connection fails, THEN THE Proxy Rotator SHALL automatically retry with the next available proxy
8. WHEN configuring the browser, THE Proxy Rotator SHALL apply the selected proxy to the Playwright Browser instance

### Requirement 6

**User Story:** As a User, I want the system to handle failures gracefully, so that partial data is not lost and the system remains stable

#### Acceptance Criteria

1. IF a page fails to load, THEN THE Scraper System SHALL retry the request up to 3 times
2. WHEN any operation exceeds 30 seconds, THE Scraper System SHALL timeout and proceed with available data
3. IF no emails are found, THEN THE Data Extractor SHALL record "NONE" in the emails field
4. IF no phone numbers are found, THEN THE Data Extractor SHALL record "NONE" in the phones field
5. WHEN extracting text, THE Data Extractor SHALL strip whitespace and remove duplicate entries
6. WHEN extracting emails and links, THE Data Extractor SHALL normalize formatting for consistency
7. IF an error occurs during extraction, THEN THE Scraper System SHALL log the error and continue with remaining fields
8. WHEN the scraping process completes or fails, THE Scraper System SHALL close the Playwright Browser

### Requirement 7

**User Story:** As a User, I want all extracted data saved to a CSV file, so that I can use the data in other applications

#### Acceptance Criteria

1. WHEN data extraction completes, THE CSV Exporter SHALL save data to a file named results.csv in the working directory
2. IF results.csv already exists, THEN THE CSV Exporter SHALL append new rows without overwriting existing data
3. WHEN creating the CSV, THE CSV Exporter SHALL use the following column order: url, title, emails, phones, social_links, external_links, description, meta_description, address, whatsapp, telegram, contact_form, industry, blog_present, products_or_services, word_count, scrape_timestamp
4. WHEN writing data, THE CSV Exporter SHALL properly escape special characters and handle multi-value fields
5. WHEN the file is saved, THE CSV Exporter SHALL verify the write operation succeeded
6. IF the CSV write fails, THEN THE Scraper System SHALL display an error message with details

### Requirement 8

**User Story:** As a User, I want clear terminal output showing scraping progress and results, so that I can understand what data was collected

#### Acceptance Criteria

1. WHILE scraping is in progress, THE Scraper System SHALL display status messages for each major operation
2. WHEN data extraction completes, THE Scraper System SHALL display a summary of extracted data in the terminal
3. WHEN displaying the summary, THE Scraper System SHALL show each data category with found values or "None detected"
4. WHEN the scraping completes successfully, THE Scraper System SHALL print a clean success message
5. WHEN displaying output, THE Scraper System SHALL format text for readability with proper spacing and alignment
6. IF an error occurs, THEN THE Scraper System SHALL display a clear error message without exposing technical stack traces to the User

### Requirement 9

**User Story:** As a User, I want to run the scraper with a single command, so that I can easily execute the tool without complex setup

#### Acceptance Criteria

1. WHEN the User executes the Python file, THE Scraper System SHALL run without requiring additional command-line arguments
2. THE Scraper System SHALL include all necessary dependencies in a requirements.txt file or document them clearly
3. THE Scraper System SHALL be contained in a single Python file for simplicity
4. WHEN the code is reviewed, THE Scraper System SHALL include comments explaining key functionality
5. WHEN the code is reviewed, THE Scraper System SHALL follow Python best practices and production-grade standards
