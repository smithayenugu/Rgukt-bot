"""scrape_rgukt.py - Scrape ALL RGUKT Basar website pages for vector store"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time, json, os

DELAY = 0.1
OUTPUT_FILE = "rgukt_scraped_content.txt"
URLS_JSON = "rgukt_all_urls.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

ALL_URLS = [
    "https://www.rgukt.ac.in/", "https://www.rgukt.ac.in/index.html",
    "https://www.rgukt.ac.in/about-introduction.html", "https://www.rgukt.ac.in/about-rgukt.html",
    "https://www.rgukt.ac.in/vision-mission.html", "https://www.rgukt.ac.in/awards.html",
    "https://www.rgukt.ac.in/vc.html", "https://www.rgukt.ac.in/vc-succession.html",
    "https://www.rgukt.ac.in/gc.html", "https://www.rgukt.ac.in/director.html",
    "https://www.rgukt.ac.in/administration-section.html", "https://www.rgukt.ac.in/cd.html",
    "https://www.rgukt.ac.in/deans-and-hods.html",
    "https://www.rgukt.ac.in/academicprogrammes.html", "https://www.rgukt.ac.in/curricula.html",
    "https://www.rgukt.ac.in/academiccalender.html", "https://www.rgukt.ac.in/departments.html",
    "https://www.rgukt.ac.in/examination.html", "https://www.rgukt.ac.in/time-table.html",
    "https://www.rgukt.ac.in/cse.html", "https://www.rgukt.ac.in/cse-Curriculum.html",
    "https://www.rgukt.ac.in/cse-faculty.html", "https://www.rgukt.ac.in/cse-staff.html",
    "https://www.rgukt.ac.in/cse-labmanual.html",
    "https://www.rgukt.ac.in/ece.html", "https://www.rgukt.ac.in/ece-Curriculum.html",
    "https://www.rgukt.ac.in/ece-faculty.html", "https://www.rgukt.ac.in/ece-staff.html",
    "https://www.rgukt.ac.in/ece-labmanual.html",
    "https://www.rgukt.ac.in/me.html", "https://www.rgukt.ac.in/me-Curriculum.html",
    "https://www.rgukt.ac.in/me-faculty.html", "https://www.rgukt.ac.in/me-staff.html",
    "https://www.rgukt.ac.in/me-labmanual.html",
    "https://www.rgukt.ac.in/che.html", "https://www.rgukt.ac.in/che-Curriculum.html",
    "https://www.rgukt.ac.in/che-faculty.html", "https://www.rgukt.ac.in/che-staff.html",
    "https://www.rgukt.ac.in/che-labmanual.html",
    "https://www.rgukt.ac.in/ce.html", "https://www.rgukt.ac.in/ce-Curriculum.html",
    "https://www.rgukt.ac.in/ce-faculty.html", "https://www.rgukt.ac.in/ce-staff.html",
    "https://www.rgukt.ac.in/ce-labmanual.html",
    "https://www.rgukt.ac.in/mme.html", "https://www.rgukt.ac.in/mme-Curriculum.html",
    "https://www.rgukt.ac.in/mme-faculty.html", "https://www.rgukt.ac.in/mme-staff.html",
    "https://www.rgukt.ac.in/mme-labmanual.html",
    "https://www.rgukt.ac.in/eee.html", "https://www.rgukt.ac.in/eee-Curriculum.html",
    "https://www.rgukt.ac.in/eee-faculty.html", "https://www.rgukt.ac.in/eee-staff.html",
    "https://www.rgukt.ac.in/eee-labmanual.html",
    "https://www.rgukt.ac.in/bio-sciences.html", "https://www.rgukt.ac.in/bio-sciences-Curriculum.html",
    "https://www.rgukt.ac.in/bio-sciences-faculty.html", "https://www.rgukt.ac.in/bio-sciences-staff.html",
    "https://www.rgukt.ac.in/bio-sciences-labmanual.html",
    "https://www.rgukt.ac.in/chemistry.html", "https://www.rgukt.ac.in/chemistry-Curriculum.html",
    "https://www.rgukt.ac.in/chemistry-faculty.html", "https://www.rgukt.ac.in/chemistry-staff.html",
    "https://www.rgukt.ac.in/chemistry-labmanual.html",
    "https://www.rgukt.ac.in/hss.html", "https://www.rgukt.ac.in/hss-Curriculum.html",
    "https://www.rgukt.ac.in/hss-faculty.html", "https://www.rgukt.ac.in/hss-staff.html",
    "https://www.rgukt.ac.in/hss-labmanual.html",
    "https://www.rgukt.ac.in/maths.html", "https://www.rgukt.ac.in/maths-Curriculum.html",
    "https://www.rgukt.ac.in/maths-faculty.html", "https://www.rgukt.ac.in/maths-staff.html",
    "https://www.rgukt.ac.in/maths-labmanual.html",
    "https://www.rgukt.ac.in/physics.html", "https://www.rgukt.ac.in/physics-Curriculum.html",
    "https://www.rgukt.ac.in/physics-faculty.html", "https://www.rgukt.ac.in/physics-staff.html",
    "https://www.rgukt.ac.in/physics-labmanual.html",
    "https://www.rgukt.ac.in/schoolmng.html", "https://www.rgukt.ac.in/schoolmng-Curriculum.html",
    "https://www.rgukt.ac.in/schoolmng-faculty.html", "https://www.rgukt.ac.in/schoolmng-staff.html",
    "https://www.rgukt.ac.in/schoolmng-labmanual.html",

    "https://www.rgukt.ac.in/library/index.html", "https://www.rgukt.ac.in/library/objectives.html",
    "https://www.rgukt.ac.in/library/services.html", "https://www.rgukt.ac.in/library/rules.html",
    "https://www.rgukt.ac.in/library/enhancements.html", "https://www.rgukt.ac.in/library/periodicals.html",
    "https://www.rgukt.ac.in/library/digital-library.html", "https://www.rgukt.ac.in/library/staff.html",
    "https://www.rgukt.ac.in/library/contact.html",
    "https://www.rgukt.ac.in/placement/index.html", "https://www.rgukt.ac.in/placement/scroll_gallery.html",
    "https://www.rgukt.ac.in/hostels.html", "https://www.rgukt.ac.in/counseling.html",
    "https://www.rgukt.ac.in/hospital.html", "https://www.rgukt.ac.in/shopping-complex.html",
    "https://www.rgukt.ac.in/e-cell.html", "https://www.rgukt.ac.in/swayam-nptel.html",
    "https://www.rgukt.ac.in/rd.html", "https://www.rgukt.ac.in/iqac.html",
    "https://www.rgukt.ac.in/rd-facilities.html", "https://www.rgukt.ac.in/rd-guest-lectures.html",
    "https://www.rgukt.ac.in/rd-publications.html", "https://www.rgukt.ac.in/rd-outreach.html",
    "https://www.rgukt.ac.in/rd-consultancy-charges.html", "https://www.rgukt.ac.in/rd-news-updates.html",
    "https://www.rgukt.ac.in/anti-ragging.html", "https://www.rgukt.ac.in/grievance.html",
    "https://www.rgukt.ac.in/cgc.html", "https://www.rgukt.ac.in/pdc.html",
    "https://www.rgukt.ac.in/cbc.html", "https://www.rgukt.ac.in/Cultural-Social-Activity-Club.html",
    "https://www.rgukt.ac.in/sc-st-cell.html", "https://www.rgukt.ac.in/uic.html",
    "https://www.rgukt.ac.in/alumni.html", "https://www.rgukt.ac.in/stu-edurgukt.html",
    "https://www.rgukt.ac.in/stu-campuslife.html", "https://www.rgukt.ac.in/admissions2026.html",
    "https://www.rgukt.ac.in/gallery-album.html",
    "https://www.rgukt.ac.in/rti.html", "https://www.rgukt.ac.in/notices-downloads.html",
    "https://www.rgukt.ac.in/tenders.html",
    "https://www.rgukt.ac.in/term-of-use.html", "https://www.rgukt.ac.in/disclaimer.html",
    "https://www.rgukt.ac.in/contactus.html",
]



def clean_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup.find_all(["script","style","nav","footer","noscript","iframe","form"]):
        t.decompose()
    body = soup.find("body") or soup
    text = body.get_text(separator="\n", strip=True)
    return "\n".join(l.strip() for l in text.split("\n") if len(l.strip()) > 2)


def get_title(soup, url):
    t = soup.find("title")
    if t and t.text.strip():
        return t.text.strip()
    return urlparse(url).path.strip("/").replace("-"," ").replace("_"," ").title() or "Homepage"


def scrape_batch(start=0, end=None):
    urls = ALL_URLS[start:end] if end else ALL_URLS[start:]
    print(f"Scraping {len(urls)} pages (batch {start}-{start+len(urls)-1})...")
    sections, discovered = [], {}
    ok, fail = 0, 0
    for i, url in enumerate(urls, start+1):
        print(f"[{i}/{len(ALL_URLS)}] {url}")
        try:
            r = requests.get(url, timeout=10, headers=HEADERS)
            r.raise_for_status()
            if "html" not in r.headers.get("Content-Type","").lower():
                print("  -> Not HTML"); continue
            soup = BeautifulSoup(r.content, "html.parser")
            title = get_title(soup, url)
            discovered[url] = title
            text = clean_text(r.content)
            if text.strip():
                sections.append(f"=== {title} ===\nSource: {url}\n\n{text}\n")
                ok += 1; print(f"  -> OK, {len(text)} chars")
            else:
                fail += 1; print("  -> Empty")
            time.sleep(DELAY)
        except Exception as e:
            fail += 1; print(f"  -> FAILED: {e}")
            # Record failed URL for later cleanup
            with open("rgukt_failed_urls.txt", "a") as ff:
                ff.write(f"{url} | {str(e)[:80]}\n")
    # Append to output files
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write("\n\n".join(sections))
        if sections:
            f.write("\n\n")
    existing = {}
    failed_urls = []
    if os.path.exists(URLS_JSON):
        with open(URLS_JSON) as f:
            existing = json.load(f)
    existing.update(dict(discovered))
    # Track failed URLs
    failed_file = "rgukt_failed_urls.txt"
    failed_urls = []
    if os.path.exists(failed_file):
        with open(failed_file) as f:
            failed_urls = [line.strip() for line in f if line.strip()]
    # Also track total across batches via a simple counter file
    counter_file = ".scrape_progress.json"
    total_ok = ok
    total_fail = fail
    if os.path.exists(counter_file):
        with open(counter_file) as f:
            prev = json.load(f)
            total_ok += prev.get("ok", 0)
            total_fail += prev.get("fail", 0)
    with open(counter_file, "w") as f:
        json.dump({"ok": total_ok, "fail": total_fail}, f)
    with open(URLS_JSON, "w") as f:
        json.dump({"urls": list(existing.items()), "count": len(existing)}, f)
    fsize = os.path.getsize(OUTPUT_FILE) if os.path.exists(OUTPUT_FILE) else 0
    print(f"Batch done. File: {fsize:,} bytes | OK: {total_ok}, Failed: {total_fail}")

def main():
    import sys
    # Determine start index from command-line arg, or default to 0 (fresh)
    start_idx = 0
    if len(sys.argv) > 1:
        try:
            start_idx = int(sys.argv[1])
        except ValueError:
            pass
    if start_idx == 0:
        # Fresh start: clear output files
        for f in [OUTPUT_FILE, ".scrape_progress.json"]:
            if os.path.exists(f):
                os.remove(f)
    batch_size = 25
    for batch_start in range(start_idx, len(ALL_URLS), batch_size):
        batch_end = min(batch_start + batch_size, len(ALL_URLS))
        scrape_batch(batch_start, batch_end)
        print(f"--- Pausing between batches ---\n")
    fsize = os.path.getsize(OUTPUT_FILE) if os.path.exists(OUTPUT_FILE) else 0
    print(f"Scrape complete! Output: {OUTPUT_FILE} ({fsize:,} bytes)")

if __name__ == "__main__":
    main()