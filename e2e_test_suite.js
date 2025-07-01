#!/usr/bin/env node
"""Comprehensive E2E test suite for HoistScraper using Puppeteer."""

const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

class E2ETestSuite {
    constructor(baseUrl = 'http://localhost:3000', apiUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.apiUrl = apiUrl;
        this.browser = null;
        this.page = null;
        this.results = {
            passed: 0,
            failed: 0,
            tests: [],
            screenshots: []
        };
    }

    async setup() {
        console.log('🚀 Setting up browser...');
        this.browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        });
        this.page = await this.browser.newPage();
        await this.page.setViewport({ width: 1920, height: 1080 });
        
        // Set up request interception for performance monitoring
        await this.page.setRequestInterception(true);
        this.page.on('request', (request) => {
            request.continue();
        });
        
        // Monitor console errors
        this.page.on('console', msg => {
            if (msg.type() === 'error') {
                console.error('Browser console error:', msg.text());
            }
        });
    }

    async teardown() {
        if (this.browser) {
            await this.browser.close();
        }
    }

    async logTest(name, passed, details = '', screenshot = null) {
        const result = {
            name,
            passed,
            details,
            timestamp: new Date().toISOString(),
            screenshot
        };
        
        this.results.tests.push(result);
        
        if (passed) {
            this.results.passed++;
            console.log(`✅ ${name}`);
        } else {
            this.results.failed++;
            console.log(`❌ ${name}: ${details}`);
        }
        
        if (screenshot) {
            this.results.screenshots.push({
                test: name,
                path: screenshot
            });
        }
    }

    async takeScreenshot(name) {
        const screenshotDir = './test-screenshots';
        await fs.mkdir(screenshotDir, { recursive: true });
        
        const filename = `${name.replace(/\s+/g, '-')}-${Date.now()}.png`;
        const filepath = path.join(screenshotDir, filename);
        
        await this.page.screenshot({ path: filepath, fullPage: true });
        return filepath;
    }

    // Test 1: Homepage Load and Performance
    async testHomepagePerformance() {
        try {
            const startTime = Date.now();
            const response = await this.page.goto(this.baseUrl, {
                waitUntil: 'networkidle0',
                timeout: 30000
            });
            
            const loadTime = Date.now() - startTime;
            
            if (response.status() === 200 && loadTime < 3000) {
                await this.logTest('Homepage Performance', true, 
                    `Loaded in ${loadTime}ms`);
            } else {
                const screenshot = await this.takeScreenshot('homepage-performance');
                await this.logTest('Homepage Performance', false, 
                    `Status: ${response.status()}, Load time: ${loadTime}ms`, screenshot);
            }
            
            // Check for critical elements
            const hasNavigation = await this.page.$('nav') !== null;
            const hasMainContent = await this.page.$('main') !== null;
            
            if (hasNavigation && hasMainContent) {
                await this.logTest('Homepage Structure', true);
            } else {
                await this.logTest('Homepage Structure', false, 
                    'Missing critical elements');
            }
            
        } catch (error) {
            await this.logTest('Homepage Performance', false, error.message);
        }
    }

    // Test 2: Navigation Tests
    async testNavigation() {
        try {
            // Test navigation to Sites page
            await this.page.click('a[href="/sites"]');
            await this.page.waitForURL('**/sites', { timeout: 10000 });
            
            const sitesUrl = this.page.url();
            if (sitesUrl.includes('/sites')) {
                await this.logTest('Navigation to Sites', true);
            } else {
                await this.logTest('Navigation to Sites', false, 
                    `Expected /sites, got ${sitesUrl}`);
            }
            
            // Test navigation to Jobs
            await this.page.click('a[href="/jobs"]');
            await this.page.waitForURL('**/jobs', { timeout: 10000 });
            
            const jobsUrl = this.page.url();
            if (jobsUrl.includes('/jobs')) {
                await this.logTest('Navigation to Jobs', true);
            } else {
                await this.logTest('Navigation to Jobs', false, 
                    `Expected /jobs, got ${jobsUrl}`);
            }
            
        } catch (error) {
            await this.logTest('Navigation', false, error.message);
        }
    }

    // Test 3: API Integration
    async testAPIIntegration() {
        try {
            // Navigate to sites page
            await this.page.goto(`${this.baseUrl}/sites`, {
                waitUntil: 'networkidle0'
            });
            
            // Wait for data to load
            await this.page.waitForTimeout(2000);
            
            // Check if data is displayed
            const hasData = await this.page.evaluate(() => {
                const tables = document.querySelectorAll('table');
                const lists = document.querySelectorAll('ul');
                return tables.length > 0 || lists.length > 0;
            });
            
            if (hasData) {
                await this.logTest('API Data Display', true);
            } else {
                const screenshot = await this.takeScreenshot('api-integration');
                await this.logTest('API Data Display', false, 
                    'No data displayed on page', screenshot);
            }
            
        } catch (error) {
            await this.logTest('API Integration', false, error.message);
        }
    }

    // Test 4: Form Interactions
    async testFormInteractions() {
        try {
            // Navigate to sites page
            await this.page.goto(`${this.baseUrl}/sites`, {
                waitUntil: 'networkidle0'
            });
            
            // Look for add/create button
            const addButton = await this.page.$('button:has-text("Add"), button:has-text("Create")');
            
            if (addButton) {
                await addButton.click();
                await this.page.waitForTimeout(1000);
                
                // Check if form modal/dialog appears
                const hasForm = await this.page.$('form') !== null;
                
                if (hasForm) {
                    await this.logTest('Form Display', true);
                } else {
                    await this.logTest('Form Display', false, 'Form not found');
                }
            } else {
                await this.logTest('Form Interactions', false, 'Add button not found');
            }
            
        } catch (error) {
            await this.logTest('Form Interactions', false, error.message);
        }
    }

    // Test 5: Responsive Design
    async testResponsiveDesign() {
        const viewports = [
            { name: 'Mobile', width: 375, height: 667 },
            { name: 'Tablet', width: 768, height: 1024 },
            { name: 'Desktop', width: 1920, height: 1080 }
        ];
        
        for (const viewport of viewports) {
            try {
                await this.page.setViewport({
                    width: viewport.width,
                    height: viewport.height
                });
                
                await this.page.goto(this.baseUrl, {
                    waitUntil: 'networkidle0'
                });
                
                // Check if page renders without horizontal scroll
                const hasHorizontalScroll = await this.page.evaluate(() => {
                    return document.documentElement.scrollWidth > window.innerWidth;
                });
                
                if (!hasHorizontalScroll) {
                    await this.logTest(`Responsive Design - ${viewport.name}`, true);
                } else {
                    const screenshot = await this.takeScreenshot(`responsive-${viewport.name}`);
                    await this.logTest(`Responsive Design - ${viewport.name}`, false,
                        'Horizontal scroll detected', screenshot);
                }
                
            } catch (error) {
                await this.logTest(`Responsive Design - ${viewport.name}`, false, 
                    error.message);
            }
        }
    }

    // Test 6: Performance Metrics
    async testPerformanceMetrics() {
        try {
            await this.page.goto(this.baseUrl);
            
            // Get performance metrics
            const metrics = await this.page.metrics();
            const performanceTiming = await this.page.evaluate(() => {
                const timing = performance.timing;
                return {
                    domContentLoaded: timing.domContentLoadedEventEnd - timing.domContentLoadedEventStart,
                    loadComplete: timing.loadEventEnd - timing.loadEventStart,
                    firstPaint: performance.getEntriesByType('paint')[0]?.startTime || 0
                };
            });
            
            // Check performance thresholds
            const passed = performanceTiming.firstPaint < 1000 && 
                          performanceTiming.domContentLoaded < 2000;
            
            await this.logTest('Performance Metrics', passed, 
                `First Paint: ${performanceTiming.firstPaint}ms, ` +
                `DOM Content Loaded: ${performanceTiming.domContentLoaded}ms`);
            
        } catch (error) {
            await this.logTest('Performance Metrics', false, error.message);
        }
    }

    // Test 7: Accessibility
    async testAccessibility() {
        try {
            await this.page.goto(this.baseUrl);
            
            // Basic accessibility checks
            const accessibilityChecks = await this.page.evaluate(() => {
                const checks = {
                    hasLangAttribute: document.documentElement.lang !== '',
                    hasAltTexts: Array.from(document.images).every(img => img.alt !== ''),
                    hasLabels: Array.from(document.querySelectorAll('input:not([type="hidden"])')).every(input => {
                        return input.labels.length > 0 || input.getAttribute('aria-label');
                    }),
                    hasHeadings: document.querySelector('h1') !== null
                };
                
                return checks;
            });
            
            const allPassed = Object.values(accessibilityChecks).every(check => check);
            
            await this.logTest('Accessibility Basics', allPassed,
                JSON.stringify(accessibilityChecks));
            
        } catch (error) {
            await this.logTest('Accessibility', false, error.message);
        }
    }

    // Run all tests
    async runAllTests() {
        console.log('=' * 50);
        console.log('HOISTSCRAPER E2E TEST SUITE');
        console.log(`Frontend: ${this.baseUrl}`);
        console.log(`API: ${this.apiUrl}`);
        console.log(`Time: ${new Date().toISOString()}`);
        console.log('=' * 50);
        
        await this.setup();
        
        // Run tests in sequence
        await this.testHomepagePerformance();
        await this.testNavigation();
        await this.testAPIIntegration();
        await this.testFormInteractions();
        await this.testResponsiveDesign();
        await this.testPerformanceMetrics();
        await this.testAccessibility();
        
        await this.teardown();
        
        // Generate report
        await this.generateReport();
    }

    async generateReport() {
        console.log('\n' + '=' * 50);
        console.log('TEST RESULTS SUMMARY');
        console.log('=' * 50);
        
        const total = this.results.passed + this.results.failed;
        const passRate = total > 0 ? (this.results.passed / total * 100) : 0;
        
        console.log(`\nTotal Tests: ${total}`);
        console.log(`Passed: ${this.results.passed} ✅`);
        console.log(`Failed: ${this.results.failed} ❌`);
        console.log(`Pass Rate: ${passRate.toFixed(1)}%`);
        
        if (this.results.failed > 0) {
            console.log('\nFailed Tests:');
            this.results.tests
                .filter(test => !test.passed)
                .forEach(test => {
                    console.log(`  - ${test.name}: ${test.details}`);
                });
        }
        
        // Save detailed report
        await fs.writeFile('e2e_test_report.json', 
            JSON.stringify(this.results, null, 2));
        
        console.log('\n📄 Detailed report saved to e2e_test_report.json');
        
        if (this.results.screenshots.length > 0) {
            console.log(`📸 ${this.results.screenshots.length} screenshots saved to ./test-screenshots/`);
        }
        
        return passRate >= 95;
    }
}

// Main execution
async function main() {
    const suite = new E2ETestSuite();
    
    try {
        const passed = await suite.runAllTests();
        process.exit(passed ? 0 : 1);
    } catch (error) {
        console.error('Test suite error:', error);
        process.exit(1);
    }
}

// Run if executed directly
if (require.main === module) {
    main();
}

module.exports = E2ETestSuite;