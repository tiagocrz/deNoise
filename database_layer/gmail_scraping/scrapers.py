from gmail_auth import get_gmail_service
import pandas as pd
from bs4 import BeautifulSoup
from base64 import urlsafe_b64decode
import email.utils
from datetime import datetime, timedelta
import re

# =========================================================================
# Functions to extract all the wanted newsletters from Gmail to a dataset ||
# =========================================================================

def _extract_best_body(payload):
    """Recursively searches all MIME parts for the best (HTML preferred) content."""
    html_body = None
    text_body = None

    if payload.get("mimeType") == "text/html":
        data = payload.get("body", {}).get("data")
        if data:
            html_body = urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    elif payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data")
        if data:
            text_body = urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    elif "parts" in payload:
        for part in payload["parts"]:
            sub_html, sub_text = _extract_best_body(part)
            # keep HTML if found
            if sub_html:
                html_body = (html_body or "") + "\n" + sub_html
            # only use plain text if we still don't have HTML
            if sub_text and not html_body:
                text_body = (text_body or "") + "\n" + sub_text

    return html_body, text_body



def get_newsletters_df(label_name="Newsletters", days=7):
    """
    Fetch newsletters from Gmail issued in the past X days
    from the following senders:
      - dan@tldrnewsletter.com
      - crew@morningbrew.com
      - contact@startupportugal.com

    Returns a DataFrame with:
    ["email_id", "from", "date", "body"]
    """
    service = get_gmail_service()

    # Gmail search query: label + date range
    after_date = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
    query = f'label:"{label_name}" after:{after_date}'

    results = service.users().messages().list(
        userId="me",
        q=query
    ).execute()

    messages = results.get("messages", [])
    email_records = []

    allowed_senders = {
        "dan@tldrnewsletter.com",
        "crew@morningbrew.com",
        "contact@startupportugal.com"
    }

    for msg in messages:
        msg_id = msg["id"]
        msg_detail = service.users().messages().get(
            userId="me", id=msg_id, format="full"
        ).execute()

        payload = msg_detail.get("payload", {})
        headers = payload.get("headers", [])
        sender_raw = next((h["value"] for h in headers if h["name"] == "From"), "")
        
        # extract clean email address (ignore display name)
        sender_email = sender_raw.lower().strip()
        if "<" in sender_email and ">" in sender_email:
            sender_email = sender_email.split("<")[1].split(">")[0].strip()

        if sender_email not in allowed_senders:
            continue

        # parse date
        date_str = next((h["value"] for h in headers if h["name"] == "Date"), None)
        try:
            date_obj = datetime.fromtimestamp(
                email.utils.mktime_tz(email.utils.parsedate_tz(date_str))
            )
        except Exception:
            date_obj = None

        # skip if date outside the window (Gmail query isn't perfect)
        if not date_obj or date_obj < datetime.now() - timedelta(days=days):
            continue

        body_html, body_text = _extract_best_body(payload)
        body = body_html or body_text or ""

        email_records.append({
            "email_id": msg_id,
            "from": sender_email,
            "date": date_obj,
            "body": body
        })

    return pd.DataFrame(email_records)


# ==============
# TLDR Scraper ||
# ==============

def extract_news_from_TLDR(email_row):
    """
    Extracts structured news items (id, title, text, date)
    from a newsletter's HTML content.
    """
    email_id = email_row["email_id"]
    date = email_row["date"]
    html = email_row["body"]

    soup = BeautifulSoup(html, "html.parser")
    news_items = []

    # TLDR and similar newsletters often use <div class="text-block"> for each story
    for block in soup.find_all("div", class_="text-block"):
        # Title: usually in <strong>
        title_tag = block.find("strong")
        title = title_tag.get_text(" ", strip=True) if title_tag else None

        # Text: collect all text spans after the title
        body_parts = []
        for span in block.find_all("span"):
            text = span.get_text(" ", strip=True)
            if text and (not title or text != title):
                body_parts.append(text)

        body = " ".join(body_parts).strip()

        if title and body:
            news_items.append({
                "id": f"{email_id}_{len(news_items)+1}",
                "title": title,
                "text": body,
                "date": date
            })

    # Fallback: if no 'text-block' divs were found, use your old generic method
    if not news_items:
        for header in soup.find_all(["h2", "h3", "strong"]):
            title = header.get_text(strip=True)
            body_parts = []
            for sibling in header.find_next_siblings():
                if sibling.name in ["h2", "h3", "strong"]:
                    break
                if sibling.name in ["p", "div"]:
                    text = sibling.get_text(" ", strip=True)
                    if text:
                        body_parts.append(text)
            body = " ".join(body_parts)
            if title and body:
                news_items.append({
                    "id": f"{email_id}_{len(news_items)+1}",
                    "title": title,
                    "text": body,
                    "date": date
                })

    return news_items


