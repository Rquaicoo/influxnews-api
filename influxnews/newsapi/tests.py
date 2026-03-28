"""
smart_scraper.py  v2
────────────────────
Selector-free news-feed scraper.

Goal
────
Extract EVERY news item on a listing page — each with:
  • title
  • link  (absolute URL)
  • image (absolute URL, if any)
  • published date / timestamp

Algorithm
─────────
Phase 1 — Candidate collection
  Walk the DOM.  A "card candidate" is any element that:
    - is a block tag (article, li, div, section, …)
    - contains at least one <a> with non-trivial link text  (≥3 words)
    - is not inside nav / footer / aside / header

Phase 2 — Feature extraction (per candidate)
  Each candidate gets a numeric vector:
    depth, word_count, link_count, has_img, has_date,
    text/link_ratio, child_count, sibling_similarity,
    positive_signal, negative_signal, a_href_is_internal,
    img_count, heading_count, time_tag

Phase 3 — DBSCAN structural clustering
  We cluster candidates by (depth, child_count, word_count) to find
  the dominant repeating structure — the "card template".
  DBSCAN is ideal here: it finds dense groups of similar elements
  without requiring a fixed k, and flags outliers (noise) automatically.

Phase 4 — Winner selection
  Score each cluster by:
    - cluster size  (more cards = more likely feed)
    - avg internal link ratio  (cards link *out* to articles)
    - presence of headings / images
    - absence of nav/footer signals
  Pick the best cluster.

Phase 5 — Field extraction (per card)
  From each card in the winning cluster:
    title   ← longest heading text OR longest anchor text
    link    ← href of the anchor that carries the title
    image   ← src / data-src of first <img> or og:image attr
    date    ← <time datetime="…"> OR text matching date patterns,
              OR JSON-LD datePublished

Usage
─────
    python smart_scraper.py <url> [<url2> ...]

    # library:
    from smart_scraper import scrape_feed
    items = scrape_feed("https://techcrunch.com")
    for item in items:
        print(item)
"""

import sys, re, json, time, hashlib, warnings, urllib.parse
from dataclasses import dataclass, asdict, field
from typing import Optional

import requests
import numpy as np
from bs4 import BeautifulSoup, Tag
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ── Constants ────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

PRUNE_TAGS = {"script", "style", "noscript", "iframe", "svg",
              "path", "symbol", "defs", "form", "input", "button",
              "select", "textarea"}

BOILERPLATE_ANCESTORS = {"nav", "footer", "header", "aside"}
BOILERPLATE_CLASSES = {"sidebar", "breadcrumb", "pagination", "footer", "nav", "navigation", "header"}
CARD_TAGS = {"article", "li", "div", "section", "tr", "figure"}

# Placeholder image patterns to exclude
PLACEHOLDER_PATTERNS = {
    "grey-placeholder", "placeholder", "grey.png", 
    "default.png", "no-image", "loading", "transparent.gif"
}
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

DATE_RE = re.compile(
    r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s*\d{4}"
    r"|\b\d{4}[-/]\d{2}[-/]\d{2}\b"
    r"|\b\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*,?\s*\d{4}"
    r"|\b\d+\s+(?:hour|minute|day|week|month)s?\s+ago\b"
    r"|\byesterday\b|\bjust now\b",
    re.I,
)

POSITIVE_RE = re.compile(
    r"card|item|article|post|story|entry|news|feed|teaser|preview|result|tile|block",
    re.I,
)
NEGATIVE_RE = re.compile(
    r"sidebar|widget|ad|banner|promo|comment|share|social|cookie|popup|modal"
    r"|pagination|breadcrumb|tag|label|author-bio|newsletter|signup",
    re.I,
)

IMG_ATTRS = ["src", "data-src", "data-lazy-src", "data-original",
             "data-srcset", "srcset", "data-img"]


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class NewsItem:
    title: str = ""
    link: str = ""
    image: str = ""
    published: str = ""

    def is_valid(self):
        return bool(self.title and self.link)


