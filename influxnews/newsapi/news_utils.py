import requests
import os
from .models import News, Author
import environ
from bs4 import BeautifulSoup
import re
import json
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from dataclasses import dataclass, asdict

env = environ.Env()
environ.Env.read_env()


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
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

PLACEHOLDER_PATTERNS = {
    "grey-placeholder", "placeholder", "grey.png", 
    "default.png", "no-image", "loading", "transparent.gif"
}

IMG_ATTRS = ["src", "data-src", "data-lazy-src", "data-original",
             "data-srcset", "srcset", "data-img"]

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


#authors
bbc_news = Author.objects.get(name='BBC News')
tech_crunch = Author.objects.get(name='TechCrunch')
bbc_sport = Author.objects.get(name='BBC Sport')


# ── Helper functions ─────────────────────────────────────────────────────────

def _attr(tag) -> str:
    return " ".join(tag.get("class", [])) + " " + tag.get("id", "")


def _depth(tag) -> int:
    d = 0
    p = tag.parent
    while p and p.name not in (None, "[document]", "html", "body"):
        d += 1
        p = p.parent
    return d


def _has_boilerplate_ancestor(tag) -> bool:
    for ancestor in tag.parents:
        if isinstance(ancestor, BeautifulSoup.element.Tag) and ancestor.name in BOILERPLATE_ANCESTORS:
            return True
    return False


def _abs_url(base: str, href: str) -> str:
    if not href:
        return ""
    href = href.strip()
    if href.startswith(("http://", "https://")):
        return href
    if href.startswith("//"):
        import urllib.parse
        scheme = urllib.parse.urlparse(base).scheme
        return f"{scheme}:{href}"
    import urllib.parse
    return urllib.parse.urljoin(base, href)


def _best_img(tag, base_url: str) -> str:
    for img in tag.find_all("img"):
        for attr in IMG_ATTRS:
            val = img.get(attr, "")
            if val:
                if " " in val:
                    val = val.split()[0]
                if val and not val.startswith("data:"):
                    val_lower = val.lower()
                    if any(p in val_lower for p in PLACEHOLDER_PATTERNS):
                        continue
                    return _abs_url(base_url, val)
    return ""


def _extract_date(tag) -> str:
    time_el = tag.find("time")
    if time_el:
        dt = time_el.get("datetime", "").strip()
        if dt and _is_valid_date(dt):
            return dt
        txt = time_el.get_text(strip=True)
        if txt and len(txt) < 100 and _is_valid_date(txt):
            return txt

    for el in tag.find_all(True):
        attr = _attr(el).lower()
        if re.search(r"date|time|timestamp|publish", attr):
            txt = el.get_text(strip=True)
            if txt and len(txt) < 80 and _is_valid_date(txt):
                return txt

    text = tag.get_text(" ", strip=True)
    m = DATE_RE.search(text)
    if m:
        date_str = m.group(0).strip()
        if len(date_str) < 100:
            return date_str

    return ""


def _is_valid_date(text: str) -> bool:
    if not text or len(text) > 100:
        return False
    if any(x in text.lower() for x in {"select", "category", "sign up", "try", "read more"}):
        return False
    return bool(DATE_RE.search(text))


def _extract_title_and_link(tag, base_url: str):
    for h in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        headings = tag.find_all(h)
        if headings:
            best = max(headings, key=lambda el: len(el.get_text(strip=True)))
            title = best.get_text(strip=True)
            if not title or len(title.split()) < 3:
                continue
            
            link = ""
            for ancestor in [best] + list(best.parents):
                if isinstance(ancestor, BeautifulSoup.element.Tag) and ancestor.name == "a" and ancestor.get("href"):
                    link = _abs_url(base_url, ancestor.get("href"))
                    break
            
            if link and not _is_navigation_link(link, base_url):
                return title, link

    anchors = tag.find_all("a", href=True)
    best_anchor, best_len = None, 0
    
    for a in anchors:
        txt = a.get_text(strip=True)
        txt_words = txt.split()
        
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
    url_lower = url.lower()
    base_lower = base_url.lower().rstrip("/")
    
    nav_patterns = {"/category/", "/archive/", "/tag/", "/author/", 
                    "/page/", "/search", "category=", "tag=", 
                    "#", "javascript:", "mailto:"}
    
    if any(p in url_lower for p in nav_patterns):
        return True
    
    if url_lower.rstrip("/") == base_lower:
        return True
    
    return False


