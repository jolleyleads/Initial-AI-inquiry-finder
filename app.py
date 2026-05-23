from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import re

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AI Inquiry Finder</title>
<style>
body{font-family:Arial;background:#0f172a;color:white;padding:30px}
input,button{padding:12px;border-radius:8px;border:none}
input{width:420px}
button{background:#38bdf8;font-weight:bold;cursor:pointer}
.card{background:#1e293b;padding:16px;margin:14px 0;border-radius:12px}
.score{color:#22c55e;font-weight:bold}
.error{background:#7f1d1d;padding:15px;border-radius:10px}
a{color:#38bdf8}
</style>
</head>
<body>
<h1>AI Inquiry Finder</h1>
<p>Search public web/classified-style inquiry keywords and rank leads.</p>

<form method="POST">
<input name="query" placeholder="example: content requests Virginia Beach" required>
<button>Search</button>
</form>

{% if error %}
<div class="error">{{error}}</div>
{% endif %}

{% if searched and not results %}
<p>No results found. Try broader words like: content, photos, videos, looking for, need, near me.</p>
{% endif %}

{% for r in results %}
<div class="card">
<h3>{{r.title}}</h3>
<p>{{r.snippet}}</p>
<p class="score">Lead Score: {{r.score}}/100</p>
<a href="{{r.link}}" target="_blank">Open Result</a>
</div>
{% endfor %}
</body>
</html>
"""

BUYER_WORDS = [
    "looking for", "need", "seeking", "want", "anyone know",
    "where can i", "recommend", "near me", "available",
    "photos", "videos", "content", "custom", "inquiry",
    "classified", "personal", "dating"
]

def score_result(text):
    t = text.lower()
    score = 20
    for word in BUYER_WORDS:
        if word in t:
            score += 10
    if "near me" in t:
        score += 15
    if len(t) > 120:
        score += 10
    return min(score, 100)

def clean_link(link):
    if not link:
        return "#"
    return link

def search_duckduckgo(query):
    urls = [
        "https://html.duckduckgo.com/html/?q=" + quote_plus(query),
        "https://duckduckgo.com/html/?q=" + quote_plus(query)
    ]

    results = []

    for url in urls:
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(res.text, "html.parser")

            blocks = soup.select(".result")
            if not blocks:
                blocks = soup.select("div")

            for block in blocks:
                a = block.select_one("a.result__a") or block.find("a")
                snippet = block.select_one(".result__snippet")

                if not a:
                    continue

                title = a.get_text(" ", strip=True)
                link = clean_link(a.get("href"))
                desc = snippet.get_text(" ", strip=True) if snippet else block.get_text(" ", strip=True)

                if not title or len(title) < 4:
                    continue

                combined = title + " " + desc

                results.append({
                    "title": title[:140],
                    "snippet": desc[:300],
                    "link": link,
                    "score": score_result(combined)
                })

            if results:
                break

        except Exception:
            continue

    seen = set()
    unique = []
    for r in results:
        key = r["title"].lower()
        if key not in seen:
            unique.append(r)
            seen.add(key)

    return sorted(unique, key=lambda x: x["score"], reverse=True)[:20]

@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    error = None
    searched = False

    if request.method == "POST":
        searched = True
        q = request.form.get("query", "").strip()

        if not q:
            error = "Type a search first."
        else:
            search_query = q + " public classified inquiry personal lead"
            results = search_duckduckgo(search_query)

            if not results:
                error = "Search ran, but the public search source returned no readable results."

    return render_template_string(
        HTML,
        results=results,
        error=error,
        searched=searched
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