@dataclass
class FeedResult:
    url: str
    items: list = field(default_factory=list)
    n_candidates: int = 0
    n_clusters: int = 0
    winning_cluster_size: int = 0
    extraction_ms: int = 0
    error: Optional[str] = None


@dataclass
class CardFeatures:
    depth: float
    word_count: float
    direct_child_count: float
    link_count: float
    img_count: float
    heading_count: float
    has_date: float
    has_time_tag: float
    positive_signal: float
    negative_signal: float


# ── Helpers ───────────────────────────────────────────────────────────────────

def _attr(tag: Tag) -> str:
    return " ".join(tag.get("class", [])) + " " + tag.get("id", "")


def _depth(tag: Tag) -> int:
    d = 0
    p = tag.parent
    while p and p.name not in (None, "[document]", "html", "body"):
        d += 1
        p = p.parent
    return d


def _has_boilerplate_ancestor(tag: Tag) -> bool:
    for ancestor in tag.parents:
        if isinstance(ancestor, Tag) and ancestor.name in BOILERPLATE_ANCESTORS:
            return True
    return False


def _abs_url(base: str, href: str) -> str:
    if not href:
        return ""
    href = href.strip()
    if href.startswith(("http://", "https://")):
        return href
    if href.startswith("//"):
        scheme = urllib.parse.urlparse(base).scheme
        return f"{scheme}:{href}"
    return urllib.parse.urljoin(base, href)


def _best_img(tag: Tag, base_url: str) -> str:
    for img in tag.find_all("img"):
        for attr in IMG_ATTRS:
            val = img.get(attr, "")
            if val:
                if " " in val:
                    val = val.split()[0]
                if val and not val.startswith("data:"):
                    # Check if it's a placeholder
                    val_lower = val.lower()
                    if any(p in val_lower for p in PLACEHOLDER_PATTERNS):
                        continue
                    return _abs_url(base_url, val)
    return ""


def _extract_date(tag: Tag) -> str:
    # Priority 1: <time datetime="…">
    time_el = tag.find("time")
    if time_el:
        dt = time_el.get("datetime", "").strip()
        if dt and _is_valid_date(dt):
            return dt
        txt = time_el.get_text(strip=True)
        if txt and len(txt) < 100 and _is_valid_date(txt):
            return txt

    # Priority 2: Class/id with date pattern
    for el in tag.find_all(True):
        attr = _attr(el).lower()
        if re.search(r"date|time|timestamp|publish", attr):
            txt = el.get_text(strip=True)
            if txt and len(txt) < 80 and _is_valid_date(txt):
                return txt

    # Priority 3: Regex search in text
    text = tag.get_text(" ", strip=True)
    m = DATE_RE.search(text)
    if m:
        date_str = m.group(0).strip()
        if len(date_str) < 100:
            return date_str

    return ""


def _is_valid_date(text: str) -> bool:
    """
    Validate that text looks like a date.
    Avoid garbled text or utility labels.
    """
    if not text or len(text) > 100:
        return False
    
    # Reject obvious false positives
    if any(x in text.lower() for x in {"select", "category", "sign up", "try", "read more"}):
        return False
    
    return bool(DATE_RE.search(text))


def _extract_title_and_link(tag: Tag, base_url: str):
    """
    Extract title and link with validation.
    Ensures the title is actually associated with the link.
    """
    # Strategy 1: Find heading inside an anchor (most reliable)
    for h in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        headings = tag.find_all(h)
        if headings:
            best = max(headings, key=lambda el: len(el.get_text(strip=True)))
            title = best.get_text(strip=True)
            if not title or len(title.split()) < 3:
                continue
            
            # Try to find anchor that contains or wraps this heading
            link = ""
            for ancestor in [best] + list(best.parents):
                if isinstance(ancestor, Tag) and ancestor.name == "a" and ancestor.get("href"):
                    link = _abs_url(base_url, ancestor.get("href"))
                    break
            
            if link and not _is_navigation_link(link, base_url):
                return title, link

    # Strategy 2: Best anchor by link text (must be substantial)
    anchors = tag.find_all("a", href=True)
    best_anchor, best_len = None, 0
    
    for a in anchors:
        txt = a.get_text(strip=True)
        txt_words = txt.split()
        
        # Filter: must have ≥3 words, no author/nav patterns
        if len(txt_words) < 3:
            continue
        if any(p in txt.lower() for p in {"by ", "author", "sign up", "more"}):
            continue
        
        href = _abs_url(base_url, a["href"])
        if _is_navigation_link(href, base_url):
            continue
        
        if len(txt) > best_len:
            best_len = len(txt)
            best_anchor = a

    if best_anchor:
        href = _abs_url(base_url, best_anchor["href"])
        text = best_anchor.get_text(strip=True)
        if text and not _is_navigation_link(href, base_url):
            return text, href

    return "", ""