def cleaning_TLDR_results(news_items):
    # Removing sponsored content and cleaning the reading times from titles and text
    cleaned_items = []
    for item in news_items:
        title = item['title']
        text = item['text']
        if title.strip().endswith("(Sponsor)"):
            continue
        if "(" in title and "minute read" in title:
            text = text[len(title):].strip()
            title = title[:title.rfind("(")].strip()
        cleaned_items.append({
            "id": item['id'],
            "title": title,
            "text": text,
            "date": item['date']
        })

    return pd.DataFrame(cleaned_items)


def final_TLDR_extraction(email_row):
    raw_items = extract_news_from_TLDR(email_row)
    cleaned_items = cleaning_TLDR_results(raw_items)
    return cleaned_items



# =====================
# MorningBrew Scraper ||
# =====================

def extract_news_from_MorningBrew(email_row):
    """
    Extracts structured news items (id, section, title, text, date)
    from a Morning Brew newsletter's HTML content.

    Handels:
    - Market section
    - Standard news (removing image credits and sponsored sections)
    - Tour de headlines section
    - Whats else is brewing section
    """
    email_id = email_row["email_id"]
    date = email_row["date"]
    html = email_row["body"]

    soup = BeautifulSoup(html, "html.parser")
    news_items = []

    story_tables = soup.find_all("table", class_="story-content-container")

    # MARKETS (unchanged)
    markets_text = None
    for li in soup.find_all("li"):
        strong = li.find("strong")
        if strong and "markets" in strong.get_text(strip=True).lower():
            text = li.get_text(" ", strip=True)
            text = re.sub(r'^\s*Markets\s*:?\\s*', '', text, flags=re.I)
            markets_text = text
            break
    if markets_text:
        news_items.append({
            "id": f"{email_id}_{len(news_items)+1}",
            "section": "Markets",
            "title": f"Stock markets {date.strftime('%B %d, %Y')}",
            "text": markets_text,
            "date": date
        })

    IMAGE_CREDIT_RE = re.compile(
        r'^\s*(image|image credit|photo|photo credit|source|credit|courtesy|image courtesy)[:\-\s]',
        re.I
    )

    for story in story_tables:
        section_tag = story.find_previous("h3")
        section = section_tag.get_text(strip=True) if section_tag else None
        title_tag = story.find("h1", class_="story-title")
        title = title_tag.get_text(strip=True) if title_tag else None

        # Tour de headlines (unchanged)
        if section and section.lower() == "world" and title and "tour de" in title.lower():
            content_td = story.find("td", class_="content-container")
            if not content_td:
                continue
            for p in content_td.find_all("p"):
                strong = p.find("strong")
                if not strong:
                    continue
                for img in strong.find_all("img"):
                    img.decompose()
                sub_title = strong.get_text(" ", strip=True).rstrip(".:").strip()
                strong.extract()
                text = p.get_text(" ", strip=True)
                text = re.sub(r"\s+", " ", text).strip()
                if sub_title and text and not text.startswith("Image:"):
                    news_items.append({
                        "id": f"{email_id}_{len(news_items)+1}",
                        "section": section,
                        "title": sub_title,
                        "text": text,
                        "date": date
                    })
            continue

        # STANDARD NEWS: include headers (h2/h3) as content elements
        body_parts = []
        content_td = story.find("td", class_="story-content")
        if content_td:
            # target headings too — many bolded subtitles are <h2>/<h3>
            for element in content_td.find_all(["h2", "h3", "p", "li"], recursive=True):
                # remove embedded images and nodes that often contain credits
                for img in element.find_all("img"):
                    img.decompose()
                for cap in element.find_all(["figcaption", "small", "footer"]):
                    cap.decompose()

                # skip obvious credit lines by class or by regex
                el_classes = element.get("class") or []
                # skips sponsored sections
                if "source" in el_classes or "sponsored-header-image" in el_classes:
                    continue
                
                text = element.get_text(" ", strip=True)
                
                if not text:
                    continue

                if IMAGE_CREDIT_RE.search(text) or text.startswith("Image:") or text.startswith("Source:"):
                    continue

                text = element.get_text(" ", strip=True)
                if not text:
                    continue

                # If this is a heading, preserve it as a subtitle line
                if element.name in ("h2", "h3"):
                    body_parts.append(text)
                    continue

                # For paragraphs/lists: preserve a leading bolded phrase if present
                lead_tag = element.find(["strong", "b"])
                lead_text = None
                if lead_tag:
                    lead_text = lead_tag.get_text(" ", strip=True)
                    lead_tag.extract()

                # re-fetch text after lead extraction to avoid duplication
                text = element.get_text(" ", strip=True)

                if lead_text:
                    text = f"{lead_text} — {text}" if text else lead_text

                # preserve list bullets
                if element.name == "li":
                    body_parts.append(f"• {text}")
                else:
                    body_parts.append(text)

        # WHAT ELSE IS BREWING (unchanged, but using improved credit skipping)
        content_td_alt = story.find("td", class_="content-container")
        if title and "what else is brewing" in (title.lower() if title else "") and content_td_alt:
            for li in content_td_alt.find_all("li"):
                for img in li.find_all("img"):
                    img.decompose()
                for cap in li.find_all(["figcaption", "small", "footer"]):
                    cap.decompose()
                text = li.get_text(" ", strip=True)
                if text and not IMAGE_CREDIT_RE.search(text):
                    news_items.append({
                        "id": f"{email_id}_{len(news_items)+1}",
                        "section": section,
                        "title": text,
                        "text": text,
                        "date": date
                    })
            continue

        # Combine pieces, join with space and keep any heading/subtitle lines
        body = " ".join([bp for bp in body_parts if bp]).strip()

        if title and body:
            news_items.append({
                "id": f"{email_id}_{len(news_items)+1}",
                "section": section,
                "title": title,
                "text": body,
                "date": date,
            })

    return news_items


