import { chromium } from "playwright";

async function main() {
  console.log("Attempting browser launch with msedge channel...");
  try {
    const browser = await chromium.launch({
      channel: "msedge",
      headless: true,
      args: ["--use-gl=angle", "--use-angle=swiftshader"], // or standard webgl
    });
    const page = await browser.newPage();
    await page.goto("http://localhost:3000");
    const title = await page.title();
    console.log("Success! Page title:", title);
    await browser.close();
  } catch (err) {
    console.error("msedge launch failed:", err.message);
    console.log("Attempting chrome channel...");
    const browser = await chromium.launch({
      channel: "chrome",
      headless: true,
    });
    const page = await browser.newPage();
    await page.goto("http://localhost:3000");
    console.log("Success with chrome! Page title:", await page.title());
    await browser.close();
  }
}

main().catch(console.error);