def _is_navigation_link(url: str, base_url: str) -> bool:
    """Check if URL points to navigation/category rather than article."""
    url_lower = url.lower()
    base_lower = base_url.lower().rstrip("/")
    
    # Exclude category/archive/tag pages
    nav_patterns = {"/category/", "/archive/", "/tag/", "/author/", 
                    "/page/", "/search", "category=", "tag=", 
                    "#", "javascript:", "mailto:"}
    
    if any(p in url_lower for p in nav_patterns):
        return True
    
    # Avoid self-links
    if url_lower.rstrip("/") == base_lower:
        return True
    
    return False


def _is_title_link_valid(title: str, link: str) -> bool:
    """
    Validate that title and link seem to belong together.
    Rejects mismatches like category links or author pages.
    """
    title_lower = title.lower()
    link_lower = link.lower()
    
    # Reject obviously bad pairings
    bad_titles = {"by ", "author ", "next", "prev", "more", "latest news", 
                  "popular", "upcoming events", "category", "tag"}
    
    if any(t in title_lower for t in bad_titles):
        # Exception: allow if title is just the keyword
        if title_lower not in bad_titles:
            pass
        else:
            return False
    
    # If link contains category but title doesn't mention categories, reject
    if "/category/" in link_lower and "category" not in title_lower:
        return False
    
    return True