def _is_title_link_valid(title: str, link: str) -> bool:
    title_lower = title.lower()
    link_lower = link.lower()
    
    bad_titles = {"by ", "author ", "next", "prev", "more", "latest news", 
                  "popular", "upcoming events", "category", "tag"}
    
    if any(t in title_lower for t in bad_titles):
        if title_lower not in bad_titles:
            pass
        else:
            return False
    
    if "/category/" in link_lower and "category" not in title_lower:
        return False
    
    return True


# ── Feature extraction ───────────────────────────────────────────────────────

def extract_card_features(tag) -> CardFeatures:
    text = tag.get_text(" ", strip=True)
    children = [c for c in tag.children if isinstance(c, BeautifulSoup.element.Tag)]
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


# ── Candidate collection ─────────────────────────────────────────────────────

def _is_valid_card(tag) -> bool:
    if tag.name not in CARD_TAGS:
        return False
    if _has_boilerplate_ancestor(tag):
        return False
    
    attr = _attr(tag).lower()
    if any(x in attr for x in BOILERPLATE_CLASSES):
        return False
    
    text = tag.get_text(" ", strip=True)
    if len(text.split()) < 8:
        return False
    
    for a in tag.find_all("a", href=True):
        link_text = a.get_text(strip=True)
        if len(link_text.split()) >= 3:
            return True
    return False


def _collect_candidates(soup):
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


# ── Cluster scoring ──────────────────────────────────────────────────────────

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


# ── JSON-LD structured data ──────────────────────────────────────────────────

def _jsonld_items(soup, base_url: str):
    """Extract NewsArticle items from JSON-LD structured data"""
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
                items.append({
                    "title": title,
                    "link": link,
                    "image": image,
                    "published": published
                })
    return items


