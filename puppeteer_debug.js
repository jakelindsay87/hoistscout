const puppeteer = require('puppeteer');

async function debugHoistScoutAuth() {
    console.log('=== HoistScout Frontend Debug with Puppeteer ===\n');
    
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    try {
        const page = await browser.newPage();
        
        // Enable console log collection
        const consoleLogs = [];
        const networkErrors = [];
        const pageErrors = [];
        
        page.on('console', msg => {
            consoleLogs.push({
                type: msg.type(),
                text: msg.text(),
                location: msg.location()
            });
        });
        
        page.on('pageerror', error => {
            pageErrors.push(error.toString());
        });
        
        // Monitor network requests
        await page.setRequestInterception(true);
        const requests = [];
        const responses = [];
        
        page.on('request', request => {
            requests.push({
                url: request.url(),
                method: request.method(),
                headers: request.headers(),
                postData: request.postData()
            });
            request.continue();
        });
        
        page.on('response', response => {
            responses.push({
                url: response.url(),
                status: response.status(),
                headers: response.headers()
            });
        });
        
        console.log('1. Loading frontend...');
        await page.goto('https://hoistscout-frontend.onrender.com', {
            waitUntil: 'networkidle2',
            timeout: 30000
        });
        
        console.log('2. Taking screenshot of homepage...');
        await page.screenshot({ path: 'homepage.png' });
        
        // Check localStorage
        console.log('\n3. Checking localStorage:');
        const localStorageData = await page.evaluate(() => {
            const data = {};
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                data[key] = localStorage.getItem(key);
            }
            return data;
        });
        console.log('LocalStorage:', localStorageData);
        
        // Navigate to login
        console.log('\n4. Navigating to login page...');
        await page.goto('https://hoistscout-frontend.onrender.com/login', {
            waitUntil: 'networkidle2'
        });
        
        await page.screenshot({ path: 'login-page.png' });
        
        // Try to find login form
        console.log('\n5. Looking for login form elements...');
        const formElements = await page.evaluate(() => {
            const emailInput = document.querySelector('input[type="email"], input[name="email"], input[placeholder*="email" i]');
            const passwordInput = document.querySelector('input[type="password"], input[name="password"]');
            const submitButton = document.querySelector('button[type="submit"]') || 
                                 Array.from(document.querySelectorAll('button')).find(btn => 
                                     btn.textContent.toLowerCase().includes('login') || 
                                     btn.textContent.toLowerCase().includes('sign in'));
            
            return {
                hasEmailInput: !!emailInput,
                hasPasswordInput: !!passwordInput,
                hasSubmitButton: !!submitButton,
                emailSelector: emailInput ? emailInput.tagName + (emailInput.id ? '#' + emailInput.id : '') : null,
                passwordSelector: passwordInput ? passwordInput.tagName + (passwordInput.id ? '#' + passwordInput.id : '') : null
            };
        });
        console.log('Form elements found:', formElements);
        
        // Attempt login
        console.log('\n6. Attempting login with demo credentials...');
        
        // Type email
        await page.type('input[type="email"], input[name="email"]', 'demo@hoistscout.com');
        await page.type('input[type="password"]', 'demo123');
        
        // Clear network logs before login
        requests.length = 0;
        responses.length = 0;
        
        // Click login button
        await Promise.all([
            page.click('button[type="submit"]'),
            page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 10000 }).catch(() => {})
        ]);
        
        // Wait a bit for any async operations
        await page.waitForTimeout(2000);
        
        console.log('\n7. Login attempt results:');
        
        // Check current URL
        console.log('Current URL:', page.url());
        
        // Take screenshot after login attempt
        await page.screenshot({ path: 'after-login.png' });
        
        // Check localStorage again
        const postLoginStorage = await page.evaluate(() => {
            const data = {};
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                data[key] = localStorage.getItem(key);
            }
            return data;
        });
        console.log('Post-login localStorage:', postLoginStorage);
        
        // Analyze network requests
        console.log('\n8. Network Analysis:');
        
        const authRequests = requests.filter(r => r.url.includes('/auth'));
        console.log(`Found ${authRequests.length} auth-related requests:`);
        authRequests.forEach(req => {
            console.log(`  ${req.method} ${req.url}`);
            if (req.postData) {
                console.log(`    Body: ${req.postData}`);
            }
        });
        
        const authResponses = responses.filter(r => r.url.includes('/auth'));
        console.log(`\nAuth responses:`);
        authResponses.forEach(resp => {
            console.log(`  ${resp.url}: ${resp.status}`);
        });
        
        // Console logs
        console.log('\n9. Console logs:');
        const errorLogs = consoleLogs.filter(log => log.type === 'error');
        errorLogs.forEach(log => {
            console.log(`  ERROR: ${log.text}`);
        });
        
        // Page errors
        if (pageErrors.length > 0) {
            console.log('\n10. Page errors:');
            pageErrors.forEach(error => {
                console.log(`  ${error}`);
            });
        }
        
        // Final analysis
        console.log('\n=== ANALYSIS ===');
        console.log('Issues found:');
        
        const issues = [];
        
        // Check for 401 errors
        const unauthorizedResponses = responses.filter(r => r.status === 401);
        if (unauthorizedResponses.length > 0) {
            issues.push(`${unauthorizedResponses.length} unauthorized (401) responses`);
            unauthorizedResponses.forEach(r => {
                console.log(`  - ${r.url}`);
            });
        }
        
        // Check for missing tokens
        if (!postLoginStorage.access_token && !postLoginStorage.token) {
            issues.push('No access token found in localStorage after login');
        }
        
        // Check for CORS errors
        const corsErrors = errorLogs.filter(log => log.text.includes('CORS') || log.text.includes('Cross-Origin'));
        if (corsErrors.length > 0) {
            issues.push(`${corsErrors.length} CORS-related errors`);
        }
        
        if (issues.length === 0) {
            console.log('No obvious issues found - auth might be working correctly');
        } else {
            issues.forEach(issue => console.log(`- ${issue}`));
        }
        
    } catch (error) {
        console.error('Error during debugging:', error);
    } finally {
        await browser.close();
    }
}

debugHoistScoutAuth().catch(console.error);