def _fetch_cover_image(link: str) -> str:
    """
    Fetch the article page and extract the cover image.
    Tries og:image meta tag first (most reliable), then article images.
    Returns empty string if fetch fails or no image found.
    """
    try:
        resp = requests.get(link, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        
        # Priority 1: og:image meta tag (most reliable for articles)
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            img_url = og_image.get("content", "").strip()
            if img_url and not any(p in img_url.lower() for p in PLACEHOLDER_PATTERNS):
                return _abs_url(link, img_url)
        
        # Priority 2: twitter:image meta tag
        tw_image = soup.find("meta", {"name": "twitter:image"})
        if tw_image and tw_image.get("content"):
            img_url = tw_image.get("content", "").strip()
            if img_url and not any(p in img_url.lower() for p in PLACEHOLDER_PATTERNS):
                return _abs_url(link, img_url)
        
        # Priority 3: First substantial image in article/main content
        article = soup.find(["article", "main", "[role='main']"])
        if article:
            for img in article.find_all("img", limit=3):
                for attr in IMG_ATTRS:
                    val = img.get(attr, "")
                    if val:
                        if " " in val:
                            val = val.split()[0]
                        if val and not val.startswith("data:"):
                            if not any(p in val.lower() for p in PLACEHOLDER_PATTERNS):
                                abs_img = _abs_url(link, val)
                                if abs_img:
                                    return abs_img
        
        return ""
    except Exception:
        # Fail silently - network issues, blocked pages, etc.
        return ""


# ── Feature extraction ────────────────────────────────────────────────────────

def extract_card_features(tag: Tag) -> CardFeatures:
    text = tag.get_text(" ", strip=True)
    children = [c for c in tag.children if isinstance(c, Tag)]
    attr = _attr(tag)
    return CardFeatures(
        depth=_depth(tag),
        word_count=len(text.split()),
        direct_child_count=len(children),
        link_count=len(tag.find_all("a")),
        img_count=len(tag.find_all("img")),
        heading_count=sum(len(tag.find_all(h)) for h in HEADING_TAGS),
        has_date=1.0 if DATE_RE.search(text) or tag.find("time") else 0.0,
        has_time_tag=1.0 if tag.find("time") else 0.0,
        positive_signal=1.0 if POSITIVE_RE.search(attr) else 0.0,
        negative_signal=1.0 if NEGATIVE_RE.search(attr) else 0.0,
    )


# ── Candidate collection ──────────────────────────────────────────────────────

def _is_valid_card(tag: Tag) -> bool:
    if tag.name not in CARD_TAGS:
        return False
    if _has_boilerplate_ancestor(tag):
        return False
    
    # Exclude by class/id patterns
    attr = _attr(tag).lower()
    if any(x in attr for x in BOILERPLATE_CLASSES):
        return False
    
    # Skip very small cards (likely not articles)
    text = tag.get_text(" ", strip=True)
    if len(text.split()) < 8:
        return False
    
    # Must have at least one substantial anchor
    for a in tag.find_all("a", href=True):
        link_text = a.get_text(strip=True)
        if len(link_text.split()) >= 3:
            return True
    return False


def _collect_candidates(soup: BeautifulSoup):
    seen_ids = set()
    out = []
    for tag in soup.find_all(CARD_TAGS):
        tid = id(tag)
        if tid in seen_ids:
            continue
        seen_ids.add(tid)
        if _is_valid_card(tag):
            out.append(tag)
    return out


# ── Cluster scoring ───────────────────────────────────────────────────────────

def _score_cluster(members: list, size: int) -> float:
    if size < 2:
        return -999.0

    avg = lambda attr: np.mean([getattr(m, attr) for m in members])

    return (
        np.log1p(size) * 3.0
        + avg("heading_count") * 2.0
        + avg("img_count") * 1.5
        + avg("has_date") * 1.5
        + avg("has_time_tag") * 1.0
        + avg("positive_signal") * 1.5
        - avg("negative_signal") * 3.0
        - avg("link_count") * 0.1
    )


# ── JSON-LD structured data ───────────────────────────────────────────────────

def _jsonld_items(soup: BeautifulSoup, base_url: str):
    items = []
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        entries = data if isinstance(data, list) else data.get("itemListElement", [data])
        for entry in entries:
            if isinstance(entry, dict) and "item" in entry:
                entry = entry["item"]
            if not isinstance(entry, dict):
                continue
            t = entry.get("@type", "")
            if not any(x in t for x in ("NewsArticle", "Article", "BlogPosting")):
                continue
            title = entry.get("headline", entry.get("name", ""))
            link = _abs_url(base_url, entry.get("url", entry.get("@id", "")))
            img_f = entry.get("image", "")
            image = _abs_url(base_url, img_f if isinstance(img_f, str) else img_f.get("url", ""))
            published = entry.get("datePublished", entry.get("dateModified", ""))
            if title and link:
                items.append(NewsItem(title=title, link=link,
                                      image=image, published=published))
    return items


# ── Main entry point ──────────────────────────────────────────────────────────

def scrape_feed(url: str) -> FeedResult:
    t0 = time.time()
    result = FeedResult(url=url)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        result.error = f"Fetch error: {e}"
        result.extraction_ms = int((time.time() - t0) * 1000)
        return result

    soup = BeautifulSoup(html, "lxml")

    # JSON-LD pass (very reliable when present)
    jl_items = _jsonld_items(soup, url)

    # Prune noise
    for tag in soup(PRUNE_TAGS):
        tag.decompose()

    # Candidates
    candidates = _collect_candidates(soup)
    result.n_candidates = len(candidates)

    if len(candidates) < 3:
        if jl_items:
            result.items = jl_items
            result.extraction_ms = int((time.time() - t0) * 1000)
            return result
        result.error = f"Too few candidates ({len(candidates)}) to cluster"
        result.extraction_ms = int((time.time() - t0) * 1000)
        return result

    # Features
    feature_list = [extract_card_features(c) for c in candidates]
    X = np.array([list(asdict(f).values()) for f in feature_list], dtype=float)

    # DBSCAN on structural shape columns only
    structural_cols = [0, 1, 2, 3, 4, 5]
    X_struct = X[:, structural_cols]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_struct)

    labels = DBSCAN(eps=1.2, min_samples=2).fit_predict(X_scaled)
    unique_labels = set(labels) - {-1}

    if not unique_labels:
        labels = DBSCAN(eps=2.0, min_samples=2).fit_predict(X_scaled)
        unique_labels = set(labels) - {-1}

    result.n_clusters = len(unique_labels)

    cluster_members: dict = {}
    cluster_indices: dict = {}
    for i, (feat, lbl) in enumerate(zip(feature_list, labels)):
        if lbl == -1:
            continue
        cluster_members.setdefault(lbl, []).append(feat)
        cluster_indices.setdefault(lbl, []).append(i)

    if not cluster_members:
        cluster_members = {0: feature_list}
        cluster_indices = {0: list(range(len(candidates)))}

    cluster_scores = {
        lbl: _score_cluster(members, len(members))
        for lbl, members in cluster_members.items()
    }
    best_label = max(cluster_scores, key=lambda l: cluster_scores[l])
    best_indices = cluster_indices[best_label]
    result.winning_cluster_size = len(best_indices)

    # Extract fields per card
    seen_links: set = set()
    items = []

    for idx in best_indices:
        card = candidates[idx]
        title, link = _extract_title_and_link(card, url)
        
        if not title or not link:
            continue
        
        # Validate title-link association
        if not _is_title_link_valid(title, link):
            continue
        
        link_key = link.rstrip("/").lower()
        if link_key in seen_links:
            continue
        seen_links.add(link_key)
        
        if link.rstrip("/").lower() == url.rstrip("/").lower():
            continue

        # Try to fetch cover image from article page first (better quality)
        # Fall back to card image if fetch fails
        image = _fetch_cover_image(link)
        if not image:
            image = _best_img(card, url)
        
        published = _extract_date(card)
        items.append(NewsItem(title=title, link=link, image=image, published=published))

    # Merge JSON-LD metadata into DOM-scraped items
    if jl_items:
        jl_by_link = {i.link.rstrip("/").lower(): i for i in jl_items}
        for item in items:
            jl = jl_by_link.get(item.link.rstrip("/").lower())
            if jl:
                if not item.image and jl.image:
                    item.image = jl.image
                if not item.published and jl.published:
                    item.published = jl.published

    result.items = items
    result.extraction_ms = int((time.time() - t0) * 1000)
    return result


