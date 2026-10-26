```python
LANGS = {
    "uz": " Javob tili: o'zbek.",
    "kr": " Javob tili: o'zbek (kirill).",
    "ru": " Язык ответа: русский.",
    "en": " Reply in English.",
    "tr": " Türkçe yanıt ver."
}

SYS = (
    "Sen PhishGuard kiberxavfsizlik, dasturlash va kompyuter tarmoqlari "
    "bo'yicha mutaxassis va yordamchisan. Qisqa, professional va aniq "
    "maslahat ber. Xavfsizlikka oid savollarda himoyaviy va qonuniy "
    "tavsiyalar ber."
)


def get_ai_client():
    """Gemini mijozini yaratadi."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not api_key:
        return None, "AI yoqilmagan: GEMINI_API_KEY o'rnatilmagan."

    try:
        from google import genai
        return genai.Client(api_key=api_key), None

    except ImportError:
        return None, (
            "google-genai kutubxonasi o'rnatilmagan. "
            "'pip install google-genai' buyrug'ini bajaring."
        )

    except Exception:
        return None, "Gemini mijozini ishga tushirib bo'lmadi. API kalitini tekshiring."


def generate_ai(contents, lang="uz", max_output_tokens=500):
    """Gemini AI orqali javob yaratadi."""
    client, error = get_ai_client()

    if error:
        return None, error

    try:
        from google.genai import types

        model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYS + LANGS.get(lang, LANGS["uz"]),
                max_output_tokens=max_output_tokens,
                temperature=0.4,
            ),
        )

        answer = (getattr(response, "text", None) or "").strip()

        if not answer:
            return None, "AI bo'sh javob qaytardi. Qayta urinib ko'ring."

        return answer, None

    except Exception:
        app.logger.exception("Gemini API so'rovida xatolik")
        return None, (
            "AI hozir javob bermadi. API kaliti, internet "
            "va model sozlamalarini tekshiring."
        )


@app.post("/api/ai")
def api_ai():
    """Phishing tahlili natijasini AI yordamida tushuntiradi."""
    j = request.get_json(silent=True) or {}

    if not isinstance(j, dict):
        return jsonify(error="So'rov formati noto'g'ri."), 400

    text_value = j.get("text", "")

    if not isinstance(text_value, str):
        text_value = str(text_value)

    text_value = text_value[:5000]
    result = j.get("result")

    msg = (
        "Tahlil natijasi: "
        + json.dumps(result, ensure_ascii=False)[:6000]
        + "\nMatn: "
        + text_value
        + "\nNatijani sodda tilda tushuntir va kerakli himoya choralarini ayt."
    )

    answer, error = generate_ai(
        msg,
        j.get("lang", "uz"),
        max_output_tokens=500
    )

    if error:
        status = (
            503
            if "o'rnatilmagan" in error or "GEMINI_API_KEY" in error
            else 502
        )
        return jsonify(error=error), status

    return jsonify(text=answer)


@app.post("/api/chat")
def api_chat():
    """PhishGuard AI yordamchisi bilan suhbat."""
    j = request.get_json(silent=True) or {}

    if not isinstance(j, dict):
        return jsonify(error="So'rov formati noto'g'ri."), 400

    incoming = j.get("messages") or []

    if not isinstance(incoming, list):
        return jsonify(error="Xabarlar ro'yxati noto'g'ri."), 400

    contents = []

    for m in incoming[-10:]:
        if not isinstance(m, dict):
            continue

        role = m.get("role")
        content = m.get("content")

        if role not in ("user", "assistant", "model"):
            continue

        if not isinstance(content, str):
            continue

        content = content.strip()[:1500]

        if not content:
            continue

        gemini_role = "user" if role == "user" else "model"

        # Ketma-ket bir xil roldagi xabarlarni birlashtirish.
        if contents and contents[-1]["role"] == gemini_role:
            contents[-1]["parts"][0]["text"] += "\n" + content
        else:
            contents.append({
                "role": gemini_role,
                "parts": [{"text": content}]
            })

    if not contents or contents[-1]["role"] != "user":
        return jsonify(
            error="Oxirgi xabar foydalanuvchidan bo'lishi kerak."
        ), 400

    answer, error = generate_ai(
        contents,
        j.get("lang", "uz"),
        max_output_tokens=700
    )

    if error:
        status = (
            503
            if "o'rnatilmagan" in error or "GEMINI_API_KEY" in error
            else 502
        )
        return jsonify(error=error), status

    return jsonify(text=answer)


@app.get("/health")
def health():
    return "ok"


@app.get("/")
def index():
    return Response(HTML, mimetype="text/html")


@app.get("/manifest.json")
def manifest():
    return Response(
        json.dumps({
            "name": "PhishGuard",
            "short_name": "PhishGuard",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#0b1020",
            "theme_color": "#0b1020"
        }),
        mimetype="application/manifest+json"
    )


@app.get("/icon.svg")
def icon():
    return Response(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<circle cx="50" cy="50" r="40" fill="#5eead4"/></svg>',
        mimetype="image/svg+xml"
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")
    )
```
