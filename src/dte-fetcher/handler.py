import os
import re
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


LOGIN_BUTTON_REGEX = re.compile(r"iniciar|ingresar|entrar|login", re.IGNORECASE)


def _fill_login_if_present(page, username: str, password: str) -> bool:
    pw_inputs = page.locator("input[type='password']")
    if pw_inputs.count() == 0:
        return True

    user_input = page.locator(
        "input[type='email'], input[name*='user' i], input[id*='user' i], input[name*='correo' i]"
    ).first
    if user_input.count() == 0:
        user_input = page.locator("input[type='text']").first

    if user_input.count() == 0:
        return False

    try:
        user_input.fill(username)
        pw_inputs.first.fill(password)

        login_btn = page.get_by_role("button", name=LOGIN_BUTTON_REGEX)
        if login_btn.count() > 0:
            login_btn.first.click()
        else:
            btn_by_text = page.get_by_text(LOGIN_BUTTON_REGEX)
            if btn_by_text.count() > 0:
                btn_by_text.first.click()
            else:
                pw_inputs.first.press("Enter")
        return True
    except Exception:
        return False


def fetch_pdf_from_dte_detail(
    fiscal_tax_document_id: str,
    username: str,
    password: str,
    out_dir: str = "/tmp/downloads",
    headless: bool = True,
) -> Optional[str]:
    url = (
        "https://vitacura-dte.moit.cl/qapps/MoitDte/DteDetail?fiscalTaxDocumentId="
        + str(fiscal_tax_document_id)
    )

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        page.goto(url, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except PlaywrightTimeoutError:
            pass

        _ = _fill_login_if_present(page, username, password)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except PlaywrightTimeoutError:
            pass

        pdf_locators = [
            page.get_by_role("link", name=re.compile("pdf", re.I)),
            page.get_by_role("button", name=re.compile("pdf", re.I)),
            page.get_by_text(re.compile(r"\bPDF\b", re.I)),
        ]

        pdf_clickable = None
        for loc in pdf_locators:
            if loc.count() > 0:
                pdf_clickable = loc.first
                break

        if pdf_clickable is None:
            maybe_pdf = page.locator("a[href*='pdf'], button[id*='pdf' i], a[id*='pdf' i]")
            if maybe_pdf.count() > 0:
                pdf_clickable = maybe_pdf.first

        if pdf_clickable is None:
            browser.close()
            return None

        # 1) Intentar evento de descarga directo
        try:
            with page.expect_download(timeout=8000) as dl_info:
                pdf_clickable.click()
            download = dl_info.value
            suggested = download.suggested_filename or f"{fiscal_tax_document_id}.pdf"
            dest = out_path / suggested
            download.save_as(dest.as_posix())
            browser.close()
            return dest.as_posix()
        except PlaywrightTimeoutError:
            pass

        # 2) Intentar popup con PDF
        popup = None
        try:
            with page.expect_popup(timeout=5000) as pop_info:
                pdf_clickable.click()
            popup = pop_info.value
        except PlaywrightTimeoutError:
            pass

        def _await_pdf_response(p):
            try:
                resp = p.wait_for_event(
                    "response",
                    timeout=8000,
                    predicate=lambda r: "application/pdf" in (r.headers.get("content-type", "").lower()),
                )
                return resp
            except PlaywrightTimeoutError:
                return None

        if popup is not None:
            resp = _await_pdf_response(popup)
            if resp is not None:
                cd = resp.headers.get("content-disposition", "")
                m = re.search(r'filename="([^"]+)"', cd)
                suggested = m.group(1) if m else f"{fiscal_tax_document_id}.pdf"
                dest = out_path / suggested
                body = resp.body()
                dest.write_bytes(body)
                browser.close()
                return dest.as_posix()

        captured = {"resp": None}

        def on_response(r):
            try:
                ct = r.headers.get("content-type", "").lower()
                if "application/pdf" in ct and captured["resp"] is None:
                    captured["resp"] = r
            except Exception:
                pass

        page.on("response", on_response)
        pdf_clickable.click()
        page.wait_for_timeout(3000)
        if captured["resp"] is not None:
            resp = captured["resp"]
            cd = resp.headers.get("content-disposition", "")
            m = re.search(r'filename="([^"]+)"', cd)
            suggested = m.group(1) if m else f"{fiscal_tax_document_id}.pdf"
            dest = out_path / suggested
            body = resp.body()
            dest.write_bytes(body)
            browser.close()
            return dest.as_posix()

        browser.close()
        return None


def lambda_handler(event, context):
    fiscal_id = (
        event.get("id")
        or event.get("fiscalTaxDocumentId")
        or event.get("fiscal_tax_document_id")
    )
    if not fiscal_id:
        return {"statusCode": 400, "body": "Missing fiscalTaxDocumentId in event"}

    user = os.environ.get("VITACURA_DTE_USER")
    passwd = os.environ.get("VITACURA_DTE_PASS")
    if not user or not passwd:
        return {"statusCode": 500, "body": "Missing VITACURA_DTE_USER/VITACURA_DTE_PASS env vars"}

    path = fetch_pdf_from_dte_detail(
        fiscal_tax_document_id=str(fiscal_id),
        username=user,
        password=passwd,
        out_dir="/tmp/downloads",
        headless=True,
    )

    if path:
        return {"statusCode": 200, "body": path}
    else:
        return {"statusCode": 200, "body": "No PDF download detected"}
