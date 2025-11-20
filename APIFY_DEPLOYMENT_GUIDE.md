# Apify Deployment Guide

## 🚀 Complete Guide to Deploy Your Scraper on Apify

This guide will walk you through deploying your website scraper as an Apify Actor.

---

## ✅ **What's Ready for Deployment**

Your project now includes:

```
✅ apify_main.py              - Main entry point
✅ scraper.py                 - Core scraping logic
✅ ultimate_scraper_optimized.py - Optimized scraper
✅ email_verification.py      - Verification system
✅ .actor/actor.json          - Actor configuration
✅ .actor/input_schema.json   - Input form definition
✅ .actor/Dockerfile          - Container setup
✅ .actor/requirements.txt    - Dependencies
✅ .actor/README.md           - Actor documentation
✅ apify_input.json           - Sample input for testing
```

---

## 📋 **Prerequisites**

### 1. Create Apify Account
```
1. Go to: https://apify.com/sign-up
2. Sign up (free tier available)
3. Verify your email
```

### 2. Install Apify CLI
```bash
npm install -g apify-cli
```

### 3. Login to Apify
```bash
apify login
```
(This will open a browser to authenticate)

---

## 🧪 **Step 1: Test Locally First**

Before deploying, test locally to make sure everything works:

### Install Dependencies
```bash
pip install apify playwright beautifulsoup4 aiohttp
playwright install chromium
```

### Run Local Test
```bash
python apify_main.py
```

This will:
- Read `apify_input.json`
- Scrape the URLs
- Save results to `apify_results.json`
- Generate `final_report.json`

**Check the output files to verify everything works!**

---

## 🚀 **Step 2: Deploy to Apify**

### Method 1: Using Apify CLI (Recommended)

#### 1. Initialize Actor
```bash
# In your project directory
apify init
```

When prompted:
- Actor name: `website-email-scraper`
- Template: Skip (we already have files)

#### 2. Update apify.json
The CLI creates `apify.json`. Update it:
```json
{
  "name": "website-email-scraper",
  "version": "1.0.0",
  "buildTag": "latest",
  "env": {},
  "template": "python"
}
```

#### 3. Push to Apify
```bash
apify push
```

This will:
- Upload all your files
- Build the Docker container
- Deploy the Actor

#### 4. Test on Apify
```bash
apify call
```

Or go to:
```
https://console.apify.com/actors
```

---

### Method 2: Using Apify Console (Web UI)

#### 1. Create New Actor
```
1. Go to: https://console.apify.com/actors
2. Click "Create new"
3. Choose "Empty Actor"
4. Name it: "website-email-scraper"
```

#### 2. Upload Files
```
1. Go to "Source" tab
2. Upload these files:
   - apify_main.py
   - scraper.py
   - ultimate_scraper_optimized.py
   - email_verification.py
   - .actor/actor.json
   - .actor/input_schema.json
   - .actor/Dockerfile
   - .actor/requirements.txt
   - .actor/README.md
```

#### 3. Set Entry Point
```
In "Source" tab:
- Dockerfile: .actor/Dockerfile
- Main file: apify_main.py
```

#### 4. Build & Run
```
1. Click "Build"
2. Wait for build to complete
3. Click "Start"
4. Enter test URLs
5. Click "Run"
```

---

## 🎯 **Step 3: Configure Your Actor**

### Set Actor Details

Go to "Settings" tab:

```
Name: Website & Email Scraper
Title: Professional Website & Email Scraper
Description: Fast and accurate scraper for emails, phones, addresses, and social links
Categories: Business, Lead Generation, E-commerce
```

### Set Pricing (Optional)

If you want to sell your Actor:

```
Free tier: 100 runs/month
Paid tier: $0.01 per run
```

---

## 🧪 **Step 4: Test Your Actor**

### Test with Sample Input

```json
{
  "urls": [
    "https://example.com",
    "https://httpbin.org/html"
  ],
  "maxConcurrency": 5,
  "depth": 2
}
```

