import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import random
import sys

# Generic async runner with Windows fix
def run_async(coroutine):
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    return asyncio.run(coroutine)

async def _get_industries():
    industries = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            # Navigate to generic search page
            print("Navigating to Lusha directory...")
            await page.goto("https://www.lusha.com/company-search/", timeout=60000)
            
            # Wait for content to load
            await page.wait_for_timeout(3000)

            # Selector based on user screenshot: directory-content-box-col -> a
            elements = await page.locator(".directory-content-box-col a").all()
            
            # Fallback if specific class not found
            if not elements:
                 elements = await page.locator("main a").all()

            for el in elements:
                name = await el.inner_text()
                href = await el.get_attribute("href")
                
                if name and href and "/company-search/" in href:
                    if href.startswith("/"):
                        href = "https://www.lusha.com" + href
                    
                    # Clean name
                    name = name.strip()
                    if name:
                        industries.append({"name": name, "url": href})
            
            # Remove duplicates
            industries = [dict(t) for t in {tuple(d.items()) for d in industries}]
            
        except Exception as e:
            print(f"Error fetching industries: {e}")
        finally:
            await browser.close()
    return industries

async def _get_countries(industry_url):
    countries = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            print(f"Fetching countries from {industry_url}...")
            await page.goto(industry_url, timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Assuming similar structure for countries: directory-content-box-col -> a
            elements = await page.locator(".directory-content-box-col a").all()
            
             # Fallback
            if not elements:
                 elements = await page.locator("main a").all()

            for el in elements:
                name = await el.inner_text()
                href = await el.get_attribute("href")
                
                if name and href:
                    if href.startswith("/"):
                        href = "https://www.lusha.com" + href
                    
                    name = name.strip()
                    if name and "/company-search/" in href:
                        countries.append({"name": name, "url": href})

            # Remove duplicates
            countries = [dict(t) for t in {tuple(d.items()) for d in countries}]

        except Exception as e:
            print(f"Error fetching countries: {e}")
        finally:
            await browser.close()
    return countries

async def _scrape_companies(url):
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            print(f"Scraping companies from {url}...")
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Handle cookies
            try:
                if await page.query_selector("button#onetrust-accept-btn-handler"):
                    await page.click("button#onetrust-accept-btn-handler")
            except: pass

            # Scrape companies
            # User mentioned directory-content-box-row structure
            # We will try to be broad again to capture the list
            company_elements = await page.locator(".directory-content-box a").all()
            if not company_elements:
                 main = page.locator("main")
                 if await main.count() > 0:
                    company_elements = await main.locator("a").all()

            results_seen = set()
            for element in company_elements:
                try:
                    if not await element.is_visible(): continue
                    name = await element.inner_text()
                    href = await element.get_attribute("href")
                    
                    if not name: continue
                    name = name.strip()
                    if len(name) < 2: continue
                    
                    # Filter keywords
                    skip_keywords = ["Privacy Policy", "Terms of Use", "Start for free", "Login", "Sign Up", "About Us", "Contact", "Lusha", "Twitter", "Facebook", "LinkedIn", "Instagram"]
                    if any(k.lower() == name.lower() for k in skip_keywords): continue
                    
                    if not href or "javascript" in href: continue
                    if href.startswith("/"): href = "https://www.lusha.com" + href
                    
                    if href in results_seen: continue
                    results_seen.add(href)

                    results.append({"name": name, "url": href, "linkedin": "N/A"})
                    if len(results) >= 50: break
                except: continue
        except Exception as e:
            print(f"Error scraping companies: {e}")
        finally:
            await browser.close()
    return results

# Synchronous Wrappers
def get_industries():
    return run_async(_get_industries())

def get_countries(industry_url):
    return run_async(_get_countries(industry_url))

def scrape_companies(url):
    return run_async(_scrape_companies(url))