# ── Pretty printer ────────────────────────────────────────────────────────────

def print_result(r: FeedResult):
    W = 76
    print(f"\n{'═' * W}")
    print(f"  URL : {r.url}")
    if r.error:
        print(f"  ERR : {r.error}")
    else:
        print(f"  Items={len(r.items)}  Candidates={r.n_candidates}"
              f"  Clusters={r.n_clusters}  WinCluster={r.winning_cluster_size}"
              f"  {r.extraction_ms}ms")
    print(f"{'─' * W}")
    for i, item in enumerate(r.items, 1):
        print(f"\n  [{i:03d}] {item.title}")
        print(f"         Link : {item.link}")
        if item.image:
            print(f"         Image: {item.image}")
        if item.published:
            print(f"         Date : {item.published}")
    print(f"\n{'═' * W}\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

DEFAULT_URLS = [
    "https://www.bbc.com/news",
    "https://techcrunch.com",
    "https://www.reuters.com",
    "https://edition.cnn.com/",
    "https://edition.cnn.com/health",
    "https://www.aljazeera.com/"
    
]

if __name__ == "__main__":
    urls = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_URLS

    all_results = []
    for url in urls:
        print(f"\n⏳  Scraping feed: {url}")
        r = scrape_feed(url)
        print_result(r)
        all_results.append({
            "url": r.url,
            "error": r.error,
            "stats": {
                "items": len(r.items),
                "candidates": r.n_candidates,
                "clusters": r.n_clusters,
                "winning_cluster_size": r.winning_cluster_size,
                "extraction_ms": r.extraction_ms,
            },
            "items": [asdict(it) for it in r.items],
        })

    out_path = "feed_results.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"✅  Saved → {out_path}")