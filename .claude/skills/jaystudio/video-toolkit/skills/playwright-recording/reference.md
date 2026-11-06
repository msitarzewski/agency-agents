# Playwright Recording Reference

## API Reference

### Browser Context Video Options

```typescript
interface RecordVideoOptions {
  dir: string;                    // Output directory (required)
  size?: { width: number; height: number }; // Video dimensions
}

const context = await browser.newContext({
  viewport: { width: number; height: number };
  recordVideo: RecordVideoOptions;
  // Other useful options:
  colorScheme?: 'light' | 'dark' | 'no-preference';
  locale?: string;  // e.g., 'en-US'
  timezoneId?: string;  // e.g., 'America/New_York'
  geolocation?: { latitude: number; longitude: number };
  permissions?: string[];  // e.g., ['geolocation']
  userAgent?: string;
});
```

### Browser Launch Options

```typescript
const browser = await chromium.launch({
  slowMo?: number;           // Slow down actions by ms
  headless?: boolean;        // Default true, set false to see browser
  devtools?: boolean;        // Open devtools
  args?: string[];           // Chromium flags
});

// Useful args:
args: [
  '--start-maximized',
  '--disable-infobars',
  '--hide-scrollbars',
]
```

### Page Methods for Recording

```typescript
// Navigation
await page.goto(url, { waitUntil?: 'load' | 'domcontentloaded' | 'networkidle' });
await page.goBack();
await page.goForward();
await page.reload();

// Waiting
await page.waitForTimeout(ms);
await page.waitForLoadState('networkidle');
await page.waitForSelector(selector);
await page.waitForURL(urlPattern);

// Interactions
await page.click(selector);
await page.dblclick(selector);
await page.fill(selector, value);
await page.type(selector, text);  // Types character by character
await page.press(selector, key);  // e.g., 'Enter', 'Tab'
await page.hover(selector);
await page.selectOption(selector, value);
await page.check(selector);       // Checkbox
await page.uncheck(selector);

// Scrolling
await page.evaluate(() => window.scrollTo(0, 500));
await page.evaluate(() => window.scrollBy(0, 200));
await page.locator(selector).scrollIntoViewIfNeeded();

// Screenshots (for thumbnails)
await page.screenshot({ path: 'screenshot.png' });
await page.screenshot({ path: 'full.png', fullPage: true });
```

### Getting Video After Recording

```typescript
const page = await context.newPage();
// ... do stuff ...
await context.close();

// Get video path
const video = page.video();
const path = await video?.path();

// Or save to specific location
await video?.saveAs('output.webm');

// Delete video
await video?.delete();
```

## Common Selectors

```typescript
// CSS Selectors
await page.click('button');
await page.click('#submit-btn');
await page.click('.primary-button');
await page.click('[data-testid="login"]');
await page.click('button:has-text("Submit")');

// Text selectors
await page.click('text=Click me');
await page.click('text="Exact match"');

// XPath
await page.click('xpath=//button[@type="submit"]');

// Combining
await page.click('form >> button.submit');
await page.click('div.modal >> text=Confirm');
```

## Timing Utilities

```typescript
// Reusable delay function
const delay = (ms: number) => new Promise(r => setTimeout(r, ms));

// Smooth typing with delays
async function typeSlowly(page, selector, text, delayMs = 100) {
  await page.click(selector);
  for (const char of text) {
    await page.keyboard.type(char);
    await delay(delayMs);
  }
}

// Wait for animation to complete
async function waitForAnimation(page, selector) {
  await page.waitForFunction(
    (sel) => {
      const el = document.querySelector(sel);
      if (!el) return false;
      const style = getComputedStyle(el);
      return style.animationName === 'none' || style.animationPlayState === 'paused';
    },
    selector
  );
}
```

## Device Emulation

```typescript
import { devices } from 'playwright';

// iPhone
const context = await browser.newContext({
  ...devices['iPhone 14'],
  recordVideo: { dir: './recordings' }
});

// iPad
const context = await browser.newContext({
  ...devices['iPad Pro 11'],
  recordVideo: { dir: './recordings' }
});

// Available devices (partial list):
// 'Desktop Chrome', 'Desktop Firefox', 'Desktop Safari'
// 'iPhone 14', 'iPhone 14 Pro Max', 'iPhone SE'
// 'iPad Pro 11', 'iPad Mini'
// 'Pixel 7', 'Galaxy S23'
```

