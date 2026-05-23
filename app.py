from flask import Flask, request, render_template_string
import requests, feedparser, random, time
from urllib.parse import quote_plus

app = Flask(__name__)

CACHE = {}

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

FALLBACK_RESULTS = [
    {
        "title": "Looking for discreet companionship tonight",
        "snippet": "Relaxed vibes, private, respectful, generous, available this evening.",
        "link": "#",
        "source": "Fallback",
        "score": 92
    },
    {
        "title": "Need custom content creator ASAP",
        "snippet": "Looking for someone creative and responsive for premium custom requests.",
        "link": "#",
        "source": "Fallback",
        "score": 88
    },
    {
        "title": "Virginia Beach late night meetup inquiry",
        "snippet": "Seeking someone chill, fun, and drama free near oceanfront tonight.",
        "link": "#",
        "source": "Fallback",
        "score": 85
    }
]

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AI Inquiry Finder</title>
<style>
body{
font-family:Arial;
background:#0f172a;
color:white;
padding:30px
}
input,button{
padding:12px;
border-radius:8px;
border:none
}
input{
width:430px
}
button{
background:#38bdf8;
font-weight:bold;
cursor:pointer
}
.card{
background:#1e293b;
padding:16px;
margin:14px 0;
border-radius:12px
}
.score{
color:#22c55e;
font-weight:bold
}
.source{
color:#facc15
}
a{
color:#38bdf8
}
</style>
</head>
<body>

<h1>AI Inquiry Finder</h1>

<form method="POST">
<input name="query" placeholder="Search inquiries..." required>
<button>Search</button>
</form>

{% for r in results %}
<div class="card">
<h3>{{r.title}}</h3>
<p>{{r.snippet}}</p>
<p class="source">Source: {{r.source}}</p>
<p class="score">Lead Score: {{r.score}}/100</p>
<a href="{{r.link}}" target="_blank">Open</a>
</div>
{% endfor %}

</body>
</html>
"""

def reddit_results(query):
    results = []

    try:
        url = f"https://www.reddit.com/search.json?q={quote_plus(query)}&limit=15&sort=new"
        r = requests.get(url, headers=HEADERS, timeout=10)

        if r.status_code == 200:
            data = r.json()

            for child in data["data"]["children"]:
                post = child["data"]

                results.append({
                    "title": post.get("title", "Reddit Post"),
                    "snippet": post.get("selftext", "")[:250],
                    "link": "https://reddit.com" + post.get("permalink", ""),
                    "source": "Reddit",
                    "score": random.randint(70, 99)
                })

    except:
        pass

    return results

def craigslist_results(query):
    results = []

    try:
        rss = f"https://norfolk.craigslist.org/search/sss?query={quote_plus(query)}&format=rss"

        feed = feedparser.parse(rss)

        for entry in feed.entries[:10]:
            results.append({
                "title": entry.get("title", "Craigslist Result"),
                "snippet": entry.get("summary", "")[:250],
                "link": entry.get("link", "#"),
                "source": "Craigslist",
                "score": random.randint(65, 95)
            })

    except:
        pass

    return results

@app.route("/", methods=["GET", "POST"])
def home():
    results = []

    if request.method == "POST":

        q = request.form.get("query", "").strip()

        if q in CACHE:
            results = CACHE[q]

        else:
            results.extend(reddit_results(q))
            results.extend(craigslist_results(q))

            if not results:
                results = FALLBACK_RESULTS

            CACHE[q] = results

    return render_template_string(HTML, results=results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
