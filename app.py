from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from newspaper import Article
import os

app = Flask(__name__)

def extract_all(url):
    data = {}

    try:
        # 🔥 วิธี 1: Newspaper (ฉลาด)
        article = Article(url)
        article.download()
        article.parse()

        data["title"] = article.title
        data["text"] = article.text
        data["images"] = list(article.images)

    except:
        data["title"] = ""
        data["text"] = ""
        data["images"] = []

    try:
        # 🔥 วิธี 2: BeautifulSoup (เก็บเพิ่ม)
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        if not data["title"]:
            data["title"] = soup.title.string if soup.title else "No Title"

        # ดึงข้อความทั้งหมด
        paragraphs = [p.get_text() for p in soup.find_all("p")]
        data["text_full"] = " ".join(paragraphs)

        # ดึงรูป
        imgs = [img.get("src") for img in soup.find_all("img")]
        data["images"] += imgs

        # ดึงลิงก์
        links = [a.get("href") for a in soup.find_all("a")]
        data["links"] = links[:50]

        # meta
        meta = {}
        for tag in soup.find_all("meta"):
            if tag.get("name") and tag.get("content"):
                meta[tag.get("name")] = tag.get("content")
        data["meta"] = meta

    except:
        data["text_full"] = ""
        data["links"] = []
        data["meta"] = {}

    # 🔥 รวมข้อความ
    full_text = data.get("text") + " " + data.get("text_full")

    # 🔥 เรียบเรียง (ง่ายๆ)
    sentences = full_text.split(".")
    summary = ". ".join(sentences[:5])

    data["summary"] = summary
    data["full_text"] = full_text

    # ตัดรูปซ้ำ
    data["images"] = list(set(data["images"]))[:10]

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
