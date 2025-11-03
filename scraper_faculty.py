import requests
from bs4 import BeautifulSoup
import json
import time
import re

BASE_URL = "https://engineering.purdue.edu"
FACULTY_URL = f"{BASE_URL}/ECE/People/Faculty"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def clean_name(name):
    """Add missing spaces between name parts like 'JosephMakin' or 'M.Lukens'."""
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    name = re.sub(r'\.([A-Z])', r'. \1', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def scrape_faculty_list():
    res = requests.get(FACULTY_URL, headers=HEADERS)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    faculty_entries = []
    for div in soup.select("div.people-list div.row"):
        name_tag = div.select_one("div.list-name a")
        if not name_tag:
            continue
        raw_name = name_tag.get_text(strip=True)
        name = clean_name(raw_name)
        link = name_tag.get("href")
        if link.startswith("/"):
            link = BASE_URL + link

        title_tag = div.select_one("div.short-title")
        email_tag = div.select_one("div.email a")

        faculty_entries.append({
            "name": name,
            "profile_link": link,
            "title": title_tag.get_text(strip=True) if title_tag else None,
            "email": email_tag.get_text(strip=True) if email_tag else None,
        })

    print(f"✅ Found {len(faculty_entries)} faculty entries.")
    return faculty_entries


def scrape_faculty_details(profile_url):
    """Extract research, website, and other info from an individual faculty page."""
    try:
        res = requests.get(profile_url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        # --- Research ---
        research = None
        research_p = soup.select_one("p.profile-research")
        if research_p:
            research = research_p.get_text(" ", strip=True)
        else:
            # fallback: <h2>Research</h2> → next <p>
            research_header = soup.find("h2", string=lambda s: s and "research" in s.lower())
            if research_header:
                next_p = research_header.find_next("p")
                if next_p:
                    research = next_p.get_text(" ", strip=True)
        research = research or "Not listed"

        # --- Website ---
        website = None
        contact_info = soup.select_one("div.profile-contact-info")
        if contact_info:
            for strong in contact_info.find_all("strong"):
                if "webpage" in strong.get_text(strip=True).lower():
                    a_tag = strong.find_next("a", href=True)
                    if a_tag:
                        website = a_tag["href"]
                        break
        website = website or profile_url  # fallback to Purdue page

        # --- Optional: Title correction ---
        title_tag = soup.select_one("div.profile-titles")
        title = title_tag.get_text(strip=True) if title_tag else None

        return {
            "research": research,
            "website": website,
            "title": title,
        }

    except Exception as e:
        print(f"⚠️ Error fetching {profile_url}: {e}")
        return {"research": "Not listed", "website": profile_url}


def main():
    faculty_list = scrape_faculty_list()
    full_data = []

    for i, f in enumerate(faculty_list, start=1):
        print(f"[{i}/{len(faculty_list)}] Fetching {f['name']} ...")
        details = scrape_faculty_details(f["profile_link"])
        f.update(details)
        full_data.append(f)

    with open("faculty.json", "w") as f_out:
        json.dump(full_data, f_out, indent=2)
    print("\n✅ Done! Data saved to faculty.json")


if __name__ == "__main__":
    main()
