# How Your Scraper Works on Apify

## 🎯 Overview

Apify is a cloud platform for web scraping and automation. Your scraper becomes an **"Actor"** - a serverless application that runs in the cloud.

---

## 📊 Visual Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    APIFY PLATFORM                            │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  1. USER INPUT (Web UI or API)                     │    │
│  │     {                                               │    │
│  │       "urls": ["https://example.com"],             │    │
│  │       "maxConcurrency": 10,                        │    │
│  │       "depth": 2                                    │    │
│  │     }                                               │    │
│  └────────────────────────────────────────────────────┘    │
│                          ↓                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  2. YOUR ACTOR STARTS                              │    │
│  │     - Loads your Python code                       │    │
│  │     - Reads input                                   │    │
│  │     - Initializes scraper                          │    │
│  └────────────────────────────────────────────────────┘    │
│                          ↓                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  3. SCRAPING PROCESS                               │    │
│  │     - Visits websites                              │    │
│  │     - Extracts emails, phones, etc.                │    │
│  │     - Handles errors and retries                   │    │
│  │     - Saves progress                               │    │
│  └────────────────────────────────────────────────────┘    │
│                          ↓                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  4. RESULTS SAVED                                  │    │
│  │     ┌──────────────────┐                           │    │
│  │     │  DATASET         │ ← Scraped data (JSON/CSV) │    │
│  │     └──────────────────┘                           │    │
│  │     ┌──────────────────┐                           │    │
│  │     │  KEY-VALUE STORE │ ← Logs, resume data      │    │
│  │     └──────────────────┘                           │    │
│  └────────────────────────────────────────────────────┘    │
│                          ↓                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  5. USER GETS RESULTS                              │    │
│  │     - Download as JSON/CSV/Excel                   │    │
│  │     - View in web interface                        │    │
│  │     - Access via API                               │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Step-by-Step: How It Works

### Step 1: User Provides Input

**Via Web UI:**
```
User goes to: https://console.apify.com/actors/YOUR_ACTOR_ID
Fills in form:
  - URLs: https://example.com, https://another.com
  - Max Concurrency: 10
  - Depth: 2
Clicks "Start"
```

**Via API:**
```bash
curl -X POST https://api.apify.com/v2/acts/YOUR_ACTOR_ID/runs \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{
    "urls": ["https://example.com"],
    "maxConcurrency": 10
  }'
```

---

### Step 2: Apify Starts Your Actor

```python
# Your main.py runs automatically
async with Actor:
    # Get input
    actor_input = await Actor.get_input()
    # actor_input = {"urls": ["https://example.com"], ...}
    
    # Your scraper starts
    scraper = WebsiteEmailScraper(config)
```

**What Apify Provides:**
- ✅ Cloud server (CPU, RAM)
- ✅ Headless browser (Playwright/Puppeteer)
- ✅ Proxy servers (optional)
- ✅ Storage (Dataset, Key-Value Store)
- ✅ Monitoring and logs

---

### Step 3: Scraping Happens

```python
# Your scraper runs in the cloud
for url in urls:
    # Scrape website
    data = await scraper.scrape_single_url(url)
    
    # Save to Apify Dataset (automatically synced)
    await Actor.push_data(data)
    
    # Save progress (for resume capability)
    await Actor.set_value('PROGRESS', progress_data)
```

**What Happens:**
1. Your scraper visits websites
2. Extracts emails, phones, addresses, socials
3. Handles popups automatically
4. Retries on failures
5. Saves results incrementally
6. Tracks progress

---

### Step 4: Results Are Saved

**Dataset (Main Results):**
```json
[
  {
    "url": "https://example.com",
    "emails": ["contact@example.com"],
    "phones": ["+1-555-123-4567"],
    "address": "123 Main St, City, State",
    "social_links": {...},
    "confidence_score": 0.95
  },
  {
    "url": "https://another.com",
    ...
  }
]
```

**Key-Value Store (Logs & Progress):**
```json
{
  "PROGRESS": {
    "processed": 50,
    "total": 100,
    "percentage": 50
  },
  "FAILED_URLS": [
    {"url": "https://failed.com", "reason": "timeout"}
  ],
  "FINAL_REPORT": {
    "total_urls": 100,
    "successful": 95,
    "failed": 5
  }
}
```

---

### Step 5: User Gets Results

**Download Options:**
- 📥 JSON file
- 📥 CSV file
- 📥 Excel file
- 📥 RSS feed
- 🔗 API access

**View in Browser:**
```
https://console.apify.com/actors/YOUR_ACTOR_ID/runs/LATEST/dataset
```

---

## 💰 Pricing Model

### How Apify Charges:

**Compute Units (CU):**
- 1 CU = 1 hour of 1 CPU core + 1 GB RAM
- Example: Scraping 100 URLs might use 0.5 CU ($0.25)

**Free Tier:**
- $5 free credits per month
- ~20 CU hours free
- Good for testing and small projects

**Paid Plans:**
- Starter: $49/month (200 CU)
- Team: $499/month (2,500 CU)
- Enterprise: Custom pricing

---

## 🎨 User Experience

### For End Users (Non-Technical):

