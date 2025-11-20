# 🚀 Deploy to Apify - Fixed Configuration

## What Was Wrong?

The Actor configuration files were in `.actor/` directory, but Apify needs them in the **root directory**. I've now created:

- ✅ `Dockerfile` (root)
- ✅ `actor.json` (root)
- ✅ `input_schema.json` (root)

## Deploy Steps

### 1. Push to Apify

```bash
# Make sure you're in the project directory
apify push
```

### 2. Run Your Actor

1. Go to Apify Console: https://console.apify.com
2. Find your Actor: "website-email-scraper"
3. Click **"Start"**
4. You'll see the **Input Form**

### 3. Add URLs in the Input Form

In the "URLs to Scrape" field, click **"Add URL"** and enter:

```
https://example.com
https://another-site.com
https://yourwebsite.com
```

Or use the JSON input tab:

```json
{
  "urls": [
    "https://example.com",
    "https://another-site.com"
  ],
  "maxConcurrency": 10,
  "depth": 2,
  "extractEmails": true,
  "extractPhones": true,
  "extractAddresses": true,
  "extractSocials": true
}
```

### 4. Click "Start" at the Bottom

The Actor will now:
- ✅ Run your Python code (not JavaScript)
- ✅ Scrape all URLs you provided
- ✅ Save results to Dataset
- ✅ Show progress in logs

### 5. View Results

After completion:
- Click **"Dataset"** tab to see scraped data
- Click **"Key-Value Store"** to see reports
- Download as CSV, JSON, or Excel

## What Changed?

### Before (Wrong):
```
.actor/
  ├── Dockerfile        ❌ Wrong location
  ├── actor.json        ❌ Wrong location
  └── input_schema.json ❌ Wrong location
```

### After (Correct):
```
project-root/
  ├── Dockerfile        ✅ Correct location
  ├── actor.json        ✅ Correct location
  ├── input_schema.json ✅ Correct location
  ├── apify_main.py     ✅ Entry point
  ├── scraper.py        ✅ Core logic
  └── requirements.txt  ✅ Dependencies
```

## Troubleshooting

### Still seeing "main.js" error?
- Make sure you pushed the latest code: `apify push`
- Check that `Dockerfile` exists in root directory
- Rebuild the Actor in Apify Console

### Empty results?
- Make sure you added URLs in the input form
- Check the logs for errors
- Verify URLs are accessible

### Need help?
Check the logs in Apify Console for detailed error messages.

## Quick Test

Test locally first:
```bash
python apify_main.py
```

This will use `apify_input.json` for testing before deploying.