def cleaning_MorningBrew_results(news_items):
    # Removes the columns "Section" from all the news items
    cleaned_items = []
    for item in news_items:
        cleaned_items.append({
            "id": item['id'],
            "title": item['title'],
            "text": item['text'],
            "date": item['date']
        })

    return pd.DataFrame(cleaned_items)


def final_MorningBrew_extraction(email_row):
    raw_items = extract_news_from_MorningBrew(email_row)
    cleaned_items = cleaning_MorningBrew_results(raw_items)
    return cleaned_items


# =========================
# StartupPortugal Scraper ||
# =========================

def extract_news_from_StartupPortugal(email_row):
    """
    Extract ONLY 'Ecosystem Stream' news.
    Returns rows: {"id", "title", "text", "date"}.
    Stops when 'Shameless Self Promotion' appears.
    Appends 'read more' links directly into the text body.
    """

    soup = BeautifulSoup(email_row["body"], "html.parser")
    email_id, date = email_row["email_id"], email_row["date"]
    news_items = []

    # find start of the 'Ecosystem Stream' section
    header = soup.find(lambda t: t.name in ("span", "strong", "p")
                       and "ecosystem stream" in t.get_text(strip=True).lower())
    section_table = header.find_parent("table") if header else None
    if not section_table:
        return news_items

    pending_title = None

    for tbl in section_table.find_all_next("table"):
        txt = tbl.get_text(" ", strip=True)
        if not txt:
            continue
        if "shameless self promotion" in txt.lower():
            break

        for td in tbl.find_all("td", class_="mcnTextContent"):
            text = td.get_text(" ", strip=True)
            if not text or len(text.split()) < 5:
                continue

            # --- Extract "read more"-style link ---
            read_more = None
            for a in td.find_all("a", href=True):
                if any(k in a.get_text(" ", strip=True).lower() for k in ["read", "more", "here", "learn", "apply"]):
                    read_more = a["href"]
                    break

            a = td.find("a")
            if a:
                title = (a.find("strong") or a).get_text(" ", strip=True)
                body = text.replace(title, "", 1).strip() if title in text else ""
                if read_more:
                    body = f"{body} Read more: {read_more}"
                if len(body.split()) > 5:
                    news_items.append({
                        "id": f"{email_id}_{len(news_items)+1}",
                        "title": title,
                        "text": body,
                        "date": date
                    })
                    pending_title = None
                else:
                    pending_title = title
                continue

            if pending_title and len(text.split()) > 5:
                if read_more:
                    text = f"{text} Read more: {read_more}"
                news_items.append({
                    "id": f"{email_id}_{len(news_items)+1}",
                    "title": pending_title,
                    "text": text,
                    "date": date
                })
                pending_title = None

    return news_items


def cleaning_StartupPortugal_results(news_items):
    # Removing duplicated titles
    cleaned_items = []
    seen_titles = set()
    for item in news_items:
        title = item['title']
        if title in seen_titles:
            continue
        seen_titles.add(title)
        cleaned_items.append({
            "id": item['id'],
            "title": title,
            "text": item['text'],
            "date": item['date']
        })

    return pd.DataFrame(cleaned_items)


def final_StartupPortugal_extraction(email_row):
    raw_items = extract_news_from_StartupPortugal(email_row)
    cleaned_items = cleaning_StartupPortugal_results(raw_items)
    return cleaned_items