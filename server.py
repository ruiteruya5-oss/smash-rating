import os
import sys
import json
import socket
import random
import math
import requests
from flask import Flask, jsonify, request, render_template

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "players.json")

# GitHub Gist 永続化用設定（クラウドデプロイ用）
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GIST_ID = os.environ.get("GIST_ID", "")

# =====================
# レート計算パラメータ
# =====================
K = 80
alpha = 0.5
beta = 1
cap = 80
MAX_RATING_DIFF = 350

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"), static_folder=os.path.join(BASE_DIR, "static"))

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def load_data():
    # 1. Gist設定がある場合はGistから読み込み
    if GITHUB_TOKEN and GIST_ID:
        try:
            url = f"https://api.github.com/gists/{GIST_ID}"
            headers = {
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json"
            }
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                gist_data = res.json()
                files = gist_data.get("files", {})
                if "players.json" in files:
                    content = files["players.json"].get("content", "")
                    return json.loads(content)
        except Exception as e:
            print(f"[Warn] Failed to load from Gist, falling back to local file: {e}", file=sys.stderr)

    # 2. ローカルファイルから読み込み
    if not os.path.exists(DATA_FILE):
        return {"players": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    # 1. ローカルファイルに保存
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    # 2. Gist設定がある場合はGistにも保存（クラウド永続化）
    if GITHUB_TOKEN and GIST_ID:
        try:
            url = f"https://api.github.com/gists/{GIST_ID}"
            headers = {
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json"
            }
            body = {
                "files": {
                    "players.json": {
                        "content": json.dumps(data, ensure_ascii=False, indent=4)
                    }
                }
            }
            requests.patch(url, headers=headers, json=body, timeout=5)
        except Exception as e:
            print(f"[Warn] Failed to save to Gist: {e}", file=sys.stderr)

def S(d):
    return 0.5 + alpha * (d / 3) ** beta

def calc_change(p1_rating, p1_count, p2_rating, p2_count, d):
    Elo = 1 / (1 + 10 ** ((p2_rating - p1_rating) / 400))
    K_A = K * max(1, 2 - 0.05 * p1_count)
    K_B = K * max(1, 2 - 0.05 * p2_count)
    s_val = S(d)
    if d > 0:
        da = min(cap, max(1, round(K_A * (s_val - Elo)))) if d == 3 else min(cap, round(K_A * (s_val - Elo)))
        db = max(-cap, min(-1, round(K_B * (Elo - s_val)))) if d == 3 else max(-cap, round(K_B * (Elo - s_val)))
    else:
        da = max(-cap, min(-1, round(K_A * (s_val - Elo)))) if d == -3 else max(-cap, round(K_A * (s_val - Elo)))
        db = min(cap, max(1, round(K_B * (Elo - s_val)))) if d == -3 else min(cap, round(K_B * (Elo - s_val)))
    return int(da), int(db)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/players", methods=["GET"])
def get_players():
    data = load_data()
    players = data.get("players", [])
    classA = [p for p in players if 1 <= p.get("id", 0) <= 86 and p.get("name") != "-"]
    classB = [p for p in players if 87 <= p.get("id", 0) <= 172 and p.get("name") != "-"]
    return jsonify({
        "all": players,
        "classA": classA,
        "classB": classB
    })

@app.route("/api/random-pair", methods=["GET"])
def random_pair():
    data = load_data()
    players = data.get("players", [])
    classA = [p for p in players if 1 <= p.get("id", 0) <= 86 and p.get("name") != "-"]
    classB = [p for p in players if 87 <= p.get("id", 0) <= 172 and p.get("name") != "-"]

    def get_candidates(player_list):
        low_count = [p for p in player_list if p.get("count", 0) < 10]
        return low_count if low_count else player_list

    def weight(p):
        return 1 / (1 + p.get("count", 0))

    candA = get_candidates(classA)
    candB = get_candidates(classB)

    valid_pairs = []
    for p1 in candA:
        for p2 in candB:
            if abs(p1.get("rating", 1500) - p2.get("rating", 1500)) <= MAX_RATING_DIFF:
                w = weight(p1) * weight(p2)
                valid_pairs.append((p1, p2, w))

    if not valid_pairs:
        return jsonify({"error": f"レート差{MAX_RATING_DIFF}以内でマッチ可能なペアがいません"}), 404

    pairs = [(p1, p2) for p1, p2, w in valid_pairs]
    weights = [w for p1, p2, w in valid_pairs]
    p1, p2 = random.choices(pairs, weights=weights)[0]

    return jsonify({"p1": p1, "p2": p2})

@app.route("/api/battle", methods=["POST"])
def post_battle():
    req = request.get_json()
    if not req:
        return jsonify({"error": "Invalid request"}), 400

    p1_id = req.get("p1_id")
    p2_id = req.get("p2_id")
    result = req.get("result")

    if p1_id is None or p2_id is None or result not in [3, 2, 1, -1, -2, -3]:
        return jsonify({"error": "Invalid parameters"}), 400

    data = load_data()
    players = data.get("players", [])

    p1 = next((p for p in players if p.get("id") == p1_id), None)
    p2 = next((p for p in players if p.get("id") == p2_id), None)

    if not p1 or not p2:
        return jsonify({"error": "Player not found"}), 404

    old_r1 = p1.get("rating", 1500)
    old_r2 = p2.get("rating", 1500)
    c1 = p1.get("count", 0)
    c2 = p2.get("count", 0)

    da, db = calc_change(old_r1, c1, old_r2, c2, result)

    p1["rating"] = old_r1 + da
    p2["rating"] = old_r2 + db
    p1["count"] = c1 + 1
    p2["count"] = c2 + 1

    save_data(data)

    return jsonify({
        "success": True,
        "p1": {
            "id": p1["id"],
            "name": p1["name"],
            "old_rating": old_r1,
            "new_rating": p1["rating"],
            "diff": da,
            "count": p1["count"]
        },
        "p2": {
            "id": p2["id"],
            "name": p2["name"],
            "old_rating": old_r2,
            "new_rating": p2["rating"],
            "diff": db,
            "count": p2["count"]
        },
        "result": result
    })

def print_banner(ip, port):
    url = f"http://{ip}:{port}"
    local_url = f"http://localhost:{port}"

    print("\n" + "=" * 60)
    print("  🔥 スマブラ レーティング管理 Webサーバー起動中 🔥")
    print("=" * 60)
    print(f"\n[PCからのアクセス]:     {local_url}")
    print(f"[スマホからのアクセス]:   {url}")
    print("\nスマホを同じWi-Fiに接続し、以下のQRコードを")
    print("スマホのカメラで読み取るだけで開けます！\n")

    try:
        import qrcode
        qr = qrcode.QRCode(box_size=1, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except Exception:
        pass

    print("\n" + "-" * 60)
    print("※ 終了するには、この黒い画面で [Ctrl + C] を押してください。")
    print("-" * 60 + "\n")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    local_ip = get_local_ip()
    print_banner(local_ip, port)
    app.run(host="0.0.0.0", port=port, debug=False)

