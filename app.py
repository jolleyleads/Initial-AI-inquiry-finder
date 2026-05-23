from flask import Flask, request, render_template_string
import requests, re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

app = Flask(__name__)

KEYWORDS = [
    "looking for", "need", "seeking", "recommend", "anyone know",
    "hire", "available", "near me", "tonight", "booking",
    "content", "photos", "videos", "spicy", "dating", "personal"
]

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AI Inquiry Finder</title>
<style>
body{font-family:Arial;background:#0f172a;color:white;padding:30px}
input,button{padding:12px;border-radius:8px;border:none}
input{width:360px}
button{background:#38bdf8;font-weight:bold}
.card{background:#1e293b;padding:15px;margin:12px 0;border-radius:12px}
.score{color:#22c55e;font-weight:bold}
a{color:#38bdf8}
</style>
</head>
<body>
<h1>AI Inquiry Finder</h1>
<p>Finds public search inquiries from classified-style/personals-style keywords.</p>

<form method="POST">
<input name="query" placeholder="example: spicy content Virginia Beach" required>
<button>Search</button>
</form>

{% for r in results %}
<div class="card">
<h3>{{r.title}}</h3>
<p>{{r.snippet}}</p>
<p class="score">AI Lead Score: {{r.score}}/100</p>
<a href="{{r.link}}" target="_blank">Open Result</a>
</div>
{% endfor %}
</body>
</html>
"""

def score_text(text):
    text = text.lower()
    score = 0
    for kw in KEYWORDS:
        if kw in text:
            score += 12
    if len(text) > 80:
        score += 10
    return min(score, 100)

def search_public_web(query):
    url = "https://duckduckgo.com/html/?q=" + quote_plus(query)
    headers = {"User-Agent": "Mozilla/5.0"}
    page = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(page.text, "html.parser")

    results = []
    for item in soup.select(".result")[:10]:
        title_tag = item.select_one(".result__title")
        link_tag = item.select_one(".result__a")
        snippet_tag = item.select_one(".result__snippet")

        if not title_tag or not link_tag:
            continue

        title = title_tag.get_text(" ", strip=True)
        link = link_tag.get("href")
        snippet = snippet_tag.get_text(" ", strip=True) if snippet_tag else ""

        combined = title + " " + snippet
        results.append({
            "title": title,
            "link": link,
            "snippet": snippet,
            "score": score_text(combined)
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)

@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    if request.method == "POST":
        query = request.form.get("query", "")
        safe_query = query + " public inquiry classified personal"
        results = search_public_web(safe_query)
    return render_template_string(HTML, results=results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
