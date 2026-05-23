from flask import Flask, request, render_template_string
import requests, feedparser, re
from urllib.parse import quote_plus

app = Flask(__name__)

HEADERS = {"User-Agent": "AIInquiryFinder/1.0 by jolleyleads"}

KEYWORDS = [
    "looking for", "need", "seeking", "wanted", "recommend",
    "hire", "available", "content", "photos", "videos",
    "custom", "personal", "classified", "near me", "dm"
]

CRAIGSLIST_CITIES = [
    "norfolk", "richmond", "washingtondc", "raleigh", "charlotte",
    "newyork", "philadelphia", "atlanta", "miami", "dallas",
    "houston", "chicago", "losangeles"
]

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AI Inquiry Finder</title>
<style>
body{font-family:Arial;background:#0f172a;color:white;padding:30px}
input,button{padding:12px;border-radius:8px;border:none}
input{width:430px}
button{background:#38bdf8;font-weight:bold;cursor:pointer}
.card{background:#1e293b;padding:16px;margin:14px 0;border-radius:12px}
.score{color:#22c55e;font-weight:bold}
.source{color:#facc15}
.error{background:#7f1d1d;padding:15px;border-radius:10px}
a{color:#38bdf8}
</style>
</head>
<body>
<h1>AI Inquiry Finder</h1>
<p>Finds public classified-style and public discussion inquiries.</p>

<form method="POST">
<input name="query" placeholder="example: content requests Virginia Beach" required>
<button>Search</button>
</form>

{% if error %}
<div class="error">{{error}}</div>
{% endif %}

{% for r in results %}
<div class="card">
<h3>{{r.title}}</h3>
<p>{{r.snippet}}</p>
<p class="source">Source: {{r.source}}</p>
<p class="score">Lead Score: {{r.score}}/100</p>
<a href="{{r.link}}" target="_blank">Open Result</a>
</div>
{% endfor %}
</body>
</html>
"""

def score_text(text):
    t = text.lower()
    score = 25
    for kw in KEYWORDS:
        if kw in t:
            score += 10
    if len(t) > 100:
        score += 10
    return min(score, 100)

def clean_html(text):
    return re.sub("<.*?>", "", text or "").strip()

def search_craigslist(query):
    results = []
    for city in CRAIGSLIST_CITIES:
        url = f"https://{city}.craigslist.org/search/sss?query={quote_plus(query)}&format=rss"
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                title = clean_html(entry.get("title", "Craigslist result"))
                snippet = clean_html(entry.get("summary", title))
                link = entry.get("link", url)

                results.append({
                    "title": title,
                    "snippet": snippet[:350],
                    "link": link,
                    "source": f"Craigslist - {city}",
                    "score": score_text(title + " " + snippet)
                })
        except Exception:
            pass
    return results

def search_reddit(query):
    results = []
    url = f"https://www.reddit.com/search.json?q={quote_plus(query)}&sort=new&limit=25"

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        data = r.json()

        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            title = post.get("title", "")
            snippet = post.get("selftext", "") or post.get("subreddit_name_prefixed", "")
            permalink = "https://reddit.com" + post.get("permalink", "")

            if title:
                results.append({
                    "title": title,
                    "snippet": snippet[:350],
                    "link": permalink,
                    "source": "Reddit public search",
                    "score": score_text(title + " " + snippet)
                })
    except Exception:
        pass

    return results

def get_results(query):
    results = []
    results.extend(search_craigslist(query))
    results.extend(search_reddit(query))

    seen = set()
    unique = []

    for r in results:
        key = r["link"]
        if key not in seen:
            unique.append(r)
            seen.add(key)

    return sorted(unique, key=lambda x: x["score"], reverse=True)[:40]

@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    error = None

    if request.method == "POST":
        q = request.form.get("query", "").strip()

        if not q:
            error = "Type a search first."
        else:
            results = get_results(q)

            if not results:
                error = "No public results found. Try broader terms like: content, photos, videos, looking for, need, wanted, custom."

    return render_template_string(HTML, results=results, error=error)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
