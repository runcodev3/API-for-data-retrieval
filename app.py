from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import time

app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def ai_process(text):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    models = [
        "openrouter/free",
        "mistralai/mistral-7b-instruct:free",
        "meta-llama/llama-3-8b-instruct:free"
    ]

    for model in models:
        for attempt in range(2):
            try:
                data = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "สรุปและเรียบเรียงข้อความภาษาไทยให้เข้าใจง่าย"
                        },
                        {
                            "role": "user",
                            "content": f"""
สรุปและเรียบเรียงใหม่

ตอบตามนี้เท่านั้น:

SUMMARY:
(สรุปสั้น กระชับ)

CONTENT:
(เนื้อหาครบเหมือนเดิม แต่เรียบเรียงให้อ่านง่าย)

ข้อความ:
{text[:1500]}
"""
                        }
                    ]
                }

                res = requests.post(url, headers=headers, json=data, timeout=90)

                if res.status_code != 200:
                    print("MODEL FAIL:", model, res.status_code)
                    time.sleep(2)
                    continue

                result = res.json()
                content = result["choices"][0]["message"]["content"]

                if "SUMMARY:" in content and "CONTENT:" in content:
                    summary = content.split("SUMMARY:")[1].split("CONTENT:")[0].strip()
                    rewritten = content.split("CONTENT:")[1].strip()
                    print("SUCCESS:", model)
                    return summary, rewritten

            except Exception as e:
                print("ERROR:", model, e)
                time.sleep(2)

    return None, None


def extract_all(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
    except:
        return {"error": "FETCH_ERROR"}

    data = {}

    data["title"] = soup.title.string if soup.title else "No Title"

    content = []
    for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        text = tag.get_text(strip=True)
        if text:
            content.append(text)

    full_text = " ".join(content)

    summary, rewritten = ai_process(full_text)

    if summary is None:
        return {"error": "AI_ERROR"}

    data["summary"] = summary
    data["full_text"] = rewritten

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
    error = None

    if request.method == "POST":
        url = request.form["url"]
        result = extract_all(url)

        if "error" in result:
            if result["error"] == "AI_ERROR":
                error = "⚠️ AI กำลังถูกใช้งานเยอะ กรุณาลองใหม่"
            else:
                error = "❌ ไม่สามารถดึงข้อมูลเว็บได้"
            result = None

    return render_template("index.html", result=result, error=error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
