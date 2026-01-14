import asyncio
import aiohttp
from flask import Flask, jsonify

print("✅ Script started")  # ← تأكيد تشغيل الملف

API_BASE = "https://ff-jwt-theta.vercel.app/token"
INPUT_FILE = "acc.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

CONCURRENT = 8
RETRIES = 3

app = Flask(__name__)


async def fetch_token(session, acc, i, total, sem, tokens):
    uid = acc.get("uid")
    password = acc.get("password")

    if not uid or not password:
        return

    async with sem:
        for attempt in range(1, RETRIES + 1):
            try:
                async with session.get(
                    API_BASE,
                    params={"uid": uid, "password": password},
                    headers=HEADERS,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as r:

                    if r.status != 200:
                        await asyncio.sleep(0.5)
                        continue

                    data = await r.json()
                    token = data.get("token") or data.get("jwt")

                    if token:
                        tokens.append({"uid": uid, "token": token})
                        print(f"[✔] {i}/{total} Token OK")
                    return

            except Exception as e:
                await asyncio.sleep(0.5)


async def main():
    print("▶ Reading acc.json")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    tokens = []
    sem = asyncio.Semaphore(CONCURRENT)

    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_token(session, acc, i + 1, len(accounts), sem, tokens)
            for i, acc in enumerate(accounts)
        ]
        await asyncio.gather(*tasks)

    return tokens


@app.route("/generate", methods=["POST"])
def generate():
    print("🔥 REQUEST RECEIVED")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tokens = loop.run_until_complete(main())
    loop.close()

    return jsonify({
        "count": len(tokens),
        "tokens": tokens
    })


if __name__ == "__main__":
    print("🚀 Flask starting...")
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False   # ← مهم جدًا
    )

