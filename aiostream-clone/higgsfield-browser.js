const { chromium } = require('playwright');

(async () => {
    console.log('Launching browser...');
    const browser = await chromium.launch({ 
        headless: true,
        args: ['--no-sandbox', '--disable-dev-shm-usage']
    });
    
    console.log('Creating page...');
    const page = await browser.newPage();
    
    console.log('Going to Higgsfield...');
    await page.goto('https://higgsfield.ai', { timeout: 60000 });
    
    console.log('URL:', page.url());
    console.log('Title:', await page.title());
    
    // Check if logged in
    if (page.url().includes('login')) {
        console.log('NOT LOGGED IN - Please log in manually');
        // Wait for user to log in
        await page.waitForTimeout(60000); // 1 minute
    }
    
    console.log('Final URL:', page.url());
    console.log('Final Title:', await page.title());
    
    await browser.close();
    console.log('Done!');
})();
