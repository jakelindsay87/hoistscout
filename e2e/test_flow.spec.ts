import { test, expect } from '@playwright/test';
import { execSync } from 'child_process';
import path from 'path';

// Assuming your project root is the parent directory of 'e2e'
const projectRoot = path.resolve(__dirname, '..');
const backendDir = path.join(projectRoot, 'backend'); // Assuming backend is at the root

test.describe('End-to-end test flow', () => {
  test.beforeAll(async () => {
    // Step 1: Spin up docker compose up -d
    console.log('Starting Docker containers...');
    try {
      execSync('docker compose up -d', { stdio: 'inherit', cwd: projectRoot });
      console.log('Docker containers started.');
    } catch (error) {
      console.error('Failed to start Docker containers:', error);
      // Optionally, throw the error to stop the test if Docker fails to start
      // throw new Error('Failed to start Docker containers');
    }

    // Step 2: Wait on FE 3000
    // Playwright's webServer config in playwright.config.ts usually handles this.
    // Or, we can add a manual wait/poll here if not using webServer.
    // For now, let's assume webServer handles it or add a simple delay.
    // A more robust way would be to poll the frontend URL.
    console.log('Waiting for frontend to be available on port 3000...');
    await new Promise(resolve => setTimeout(resolve, 15000)); // Adjust delay as needed
    // Add a more robust check:
    // try {
    //   await page.goto('http://localhost:3000', { waitUntil: 'networkidle', timeout: 30000 });
    //   console.log('Frontend is responsive.');
    // } catch (error) {
    //   console.error('Frontend did not become responsive in time:', error);
    //   throw new Error('Frontend not available');
    // }
    console.log('Frontend presumed available.');
  });

  test.afterAll(async () => {
    // Step 8: Shut down compose
    console.log('Shutting down Docker containers...');
    try {
      execSync('docker compose down', { stdio: 'inherit', cwd: projectRoot });
      console.log('Docker containers shut down.');
    } catch (error) {
      console.error('Failed to shut down Docker containers:', error);
    }
  });

  test('should complete the full crawl and verification flow', async ({ request, page }) => {
    const siteToCrawl = 'https://playwright.dev';

    // Step 3: POST site `https://playwright.dev`
    // Assuming your API endpoint for adding sites is /api/sites (adjust if different)
    console.log(`POSTing site: ${siteToCrawl}`);
    const postResponse = await request.post('http://localhost:8000/api/sites', {
      data: {
        url: siteToCrawl,
      },
    });
    expect(postResponse.ok(), `Failed to POST site. Status: ${postResponse.status()}`).toBeTruthy();
    const responseBody = await postResponse.json();
    // expect(responseBody).toHaveProperty('id'); // Or some other confirmation from the POST response

    console.log('Site POSTed successfully.');

    // Step 4: Run `run_crawl.py --once`
    // Assuming run_crawl.py is in the backend directory and executable
    // And that your Docker setup makes the script runnable in the container context or host
    console.log('Running crawl script...');
    try {
      // This command might need to be run inside the backend container if it depends on that environment
      execSync('docker compose exec backend python /app/scripts/run_crawl.py --once', { stdio: 'inherit', cwd: projectRoot });
      // For now, assuming it can be run from the host if the backend service is correctly set up.
      // The script path needs to be correct. If it's inside the backend dir:
      // execSync(`python ${path.join(backendDir, 'run_crawl.py')} --once`, { stdio: 'inherit', cwd: backendDir });
      console.log('Crawl script executed.');
    } catch (error) {
      console.error('Failed to execute crawl script:', error);
      throw new Error('Crawl script execution failed');
    }

    // Step 5: Assert API `/opportunities` returns ≥1 row
    console.log('Fetching opportunities...');
    // This might need a delay for the crawler to process and populate opportunities
    await new Promise(resolve => setTimeout(resolve, 10000)); // Adjust delay as needed

    const opportunitiesResponse = await request.get('http://localhost:8000/api/opportunities');
    expect(opportunitiesResponse.ok(), `Failed to GET /opportunities. Status: ${opportunitiesResponse.status()}`).toBeTruthy();
    const opportunities = await opportunitiesResponse.json();
    expect(Array.isArray(opportunities), 'Opportunities response is not an array.').toBeTruthy();
    expect(opportunities.length, 'Opportunities array should have at least one row.').toBeGreaterThanOrEqual(1);
    console.log(`Found ${opportunities.length} opportunities.`);

    // Step 6: Assert JSON keys exist
    // Assuming a structure for an opportunity object. Adjust keys as necessary.
    if (opportunities.length > 0) {
      const firstOpportunity = opportunities[0];
      console.log('First opportunity sample:', JSON.stringify(firstOpportunity, null, 2));
      expect(firstOpportunity).toHaveProperty('id');
      expect(firstOpportunity).toHaveProperty('title');
      expect(firstOpportunity).toHaveProperty('url');
      expect(firstOpportunity).toHaveProperty('source');
      // Add more key assertions as needed
      console.log('JSON keys validated for the first opportunity.');
    }

    // Step 7: Assert `/sites` UI shows Status ✅
    console.log('Checking /sites UI for status...');
    await page.goto('/sites'); // Assuming frontend is on localhost:3000 and this is the correct path
    
    // You'll need to define how to find the specific site and its status.
    // This is a placeholder. You might need a more specific selector.
    // For example, find the row for 'https://playwright.dev' and then check for '✅' in that row.
    const siteRow = page.locator(`tr:has-text("${siteToCrawl}")`);
    await expect(siteRow, `Site row for ${siteToCrawl} not found.`).toBeVisible();

    const statusIndicator = siteRow.locator('td:has-text("✅")'); // Or a specific class/data-testid for status
    await expect(statusIndicator, `Status ✅ not found for site ${siteToCrawl}. Check if the status text/icon is correct.`).toBeVisible({ timeout: 10000 });
    console.log('/sites UI status validated.');
  });
}); 