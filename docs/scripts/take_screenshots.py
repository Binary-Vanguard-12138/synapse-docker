#!/usr/bin/env python3
"""Take screenshots of all web UIs for the README."""

import asyncio
from playwright.async_api import async_playwright

KEYCLOAK = "https://auth.spaceigniter.com"
SYNAPSE = "https://matrix.spaceigniter.com"
NTFY = "https://matrix.spaceigniter.com:2586"
ADMIN_USER = "admin"
ADMIN_PASS = "Hddky51J4Yfsbo79xWK29wmvOvrfoXXvL0wRRaaNiJGwRVT6"
OUT = "/root/synapse-docker/docs/screenshots"


async def shot(page, path, full=False):
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=f"{OUT}/{path}", full_page=full)
    print(f"  saved {path}")


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--no-sandbox", "--ignore-certificate-errors"])
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            ignore_https_errors=True,
        )

        # ── 1. Keycloak login page ────────────────────────────────────────────
        print("Keycloak: login page")
        page = await ctx.new_page()
        await page.goto(f"{KEYCLOAK}/admin/master/console/", wait_until="networkidle")
        await shot(page, "keycloak-login.png")

        # ── 2. Keycloak: log in and show realm list ───────────────────────────
        print("Keycloak: admin console")
        await page.fill("#username", ADMIN_USER)
        await page.fill("#password", ADMIN_PASS)
        await page.click("#kc-login")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)
        await shot(page, "keycloak-admin-home.png")

        # ── 3. Keycloak: switch to matrix realm ──────────────────────────────
        print("Keycloak: matrix realm clients")
        # Navigate via Manage realms, then select matrix
        await page.click("text=Manage realms")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)
        # Click on the matrix realm row
        await page.locator("table tbody tr").filter(has_text="matrix").first.click()
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)
        # Navigate to Clients
        await page.click("a:has-text('Clients')")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)
        await shot(page, "keycloak-matrix-clients.png")

        # ── 4. Keycloak: Users list in matrix realm ───────────────────────────
        print("Keycloak: users list (matrix realm)")
        await page.click("a:has-text('Users')")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)
        await shot(page, "keycloak-users.png")

        # ── 5. MAS account page (unauthenticated login view) ─────────────────
        print("MAS: account/login page")
        page2 = await ctx.new_page()
        await page2.goto(f"{SYNAPSE}/account", wait_until="networkidle")
        await page2.wait_for_timeout(2000)
        await shot(page2, "mas-account-login.png")

        # ── 6. Synapse Admin UI ───────────────────────────────────────────────
        print("Synapse Admin UI")
        page3 = await ctx.new_page()
        await page3.goto(f"{SYNAPSE}/admin", wait_until="networkidle")
        await page3.wait_for_timeout(2000)
        await shot(page3, "synapse-admin.png")

        # ── 7. ntfy web UI ───────────────────────────────────────────────────
        print("ntfy: web UI")
        page4 = await ctx.new_page()
        await page4.goto(NTFY, wait_until="networkidle")
        await page4.wait_for_timeout(2000)
        await shot(page4, "ntfy.png")

        await browser.close()
    print("Done.")


asyncio.run(main())