## Handling Common Scenarios

### Cookie Consent Banner

```typescript
// Option 1: Click accept
try {
  await page.click('button:has-text("Accept")', { timeout: 3000 });
} catch {
  // Banner not present
}

// Option 2: Hide with CSS
await page.addStyleTag({
  content: `
    [class*="cookie"], [id*="cookie"],
    [class*="consent"], [id*="consent"],
    [class*="gdpr"], [id*="gdpr"] {
      display: none !important;
    }
  `
});
```

### Login Before Recording

```typescript
// Save auth state
const context = await browser.newContext();
const page = await context.newPage();
await page.goto('https://app.com/login');
await page.fill('#email', 'user@example.com');
await page.fill('#password', 'password');
await page.click('button[type="submit"]');
await page.waitForURL('**/dashboard');

// Save storage state
await context.storageState({ path: 'auth.json' });
await context.close();

// Use saved auth for recording
const recordingContext = await browser.newContext({
  storageState: 'auth.json',
  recordVideo: { dir: './recordings', size: { width: 1920, height: 1080 } }
});
```

### Handling Popups/Modals

```typescript
// Wait for modal and interact
await page.click('button.open-modal');
await page.waitForSelector('.modal.visible');
await page.fill('.modal input', 'value');
await page.click('.modal button.submit');
await page.waitForSelector('.modal', { state: 'hidden' });
```

### File Upload

```typescript
// Single file
await page.setInputFiles('input[type="file"]', 'path/to/file.pdf');

// Multiple files
await page.setInputFiles('input[type="file"]', ['file1.pdf', 'file2.pdf']);
```

## Recording Script Template

```typescript
// scripts/record-[name].ts
import { chromium } from 'playwright';
import * as fs from 'fs';
import * as path from 'path';

const CONFIG = {
  url: 'https://example.com',
  outputName: 'demo-name',
  viewport: { width: 1920, height: 1080 },
  slowMo: 50,
};

async function record() {
  console.log(`Starting recording: ${CONFIG.outputName}`);

  const browser = await chromium.launch({
    slowMo: CONFIG.slowMo,
    headless: true,
  });

  const context = await browser.newContext({
    viewport: CONFIG.viewport,
    recordVideo: {
      dir: './temp-recordings',
      size: CONFIG.viewport,
    },
  });

  const page = await context.newPage();

  try {
    // === RECORDING ACTIONS START ===

    await page.goto(CONFIG.url);
    await page.waitForTimeout(2000);

    // Add your actions here...

    await page.waitForTimeout(2000);

    // === RECORDING ACTIONS END ===

  } catch (error) {
    console.error('Recording failed:', error);
  } finally {
    await context.close();

    // Move video to public/demos
    const video = page.video();
    const videoPath = await video?.path();

    if (videoPath) {
      const destDir = './public/demos';
      fs.mkdirSync(destDir, { recursive: true });

      const destPath = path.join(destDir, `${CONFIG.outputName}.webm`);
      fs.renameSync(videoPath, destPath);
      console.log(`✓ Saved: ${destPath}`);

      // Reminder to convert
      console.log(`\nConvert to MP4 for Remotion:`);
      console.log(`ffmpeg -i ${destPath} -c:v libx264 -crf 20 -movflags faststart ${destPath.replace('.webm', '.mp4')}`);
    }

    await browser.close();
  }
}

record();
```

## Duration Calculation

After recording, get duration for Remotion config:

```bash
# Get duration in seconds
ffprobe -v error -show_entries format=duration -of csv=p=0 recording.webm

# Calculate frames (30fps)
# duration_seconds * 30 = frames
```

```typescript
// In Node.js
import { execSync } from 'child_process';

function getVideoDuration(filePath: string): number {
  const output = execSync(
    `ffprobe -v error -show_entries format=duration -of csv=p=0 "${filePath}"`
  ).toString().trim();
  return parseFloat(output);
}

function getFrameCount(filePath: string, fps = 30): number {
  const duration = getVideoDuration(filePath);
  return Math.ceil(duration * fps);
}
```
