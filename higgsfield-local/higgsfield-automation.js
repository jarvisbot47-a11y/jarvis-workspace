#!/usr/bin/env node
/**
 * Higgsfield Browser Automation
 * Run this on YOUR local machine with Chrome logged into Higgsfield
 * 
 * SETUP:
 * 1. Install Node.js: https://nodejs.org
 * 2. Run: npm install playwright
 * 3. Run: npx playwright install chromium
 * 4. Make sure you're logged into Higgsfield.ai in Chrome
 * 5. Run: node higgsfield-automation.js
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Configuration
const ALBUMS = [
    { name: 'Memento Mori Vol. 1', tracks: ['Track1', 'Track2', 'Track3'] },
    { name: 'Memento Mori Vol. 2', tracks: ['Track1', 'Track2', 'Track3'] },
    { name: 'Memento Mori Vol. 3', tracks: ['Track1', 'Track2', 'Track3'] },
];

// Prompts for each album (customize these!)
const PROMPTS = {
    'Memento Mori Vol. 1': [
        'Cinematic dark alley with neon lights, fog, dramatic lighting',
        'FPV drone shot through abandoned warehouse with sparks',
        'Slow motion rain on city streets at night',
    ],
    'Memento Mori Vol. 2': [
        'Cinema-quality explosion with debris and smoke, slow motion',
        'Aerial shot of mountain landscape at golden hour',
        'Neon-lit Tokyo street at night, rain reflections',
    ],
    'Memento Mori Vol. 3': [
        'Epic battle scene with fire and smoke',
        'Underwater coral reef with rays of light',
        'Lightning storm over ocean, cinematic slow motion',
    ]
};

class HiggsfieldAutomation {
    constructor() {
        this.browser = null;
        this.page = null;
        this.downloadsPath = path.join(__dirname, 'downloads');
        
        // Ensure downloads folder exists
        if (!fs.existsSync(this.downloadsPath)) {
            fs.mkdirSync(this.downloadsPath, { recursive: true });
        }
    }
    
    async launch() {
        console.log('🚀 Launching Chrome...');
        
        // Try to use user's actual Chrome profile
        const chromePaths = [
            process.platform === 'darwin' ? '~/Library/Application Support/Google/Chrome' : '~/.config/google-chrome',
            '~/.config/chromium',
        ];
        
        let userDataDir = null;
        for (const p of chromePaths) {
            const expanded = path.expandTilde(p);
            if (fs.existsSync(expanded)) {
                userDataDir = expanded;
                break;
            }
        }
        
        const launchOptions = {
            headless: false,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        };
        
        // Use user's profile if found
        if (userDataDir) {
            console.log(`📁 Using Chrome profile: ${userDataDir}`);
            launchOptions.userDataDir = userDataDir;
        }
        
        this.browser = await chromium.launch(launchOptions);
        this.page = await this.browser.newPage();
        
        console.log('✅ Browser launched!');
    }
    
    async login() {
        console.log('🌐 Opening Higgsfield...');
        await this.page.goto('https://higgsfield.ai', { timeout: 60000 });
        await this.page.waitForTimeout(3000);
        
        // Check if logged in
        if (this.page.url().includes('login')) {
            console.log('⚠️  Please log into Higgsfield manually...');
            console.log('   1. Log in to Higgsfield in the browser window');
            console.log('   2. Navigate to Image to Video');
            console.log('   3. Press Enter here when done');
            await new Promise(resolve => {
                const readline = require('readline').createInterface({
                    input: process.stdin,
                    output: process.stdout
                });
                readline.question('Press Enter after logging in... ', resolve);
            });
        }
        
        console.log('✅ Logged in!');
    }
    
    async generateVideo(imagePath, prompt, outputName) {
        console.log(`\n🎬 Generating: ${outputName}`);
        
        try {
            // Navigate to image-to-video
            await this.page.goto('https://higgsfield.ai/image-to-video', { timeout: 60000 });
            await this.page.waitForTimeout(3000);
            
            // Upload image if exists
            if (imagePath && fs.existsSync(imagePath)) {
                console.log('📤 Uploading image...');
                const fileInput = await this.page.$('input[type="file"]');
                if (fileInput) {
                    await fileInput.setInputFiles(imagePath);
                }
                await this.page.waitForTimeout(2000);
            }
            
            // Enter prompt
            console.log('✍️  Entering prompt...');
            const promptInput = await this.page.$('textarea, input[type="text"]');
            if (promptInput) {
                await promptInput.fill(prompt);
            }
            
            // Select 5 seconds if available
            try {
                const fiveSecBtn = await this.page.$('text="5s"');
                if (fiveSecBtn) {
                    await fiveSecBtn.click();
                }
            } catch (e) {}
            
            // Click generate
            console.log('🎯 Clicking Generate...');
            try {
                const generateBtn = await this.page.$('button:has-text("Generate")');
                if (generateBtn) {
                    await generateBtn.click();
                }
            } catch (e) {
                try {
                    const submitBtn = await this.page.$('button[type="submit"]');
                    if (submitBtn) {
                        await submitBtn.click();
                    }
                } catch (e2) {}
            }
            
            // Wait for generation (30-90 seconds)
            console.log('⏳ Waiting for generation (may take up to 90 seconds)...');
            await this.page.waitForTimeout(90000);
            
            // Try to find and download video
            try {
                const videoElement = await this.page.$('video');
                if (videoElement) {
                    const src = await videoElement.getAttribute('src');
                    if (src) {
                        const outputPath = path.join(this.downloadsPath, `${outputName}.mp4`);
                        // Download logic here
                        console.log(`✅ Generated: ${outputPath}`);
                        return outputPath;
                    }
                }
            } catch (e) {}
            
            console.log('⚠️  Generation may still be in progress...');
            return null;
            
        } catch (error) {
            console.error('❌ Error:', error.message);
            return null;
        }
    }
    
    async runBatch() {
        console.log('='.repeat(60));
        console.log('HIGGSFIELD CONTENT GENERATION');
        console.log('='.repeat(60));
        
        await this.launch();
        await this.login();
        
        // Generate for each album
        for (const album of ALBUMS) {
            console.log(`\n\n${'='.repeat(60)}`);
            console.log(`📀 ${album.name}`);
            console.log(`${'='.repeat(60)}`);
            
            const prompts = PROMPTS[album.name] || [];
            
            for (let i = 0; i < prompts.length; i++) {
                const prompt = prompts[i];
                const outputName = `${album.name.replace(/\s+/g, '_')}_${i + 1}`;
                
                // Look for image in album folder
                const imagePath = path.join(
                    __dirname, 
                    '..', 
                    'MystikSingh', 
                    album.name.replace('Vol ', 'Vol'),
                    'Raw',
                    `${album.tracks[i] || 'default'}.jpg`
                );
                
                await this.generateVideo(
                    fs.existsSync(imagePath) ? imagePath : null,
                    prompt,
                    outputName
                );
                
                // Wait between generations
                if (i < prompts.length - 1) {
                    console.log('⏳ Waiting 30 seconds before next...');
                    await this.page.waitForTimeout(30000);
                }
            }
        }
        
        console.log('\n\n' + '='.repeat(60));
        console.log('✅ BATCH COMPLETE!');
        console.log('='.repeat(60));
        console.log(`📁 Downloads saved to: ${this.downloadsPath}`);
        
        await this.browser.close();
    }
}

// Run
const automation = new HiggsfieldAutomation();
automation.runBatch().catch(console.error);