def _fetch_cover_image(link: str) -> str:
    """
    Fetch article page and extract cover image from og:image or article content
    """
    try:
        resp = requests.get(link, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        
        # Priority 1: og:image meta tag
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            img_url = og_image.get("content", "").strip()
            if img_url and not any(p in img_url.lower() for p in PLACEHOLDER_PATTERNS):
                return _abs_url(link, img_url)
        
        # Priority 2: twitter:image
        tw_image = soup.find("meta", {"name": "twitter:image"})
        if tw_image and tw_image.get("content"):
            img_url = tw_image.get("content", "").strip()
            if img_url and not any(p in img_url.lower() for p in PLACEHOLDER_PATTERNS):
                return _abs_url(link, img_url)
        
        # Priority 3: First substantial image in article
        article = soup.find(["article", "main"])
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
        return ""



def scrape_news_feed(url: str, author: Author, category: str = "general", 
                     country: str = "worldwide", language: str = "en"):
    """
    Generic news scraper using DBSCAN clustering (matches tests.py exactly).
    Extracts news items from any URL and saves to the News model.
    
    Args:
        url: News feed URL to scrape
        author: Author object to associate with the news
        category: Category for the news items
        country: Country code
        language: Language code
    
    Returns:
        List of created News objects
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(html, "lxml")

    # Extract JSON-LD items (very reliable when present)
    jl_items = _jsonld_items(soup, url)

    # Prune noise
    for tag in soup(PRUNE_TAGS):
        tag.decompose()

    # Collect candidates
    candidates = _collect_candidates(soup)
    
    if len(candidates) < 3:
        if jl_items:
            # Fall back to JSON-LD if too few DOM candidates
            items_to_save = jl_items
        else:
            print(f"Too few candidates ({len(candidates)}) found")
            return []
    else:
        # Extract features
        feature_list = [extract_card_features(c) for c in candidates]
        X = np.array([list(asdict(f).values()) for f in feature_list], dtype=float)

        # DBSCAN clustering
        structural_cols = [0, 1, 2, 3, 4, 5]
        X_struct = X[:, structural_cols]
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_struct)

        labels = DBSCAN(eps=1.2, min_samples=2).fit_predict(X_scaled)
        unique_labels = set(labels) - {-1}

        if not unique_labels:
            labels = DBSCAN(eps=2.0, min_samples=2).fit_predict(X_scaled)
            unique_labels = set(labels) - {-1}

        # Build clusters
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

        # Select best cluster
        cluster_scores = {
            lbl: _score_cluster(members, len(members))
            for lbl, members in cluster_members.items()
        }
        best_label = max(cluster_scores, key=lambda l: cluster_scores[l])
        best_indices = cluster_indices[best_label]

        # Extract fields from cards
        seen_links: set = set()
        items_to_save = []

        for idx in best_indices:
            card = candidates[idx]
            title, link = _extract_title_and_link(card, url)
            
            if not title or not link:
                continue
            
            if not _is_title_link_valid(title, link):
                continue
            
            link_key = link.rstrip("/").lower()
            if link_key in seen_links:
                continue
            seen_links.add(link_key)
            
            if link.rstrip("/").lower() == url.rstrip("/").lower():
                continue

            # Try to fetch cover image from article page first
            image = _fetch_cover_image(link)
            if not image:
                image = _best_img(card, url)
            
            published = _extract_date(card)
            
            items_to_save.append({
                "title": title,
                "link": link,
                "image": image,
                "published": published
            })

        # Merge JSON-LD metadata into DOM-scraped items
        if jl_items:
            jl_by_link = {i["link"].rstrip("/").lower(): i for i in jl_items}
            for item in items_to_save:
                jl = jl_by_link.get(item["link"].rstrip("/").lower())
                if jl:
                    if not item["image"] and jl["image"]:
                        item["image"] = jl["image"]
                    if not item["published"] and jl["published"]:
                        item["published"] = jl["published"]

    # Save items to database
    created_news = []
    for item in items_to_save:
        try:
            description = re.sub(r"\s+", " ", item.get("title", ""))[:500]
            
            news_obj, created = News.objects.get_or_create(
                title=item["title"],
                url=item["link"],
                defaults={
                    "description": description,
                    "image": item["image"],
                    "category": category,
                    "country": country,
                    "language": language,
                    "publishedAt": item["published"] if item["published"] else None,
                    "author": author
                }
            )
            if created:
                created_news.append(news_obj)
                print(f"✓ Created: {item['title'][:60]}...")
        except Exception as e:
            print(f"Error saving news: {e}")
            continue

    print(f"Scraped {len(created_news)} new articles from {url}")
    return created_news


def getBBCHeadlines():
    """Scrape BBC News homepage using DBSCAN algorithm"""
    return scrape_news_feed(
        url="https://www.bbc.com/news",
        author=bbc_news,
        category="general",
        country="uk",
        language="en"
    )


def getBBCSportsHeadLines():
    """Scrape BBC Sports headlines using DBSCAN algorithm"""
    return scrape_news_feed(
        url="https://www.bbc.com/sport/football",
        author=bbc_sport,
        category="football",
        country="uk",
        language="en"
    )


def getTechCrunchHeadlines():
    """Scrape TechCrunch articles using DBSCAN algorithm"""
    all_articles = []
    categories = ['artificial-intelligence', 'fintech', 'startups', 'security', 
                  'cryptocurrency', 'apps', 'media-entertainment', 'hardware']
    
    for cat in categories:
        articles = scrape_news_feed(
            url=f"https://techcrunch.com/category/{cat}/",
            author=tech_crunch,
            category=cat,
            country="worldwide",
            language="en"
        )
        all_articles.extend(articles)
    
    return all_articles