### Check Results

1. **Dataset** - View scraped data
2. **Log** - Check for errors
3. **Key-Value Store** - View progress and reports

---

## 📊 **Step 5: Monitor Performance**

### Check Metrics

```
- Run duration
- Memory usage
- Compute units used
- Success rate
```

### Optimize if Needed

If too slow:
- Increase `maxConcurrency`
- Decrease `depth`
- Enable proxy

If using too much memory:
- Decrease `maxConcurrency`
- Add memory limits

---

## 🎨 **Step 6: Publish to Marketplace (Optional)**

### Make it Public

```
1. Go to "Publication" tab
2. Fill in:
   - Description
   - Screenshots
   - Use cases
   - Pricing
3. Click "Submit for review"
```

### Apify will review (1-3 days)

Once approved, your Actor will be in the Apify Store!

---

## 🔧 **Troubleshooting**

### Build Fails

**Problem:** Docker build fails

**Solution:**
```bash
# Check Dockerfile syntax
cat .actor/Dockerfile

# Check requirements.txt
cat .actor/requirements.txt

# Test locally first
docker build -f .actor/Dockerfile .
```

### Actor Crashes

**Problem:** Actor starts but crashes

**Solution:**
```bash
# Check logs in Apify Console
# Look for Python errors
# Test locally first:
python apify_main.py
```

### No Results

**Problem:** Actor runs but no data

**Solution:**
- Check input URLs are valid
- Check logs for errors
- Test with simple URL like https://example.com
- Verify scraper.py is working locally

### Timeout Issues

**Problem:** Pages timing out

**Solution:**
- Increase `timeout` parameter
- Enable `useProxy`
- Check if websites are blocking

---

## 📁 **File Structure for Deployment**

```
your-project/
├── apify_main.py                 # ← Main entry point
├── scraper.py                    # ← Core scraper
├── ultimate_scraper_optimized.py # ← Optimized scraper
├── email_verification.py         # ← Verification
├── .actor/
│   ├── actor.json               # ← Actor config
│   ├── input_schema.json        # ← Input form
│   ├── Dockerfile               # ← Container
│   ├── requirements.txt         # ← Dependencies
│   └── README.md                # ← Documentation
├── apify_input.json             # ← Test input
└── apify.json                   # ← CLI config (created by apify init)
```

---

## 🎯 **Quick Deployment Checklist**

```
☐ 1. Test locally (python apify_main.py)
☐ 2. Install Apify CLI (npm install -g apify-cli)
☐ 3. Login (apify login)
☐ 4. Initialize (apify init)
☐ 5. Push to Apify (apify push)
☐ 6. Test on Apify (apify call)
☐ 7. Configure settings
☐ 8. Publish (optional)
```

---

## 💰 **Cost Estimation**

### Free Tier
- $5 free credits/month
- ~20 compute unit hours
- Good for ~1000-5000 URLs/month

### Paid Plans
- Starter: $49/month (200 CU)
- Team: $499/month (2,500 CU)
- Enterprise: Custom

### Per-Run Cost
- Small (1-10 URLs): ~$0.01-$0.05
- Medium (10-100 URLs): ~$0.05-$0.25
- Large (100-1000 URLs): ~$0.50-$2.50

---

## 🎉 **You're Ready to Deploy!**

### Quick Deploy Commands

```bash
# 1. Test locally
python apify_main.py

# 2. Initialize
apify init

# 3. Deploy
apify push

# 4. Test
apify call

# 5. View in browser
apify open
```

---

## 🆘 **Need Help?**

- **Apify Docs:** https://docs.apify.com
- **Apify Discord:** https://discord.com/invite/jyEM2PRvMU
- **GitHub Issues:** https://github.com/Kismat-adhikari/website-scrapper/issues

---

**Your scraper is production-ready and optimized for Apify!** 🚀

Just run `apify push` and you're live!
