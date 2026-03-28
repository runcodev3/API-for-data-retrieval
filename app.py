from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def ai_process(text):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    models = [
        "mistralai/mistral-7b-instruct:free",
        "openchat/openchat-7b:free",
        "meta-llama/llama-3-8b-instruct:free"
    ]

    for model in models:
        try:
            data = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "คุณเป็น AI ที่เก่งในการสรุปและเรียบเรียงข้อความภาษาไทย"
                    },
                    {
                        "role": "user",
                        "content": f"""
                        กรุณาทำ 2 อย่าง:
                        1. สรุปเนื้อหาให้สั้น เข้าใจง่าย
                        2. เรียบเรียงเนื้อหาใหม่ให้อ่านง่าย แต่ความหมายเดิม

                        ข้อความ:
                        {text[:4000]}
                        """
                    }
                ]
            }

            res = requests.post(url, headers=headers, json=data, timeout=30)
            result = res.json()

            content = result["choices"][0]["message"]["content"]

            parts = content.split("2.")
            summary = parts[0]
            rewritten = parts[1] if len(parts) > 1 else content

            return summary.strip(), rewritten.strip()

        except:
            continue

    return "สรุปไม่ได้", text

def extract_all(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")

    data = {}

    data["title"] = soup.title.string if soup.title else "No Title"

    content = []
    for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        text = tag.get_text(strip=True)
        if text:
            content.append(text)

    full_text = " ".join(content)

    summary, rewritten = ai_process(full_text)

    data["summary"] = summary
    data["full_text"] = rewritten

    # รูป
    images = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            images.append(urljoin(url, src))

    data["images"] = list(set(images))[:20]

    links = []
    for a in soup.find_all("a"):
        href = a.get("href")
        text = a.get_text(strip=True)

        if href and text and len(text) > 1:
            links.append({
                "text": text,
                "url": urljoin(url, href)
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
