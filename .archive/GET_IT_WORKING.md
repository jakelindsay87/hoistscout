# Get HoistScraper Working - Step by Step

## Option 1: Quick Demo (30 minutes)

### Step 1: Add Playwright to Backend
```bash
# Edit backend/Dockerfile and add after line 32:
RUN apt-get update && apt-get install -y \
    wget \
    libxss1 \
    libgconf-2-4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

RUN poetry run playwright install chromium
```

### Step 2: Rebuild and Restart
```bash
docker-compose build backend
docker-compose up -d backend
```

### Step 3: Test Scraping
```bash
# Wait for backend to start
sleep 10

# Trigger a scrape (will be slow but should work)
curl -X POST http://localhost:8000/api/scrape/2/trigger

# Check if opportunities were created
curl http://localhost:8000/api/opportunities
```

## Option 2: Proper Setup with Ollama (2 hours)

### Step 1: Stop Current Setup
```bash
docker-compose down
```

### Step 2: Start with Production Config
```bash
# This includes Ollama
docker-compose -f docker-compose.prod.yml up -d

# Pull the Mistral model
docker-compose -f docker-compose.prod.yml --profile setup up ollama-pull
```

### Step 3: Update Worker to Use V2
```bash
# Edit backend/Dockerfile.worker
# Change the last line from:
# CMD ["poetry", "run", "python", "-m", "hoistscraper.worker"]
# To:
# CMD ["poetry", "run", "python", "-m", "hoistscraper.worker_v2"]
```

### Step 4: Rebuild and Start
```bash
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Step 5: Test Full Pipeline
```bash
# Create a job
curl -X POST http://localhost:8000/api/scrape-jobs \
  -H "Content-Type: application/json" \
  -d '{"website_id": 2}'

# Check job status
curl http://localhost:8000/api/scrape-jobs

# Check opportunities (should populate after worker processes)
curl http://localhost:8000/api/opportunities
```

## Option 3: Manual Data Insert (5 minutes)

If you need to demo RIGHT NOW:

```bash
# Connect to PostgreSQL
docker exec -it hoistscraper-db psql -U postgres -d hoistscraper

# Insert test opportunities
INSERT INTO opportunity (
    title, 
    description, 
    source_url, 
    website_id, 
    job_id,
    deadline,
    amount,
    scraped_at
) VALUES 
(
    'HMAS Creswell Fire Station Remediation',
    'Fire station remediation works at HMAS Creswell, ACT. The Department of Defence is seeking experienced contractors for building construction and support services.',
    'https://www.tenders.gov.au/atm/show/EST08355',
    2,
    1,
    '2025-06-27 12:00:00',
    'Not specified',
    NOW()
),
(
    'National Police Check Systems Replacement',
    'The AFP is conducting market analysis for a possible approach to market for replacing the National Police Check systems.',
    'https://www.tenders.gov.au/atm/show/RFI-14-2025',
    2,
    1,
    '2025-06-27 15:00:00',
    '$2-5 million',
    NOW()
),
(
    'Border Protection Technologies Panel',
    'Panel for border protection technologies including x-ray scanners, trace detection, radiation detection equipment.',
    'https://www.tenders.gov.au/atm/show/HOMEAFFAIRS-2160',
    2,
    1,
    '2025-07-09 14:00:00',
    'Panel arrangement',
    NOW()
);

# Exit PostgreSQL
\q

# Now check the API
curl http://localhost:8000/api/opportunities | python3 -m json.tool
```

## Troubleshooting

### If Redis Won't Connect
```bash
# Check Redis is running
docker ps | grep redis

# Test Redis connection
docker exec -it hoistscraper-redis redis-cli ping
# Should return: PONG

# Check worker logs
docker logs hoistscraper-worker --tail 50
```

### If Ollama Won't Start
```bash
# Check if port 11434 is already in use
lsof -i:11434

# Check Ollama logs
docker logs hoistscraper-ollama

# Test Ollama directly
curl http://localhost:11434/api/tags
```

### If Frontend Won't Build
```bash
# The frontend has dependency issues, skip it for now
# Just use the API endpoints directly or build a simple HTML page
```

## Minimal HTML UI

Create `opportunities.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <title>HoistScraper Opportunities</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Grant Opportunities</h1>
    <button onclick="loadOpportunities()">Refresh</button>
    <div id="opportunities"></div>

    <script>
    async function loadOpportunities() {
        const response = await fetch('http://localhost:8000/api/opportunities');
        const data = await response.json();
        
        let html = '<table><tr><th>Title</th><th>Description</th><th>Deadline</th><th>Link</th></tr>';
        
        data.forEach(opp => {
            html += `<tr>
                <td>${opp.title}</td>
                <td>${opp.description?.substring(0, 100)}...</td>
                <td>${opp.deadline || 'Not specified'}</td>
                <td><a href="${opp.source_url}" target="_blank">View</a></td>
            </tr>`;
        });
        
        html += '</table>';
        document.getElementById('opportunities').innerHTML = html;
    }
    
    // Load on page load
    loadOpportunities();
    </script>
</body>
</html>
```

Open this file in a browser to see your opportunities!

## Summary

The quickest path to a working demo:
1. Insert manual test data (5 minutes)
2. Use the simple HTML UI above
3. Show the API working with curl commands

For production:
1. Use docker-compose.prod.yml with Ollama
2. Implement worker_v2.py
3. Build proper React frontend

The core issue is that the extraction pipeline (HTML → Opportunities) isn't implemented. Everything else works!