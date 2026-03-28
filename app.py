from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

app = Flask(__name__)

def extract_all(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")

    data = {}

    # ✅ title
    data["title"] = soup.title.string if soup.title else "No Title"

    # ✅ เนื้อหา (paragraph)
    paragraphs = [p.get_text() for p in soup.find_all("p")]
    full_text = " ".join(paragraphs)
    data["full_text"] = full_text

    # ✅ summary (เอา 5 ประโยคแรก)
    sentences = full_text.split(".")
    data["summary"] = ". ".join(sentences[:5])

    # ✅ 🔥 รูป (แก้สำคัญ: urljoin)
    images = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            full_url = urljoin(url, src)
            images.append(full_url)

    data["images"] = list(set(images))[:15]

    # ✅ 🔥 ลิงก์ + ชื่อ (แก้สำคัญ)
    links = []
    for a in soup.find_all("a"):
        href = a.get("href")
        text = a.get_text(strip=True)

        if href and text:
            full_url = urljoin(url, href)

            # กันลิงก์ขยะ
            if len(text) > 1 and not text.startswith("["):
                links.append({
                    "text": text,
                    "url": full_url
                })

    data["links"] = links[:50]

    return data


@app.route("/", methods=["GET", "POST"])
def index():
    result = None

    if request.method == "POST":
        url = request.form["url"]
        result = extract_all(url)

    return render_template("index.html", result=result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
