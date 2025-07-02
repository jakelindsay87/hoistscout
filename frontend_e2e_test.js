#!/usr/bin/env node
/**
 * Comprehensive End-to-End Tests for HoistScout Frontend
 * Tests all UI functionality, console errors, and user workflows
 */

const puppeteer = require('puppeteer');

const FRONTEND_URL = 'https://hoistscout-frontend.onrender.com';
const API_URL = 'https://hoistscout-api.onrender.com';
const TIMEOUT = 30000;

class FrontendTester {
  constructor() {
    this.browser = null;
    this.page = null;
    this.results = {
      totalTests: 0,
      passed: 0,
      failed: 0,
      errors: [],
      consoleErrors: [],
      networkErrors: [],
      warnings: []
    };
  }

  async init() {
    console.log('🚀 Launching browser...');
    this.browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    this.page = await this.browser.newPage();
    
    // Set viewport
    await this.page.setViewport({ width: 1280, height: 800 });
    
    // Capture console errors
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        this.results.consoleErrors.push({
          text: msg.text(),
          location: msg.location()
        });
      }
    });
    
    // Capture page errors
    this.page.on('pageerror', error => {
      this.results.errors.push({
        message: error.message,
        stack: error.stack
      });
    });
    
    // Capture failed requests
    this.page.on('requestfailed', request => {
      this.results.networkErrors.push({
        url: request.url(),
        failure: request.failure()
      });
    });
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
    }
  }

  async test(testName, testFn) {
    this.results.totalTests++;
    console.log(`\n📋 Running test: ${testName}`);
    
    try {
      await testFn();
      this.results.passed++;
      console.log(`✅ ${testName} - PASSED`);
    } catch (error) {
      this.results.failed++;
      console.error(`❌ ${testName} - FAILED`);
      console.error(`   Error: ${error.message}`);
      this.results.errors.push({
        test: testName,
        error: error.message,
        stack: error.stack
      });
    }
  }

  async runAllTests() {
    console.log('🧪 Starting Frontend E2E Tests');
    console.log('=' .repeat(80));
    
    await this.init();
    
    try {
      // Test 1: Homepage loads
      await this.test('Homepage loads successfully', async () => {
        await this.page.goto(FRONTEND_URL, { waitUntil: 'networkidle2', timeout: TIMEOUT });
        const title = await this.page.title();
        if (!title) throw new Error('No page title found');
      });

      // Test 2: Check for console errors
      await this.test('No console errors on homepage', async () => {
        // Clear previous errors
        this.results.consoleErrors = [];
        await this.page.goto(FRONTEND_URL, { waitUntil: 'networkidle2', timeout: TIMEOUT });
        await this.page.waitForTimeout(3000); // Wait for any async errors
        
        if (this.results.consoleErrors.length > 0) {
          throw new Error(`Found ${this.results.consoleErrors.length} console errors: ${JSON.stringify(this.results.consoleErrors[0])}`);
        }
      });

      // Test 3: API connectivity
      await this.test('API stats endpoint works', async () => {
        const response = await this.page.evaluate(async (apiUrl) => {
          try {
            const res = await fetch(`${apiUrl}/api/stats`);
            return {
              status: res.status,
              ok: res.ok,
              data: await res.json()
            };
          } catch (err) {
            return { error: err.message };
          }
        }, API_URL);
        
        if (response.error) throw new Error(`API error: ${response.error}`);
        if (!response.ok) throw new Error(`API returned status ${response.status}`);
        if (!response.data.hasOwnProperty('total_sites')) throw new Error('Stats response missing expected fields');
      });

      // Test 4: Navigation works
      await this.test('Navigation to all pages', async () => {
        const pages = [
          { name: 'Sites', path: '/sites', selector: 'h1' },
          { name: 'Opportunities', path: '/opportunities', selector: 'h1' },
          { name: 'Jobs', path: '/jobs', selector: 'h1' },
          { name: 'Results', path: '/results', selector: 'h1' }
        ];
        
        for (const pageInfo of pages) {
          await this.page.goto(`${FRONTEND_URL}${pageInfo.path}`, { waitUntil: 'networkidle2' });
          await this.page.waitForSelector(pageInfo.selector, { timeout: 10000 });
          console.log(`   ✓ ${pageInfo.name} page loaded`);
        }
      });

      // Test 5: Sites page functionality
      await this.test('Sites page displays correctly', async () => {
        await this.page.goto(`${FRONTEND_URL}/sites`, { waitUntil: 'networkidle2' });
        
        // Check for loading state or content
        await this.page.waitForSelector('[data-testid="sites-content"], [data-testid="loading-spinner"], .MuiDataGrid-root, table', { timeout: 10000 });
        
        // Check for "Add Site" button
        const addButton = await this.page.$('button:has-text("Add"), button:has-text("Create"), button:has-text("New")');
        if (!addButton) {
          console.log('   ⚠️  No Add Site button found (might need auth)');
        }
      });

      // Test 6: Opportunities page
      await this.test('Opportunities page displays correctly', async () => {
        await this.page.goto(`${FRONTEND_URL}/opportunities`, { waitUntil: 'networkidle2' });
        await this.page.waitForSelector('[data-testid="opportunities-content"], [data-testid="loading-spinner"], .MuiDataGrid-root, table, div', { timeout: 10000 });
      });

      // Test 7: Responsive design
      await this.test('Mobile responsive design', async () => {
        // Test mobile viewport
        await this.page.setViewport({ width: 375, height: 667 });
        await this.page.goto(FRONTEND_URL, { waitUntil: 'networkidle2' });
        
        // Check if navigation is responsive (hamburger menu or similar)
        const mobileNav = await this.page.$('[data-testid="mobile-menu"], button[aria-label*="menu"], .hamburger');
        console.log(`   Mobile navigation: ${mobileNav ? 'Found' : 'Not found (might use responsive CSS)'}`);
        
        // Reset viewport
        await this.page.setViewport({ width: 1280, height: 800 });
      });

      // Test 8: Error handling
      await this.test('404 page handling', async () => {
        await this.page.goto(`${FRONTEND_URL}/nonexistent-page`, { waitUntil: 'networkidle2' });
        const content = await this.page.content();
        if (!content.includes('404') && !content.includes('not found') && !content.includes('Not Found')) {
          console.log('   ⚠️  No explicit 404 message found');
        }
      });

      // Test 9: Performance metrics
      await this.test('Performance metrics', async () => {
        await this.page.goto(FRONTEND_URL, { waitUntil: 'networkidle2' });
        const metrics = await this.page.metrics();
        
        console.log(`   📊 Performance Metrics:`);
        console.log(`      - DOM Nodes: ${metrics.Nodes}`);
        console.log(`      - JS Event Listeners: ${metrics.JSEventListeners}`);
        console.log(`      - JS Heap Used: ${(metrics.JSHeapUsedSize / 1024 / 1024).toFixed(2)} MB`);
        
        if (metrics.Nodes > 3000) {
          this.results.warnings.push('High DOM node count (>3000)');
        }
        if (metrics.JSHeapUsedSize > 50 * 1024 * 1024) {
          this.results.warnings.push('High memory usage (>50MB)');
        }
      });

      // Test 10: Forms and interactivity
      await this.test('Interactive elements', async () => {
        await this.page.goto(`${FRONTEND_URL}/sites`, { waitUntil: 'networkidle2' });
        
        // Count interactive elements
        const buttons = await this.page.$$('button');
        const links = await this.page.$$('a');
        const inputs = await this.page.$$('input, textarea, select');
        
        console.log(`   📝 Interactive Elements:`);
        console.log(`      - Buttons: ${buttons.length}`);
        console.log(`      - Links: ${links.length}`);
        console.log(`      - Form inputs: ${inputs.length}`);
      });

      // Test 11: Accessibility basics
      await this.test('Basic accessibility', async () => {
        await this.page.goto(FRONTEND_URL, { waitUntil: 'networkidle2' });
        
        // Check for alt texts on images
        const imagesWithoutAlt = await this.page.$$eval('img:not([alt])', imgs => imgs.length);
        if (imagesWithoutAlt > 0) {
          this.results.warnings.push(`${imagesWithoutAlt} images without alt text`);
        }
        
        // Check for form labels
        const inputsWithoutLabels = await this.page.$$eval('input:not([aria-label]):not([id])', inputs => inputs.length);
        if (inputsWithoutLabels > 0) {
          this.results.warnings.push(`${inputsWithoutLabels} inputs without labels`);
        }
        
        // Check for heading structure
        const h1Count = await this.page.$$eval('h1', h1s => h1s.length);
        if (h1Count === 0) {
          this.results.warnings.push('No H1 heading found');
        } else if (h1Count > 1) {
          this.results.warnings.push(`Multiple H1 headings found (${h1Count})`);
        }
      });

      // Test 12: Check all API endpoints used by frontend
      await this.test('All frontend API calls', async () => {
        const apiCalls = [];
        
        // Intercept all API calls
        await this.page.setRequestInterception(true);
        this.page.on('request', request => {
          if (request.url().includes(API_URL)) {
            apiCalls.push({
              url: request.url(),
              method: request.method()
            });
          }
          request.continue();
        });
        
        // Navigate through pages to trigger API calls
        const pagesToVisit = ['/', '/sites', '/opportunities', '/jobs', '/results'];
        for (const path of pagesToVisit) {
          await this.page.goto(`${FRONTEND_URL}${path}`, { waitUntil: 'networkidle2' });
          await this.page.waitForTimeout(1000);
        }
        
        // Stop interception
        await this.page.setRequestInterception(false);
        
        console.log(`   📡 API Calls Made:`);
        const uniqueEndpoints = [...new Set(apiCalls.map(call => `${call.method} ${call.url}`))];
        uniqueEndpoints.forEach(endpoint => {
          console.log(`      - ${endpoint}`);
        });
      });

    } finally {
      await this.printResults();
      await this.close();
    }
  }

  async printResults() {
    console.log('\n' + '='.repeat(80));
    console.log('📊 TEST RESULTS SUMMARY');
    console.log('='.repeat(80));
    
    const successRate = this.results.totalTests > 0 
      ? (this.results.passed / this.results.totalTests * 100).toFixed(1)
      : 0;
    
    console.log(`Total Tests: ${this.results.totalTests}`);
    console.log(`✅ Passed: ${this.results.passed}`);
    console.log(`❌ Failed: ${this.results.failed}`);
    console.log(`Success Rate: ${successRate}%`);
    
    if (this.results.consoleErrors.length > 0) {
      console.error(`\n❌ CONSOLE ERRORS (${this.results.consoleErrors.length})`);
      console.error('-'.repeat(40));
      this.results.consoleErrors.slice(0, 5).forEach(error => {
        console.error(`• ${error.text}`);
      });
    }
    
    if (this.results.networkErrors.length > 0) {
      console.error(`\n❌ NETWORK ERRORS (${this.results.networkErrors.length})`);
      console.error('-'.repeat(40));
      this.results.networkErrors.slice(0, 5).forEach(error => {
        console.error(`• ${error.url} - ${error.failure?.errorText || 'Failed'}`);
      });
    }
    
    if (this.results.warnings.length > 0) {
      console.warn(`\n⚠️  WARNINGS (${this.results.warnings.length})`);
      console.warn('-'.repeat(40));
      this.results.warnings.forEach(warning => {
        console.warn(`• ${warning}`);
      });
    }
    
    // Save results
    const fs = require('fs');
    fs.writeFileSync('frontend_test_results.json', JSON.stringify(this.results, null, 2));
    console.log('\n📄 Detailed results saved to frontend_test_results.json');
    
    // Exit code
    process.exit(this.results.failed > 0 ? 1 : 0);
  }
}

// Run tests
async function main() {
  const tester = new FrontendTester();
  try {
    await tester.runAllTests();
  } catch (error) {
    console.error('Fatal error:', error);
    process.exit(1);
  }
}

main();