**1. Find Your Actor:**
```
https://apify.com/store
Search: "Website Email Scraper"
Click: Your Actor
```

**2. Configure & Run:**
```
┌─────────────────────────────────────┐
│  Website Email Scraper              │
│                                     │
│  URLs to scrape:                    │
│  ┌───────────────────────────────┐ │
│  │ https://example.com           │ │
│  │ https://another.com           │ │
│  └───────────────────────────────┘ │
│                                     │
│  Max Concurrency: [10]             │
│  Depth: [2]                        │
│                                     │
│  [Start] [Schedule]                │
└─────────────────────────────────────┘
```

**3. Monitor Progress:**
```
┌─────────────────────────────────────┐
│  Run Status: Running...             │
│  Progress: 45/100 URLs (45%)        │
│  Duration: 2m 30s                   │
│  Emails Found: 67                   │
│  [View Log] [Stop]                  │
└─────────────────────────────────────┘
```

**4. Download Results:**
```
┌─────────────────────────────────────┐
│  Run Completed! ✓                   │
│  Duration: 5m 12s                   │
│  URLs Processed: 100                │
│  Emails Found: 142                  │
│                                     │
│  [Download JSON] [Download CSV]     │
│  [Download Excel] [View Dataset]    │
└─────────────────────────────────────┘
```

---

## 🔧 Technical Details

### Your Code Structure on Apify:

```
YOUR_ACTOR/
├── main.py                 # Entry point (runs automatically)
├── scraper.py             # Your scraper code
├── ultimate_scraper_optimized.py
├── email_verification.py
├── requirements.txt       # Python dependencies
└── .actor/
    ├── actor.json        # Actor metadata
    └── input_schema.json # Input form definition
```

### What Apify Does Automatically:

1. **Installs Dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Runs Your Code:**
   ```bash
   python main.py
   ```

3. **Provides Environment:**
   - Headless browser
   - Proxy servers (if enabled)
   - Storage APIs
   - Monitoring

4. **Handles Scaling:**
   - Automatically scales resources
   - Manages memory
   - Handles crashes and restarts

---

## 📊 Example: Scraping 1,000 URLs

### Timeline:

```
0:00 - Actor starts
0:01 - Loads dependencies
0:02 - Begins scraping (10 concurrent)
0:05 - 100 URLs processed (10%)
0:10 - 200 URLs processed (20%)
...
0:50 - 1,000 URLs processed (100%)
0:51 - Generates final report
0:52 - Actor finishes
```

### Resources Used:
- **Time:** ~50 minutes
- **Compute:** ~0.8 CU
- **Cost:** ~$0.40
- **Results:** 1,000 websites scraped, ~500 emails found

---

## 🎯 Key Benefits

### For You (Developer):
✅ **No Server Management** - Apify handles infrastructure
✅ **Automatic Scaling** - Handles 1 or 10,000 URLs
✅ **Built-in Storage** - Dataset and Key-Value Store
✅ **Monitoring** - Logs, metrics, alerts
✅ **Marketplace** - Sell your Actor to others

### For Users:
✅ **Easy to Use** - Web interface, no coding
✅ **Reliable** - Automatic retries and error handling
✅ **Fast** - Parallel processing
✅ **Flexible** - API access, scheduling, webhooks

---

## 🚀 Deployment Process

### 1. Prepare Your Code:
```bash
# Your project structure
website-scraper/
├── main.py                    # Apify entry point
├── scraper.py                 # Your scraper
├── ultimate_scraper_optimized.py
├── requirements.txt
└── .actor/
    ├── actor.json
    └── input_schema.json
```

### 2. Push to Apify:
```bash
# Install Apify CLI
npm install -g apify-cli

# Login
apify login

# Create Actor
apify create

# Push code
apify push
```

### 3. Test:
```bash
# Run locally
apify run

# Run on Apify
apify call
```

### 4. Publish:
```
Go to: https://console.apify.com/actors/YOUR_ACTOR_ID
Click: "Publish to Store"
Set price (free or paid)
Submit for review
```

---

## 💡 Real-World Example

### Scenario: Marketing Agency

**Need:** Scrape 5,000 company websites to find contact emails

**Process:**
1. Upload CSV with 5,000 URLs to Apify
2. Configure Actor: maxConcurrency=20, depth=2
3. Click "Start"
4. Wait ~2 hours
5. Download results as Excel
6. Import to CRM

**Results:**
- 5,000 websites scraped
- 3,200 emails found
- 800 phone numbers found
- Cost: ~$2.00
- Time saved: 100+ hours of manual work

---

## 🎉 Summary

**How It Works:**
1. User provides URLs via web UI or API
2. Apify starts your Actor in the cloud
3. Your scraper runs and extracts data
4. Results saved to Dataset automatically
5. User downloads results (JSON/CSV/Excel)

**Key Features:**
- ✅ Runs in cloud (no local setup needed)
- ✅ Handles 1 to 10,000+ URLs
- ✅ Automatic retries and error handling
- ✅ Resume capability if interrupted
- ✅ Easy to use for non-technical users
- ✅ Can be sold on Apify Marketplace

**Your scraper becomes a professional, scalable service that anyone can use!** 🚀
