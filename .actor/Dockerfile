# Use Apify's Python + Playwright base image
FROM apify/actor-python-playwright:3.11

# Copy all project files
COPY . ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Run the Actor
CMD ["python", "-u", "apify_main.py"]
