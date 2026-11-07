import pygame
import sys
import os
import random
import math
import json

# =====================
# 設定値
# =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
K = 80
alpha = 0.5
beta = 1
cap = 80
DATA_FILE = os.path.join(BASE_DIR, "players.json")
PAGE_SIZE = 10
MAX_RATING_DIFF = 350

# =====================
# データ読み込み
# =====================
class Player:
    def __init__(self, pid, name, rating, count, hid=0, char=""):
        self.id = int(pid)
        self.hid = int(hid)
        self.name = name
        self.char = char
        self.rating = int(rating)
        self.count = int(count)
    def __repr__(self):
        return f"{self.name}({self.rating})"

def load_players():
    players = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data.get("players", []):
                players.append(Player(
                    pid=item.get("id"),
                    name=item.get("name"),
                    rating=item.get("rating"),
                    count=item.get("count", 0),
                    hid=item.get("hid", 0),
                    char=item.get("character", item.get("char", ""))
                ))
    else:
        txt_file = os.path.join(BASE_DIR, "data.txt")
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        pid, name, char, rating, count = line.strip().split(",")
                        players.append(Player(pid, name, rating, count, char=char))
    return players

def save_players():
    data = {
        "players": [
            {
                "id": p.id,
                "hid": p.hid,
                "name": p.name,
                "rating": p.rating,
                "count": p.count
            }
            for p in players
        ]
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

players = load_players()
classA = [p for p in players if 1 <= p.id <= 86 and p.name != "-"]
classB = [p for p in players if 87 <= p.id <= 172 and p.name != "-"]

# =====================
# レート計算
# =====================
def S(d):
    return 0.5 + alpha * (d/3) ** beta

def calc_change(p1, p2, d):
    Elo = 1 / (1 + 10 ** ((p2.rating - p1.rating)/400))
    K_A = K * max(1, 2 - 0.05 * p1.count)
    K_B = K * max(1, 2 - 0.05 * p2.count)
    s_val = S(d)
    if d > 0:
        da = min(cap, max(1, round(K_A*(s_val - Elo)))) if d==3 else min(cap, round(K_A*(s_val - Elo)))
        db = max(-cap, min(-1, round(K_B*(Elo - s_val)))) if d==3 else max(-cap, round(K_B*(Elo - s_val)))
    else:
        da = max(-cap, min(-1, round(K_A*(s_val - Elo)))) if d==-3 else max(-cap, round(K_A*(s_val - Elo)))
        db = min(cap, max(1, round(K_B*(Elo - s_val)))) if d==-3 else min(cap, round(K_B*(Elo - s_val)))
    return da, db

# =====================
# pygame設定
# =====================
pygame.init()
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SmashBros Rating System")

def find_japanese_font():
    # Mac標準パス
    mac_font = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
    if os.path.exists(mac_font):
        return mac_font
    # OSフォント検索 (Windows / Linux / その他)
    for name in ["msgothic", "meiryo", "yugothic", "notosanscjkjp", "takaoexgothic", "ipagothic"]:
        matched = pygame.font.match_font(name)
        if matched:
            return matched
    return None

font_path = find_japanese_font()
_font_cache = {}

def get_font(size=24):
    if size not in _font_cache:
        if font_path:
            _font_cache[size] = pygame.font.Font(font_path, size)
        else:
            _font_cache[size] = pygame.font.SysFont(["msgothic", "meiryo", "yugothic", "sans-serif"], size)
    return _font_cache[size]

font = get_font(24)
bigfont = get_font(40)
clock = pygame.time.Clock()
WHITE = (255,255,255); BLACK = (0,0,0)
GRAY = (200,200,200); BLUE = (100,100,255)

def draw_text(text, x, y, size=24, color=BLACK):
    f = get_font(size)
    s = f.render(str(text), True, color)
    screen.blit(s, (x,y))

def button(text, x, y, w, h):
    rect = pygame.Rect(x,y,w,h)
    pygame.draw.rect(screen, GRAY, rect)
    pygame.draw.rect(screen, BLACK, rect, 2)
    label = font.render(text, True, BLACK)
    screen.blit(label, (x+10, y+10))
    return rect

# =====================
# プレイヤー選択
# =====================
def select_player(players, title):
    idx = 0; page = 0
    total_pages = math.ceil(len(players)/PAGE_SIZE)
    sorted_players = sorted(players, key=lambda x:x.name)
    while True:
        screen.fill(WHITE)
        draw_text(f"{title} (ESCで戻る)",50,30,30)
        start = page*PAGE_SIZE; end = start + PAGE_SIZE
        for i,p in enumerate(sorted_players[start:end]):
            y = 80 + i*30
            draw_text(f"{p.name} ({p.rating})", 50, y)
            if i==idx: pygame.draw.rect(screen, BLUE, (40,y-2,800,28), 2)
        draw_text(f"ページ {page+1}/{total_pages}",700,30,20)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: save_players(); pygame.quit(); sys.exit()
            elif e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE: return None
                elif e.key==pygame.K_DOWN: idx=(idx+1)%min(PAGE_SIZE,len(sorted_players[start:end]))
                elif e.key==pygame.K_UP: idx=(idx-1)%min(PAGE_SIZE,len(sorted_players[start:end]))
                elif e.key==pygame.K_RIGHT: page=(page+1)%total_pages; idx=0
                elif e.key==pygame.K_LEFT: page=(page-1)%total_pages; idx=0
                elif e.key==pygame.K_RETURN: return sorted_players[start+idx]
        pygame.display.flip()
        clock.tick(60)

# =====================
# 勝敗選択（プレイヤー情報表示）
# =====================
def select_result(p1=None, p2=None):
    results = [3,2,1,-1,-2,-3]; idx = 0
    while True:
        screen.fill(WHITE)
        draw_text("勝負の結果を選択 (ESCで戻る)", 50,30,30)
        if p1 and p2:
            draw_text(f"P1: {p1.name} ({p1.rating})", 50,70)
            draw_text(f"P2: {p2.name} ({p2.rating})", 50,100)
        for i,r in enumerate(results):
            y = 150 + i*50
            draw_text(str(r),100,y)
            if i==idx: pygame.draw.rect(screen, BLUE, (90,y-5,100,40), 2)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: save_players(); pygame.quit(); sys.exit()
            elif e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE: return None
                elif e.key==pygame.K_DOWN: idx=(idx+1)%len(results)
                elif e.key==pygame.K_UP: idx=(idx-1)%len(results)
                elif e.key==pygame.K_RETURN: return results[idx]
        pygame.display.flip()
        clock.tick(60)

# =====================
# レート戦
# =====================
def rate_battle():
    p1 = select_player(classA,"プレイヤー1を選択")
    if p1 is None: return
    p2 = select_player(classB,"プレイヤー2を選択")
    if p2 is None: return
    d = select_result(p1,p2)
    if d is None: return
    while True:
        screen.fill(WHITE)
        draw_text("確認",50,30,30)
        draw_text(f"P1: {p1.name} (レート: {p1.rating})",50,100)
        draw_text(f"P2: {p2.name} (レート: {p2.rating})",50,150)
        draw_text(f"結果: {d}",50,200)
        b1 = button("はい",200,300,100,50)
        b2 = button("いいえ",400,300,100,50)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: save_players(); pygame.quit(); sys.exit()
            elif e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: return
            elif e.type==pygame.MOUSEBUTTONDOWN:
                if b1.collidepoint(e.pos):
                    da,db = calc_change(p1,p2,d)
                    old1,old2 = p1.rating,p2.rating
                    p1.rating+=da; p2.rating+=db
                    p1.count+=1; p2.count+=1
                    while True:
                        screen.fill(WHITE)
                        draw_text("結果",50,30,30)
                        draw_text(f"{p1.name}: {old1} -> {p1.rating} ({da:+})",50,100)
                        draw_text(f"{p2.name}: {old2} -> {p2.rating} ({db:+})",50,150)
                        back = button("戻る",300,400,200,50)
                        for ee in pygame.event.get():
                            if ee.type==pygame.QUIT: save_players(); pygame.quit(); sys.exit()
                            elif ee.type==pygame.KEYDOWN and (ee.key==pygame.K_ESCAPE or ee.key==pygame.K_RETURN): return
                            elif ee.type==pygame.MOUSEBUTTONDOWN:
                                if back.collidepoint(ee.pos): return
                        pygame.display.flip()
                        clock.tick(60)
                elif b2.collidepoint(e.pos): return
        pygame.display.flip()
        clock.tick(60)

def random_battle():

    # =====================
    # 候補選択関数
    # =====================
    def get_candidates(player_list):
        low_count = [p for p in player_list if p.count < 10]

        # 10未満がいれば優先
        if low_count:
            return low_count

        return player_list

    # =====================
    # 重み関数
    # =====================
    def weight(p):
        return 1 / (1 + p.count)

    candidatesA = get_candidates(classA)
    candidatesB = get_candidates(classB)

    # =====================
    # マッチ可能ペア作成
    # =====================
    valid_pairs = []

    for p1 in candidatesA:
        for p2 in candidatesB:

            # レート差制限
            if abs(p1.rating - p2.rating) <= MAX_RATING_DIFF:
                pair_weight = weight(p1) * weight(p2)

                valid_pairs.append((p1, p2, pair_weight))

    # =====================
    # マッチ可能ペアがない場合
    # =====================
    if not valid_pairs:

        while True:
            screen.fill(WHITE)

            draw_text("マッチ可能なプレイヤーがいません", 180, 250, 32)
            draw_text(f"レート差制限: {MAX_RATING_DIFF}", 250, 320, 24)

            back = button("戻る", 350, 420, 200, 60)

            for e in pygame.event.get():

                if e.type == pygame.QUIT:
                    save_players()
                    pygame.quit()
                    sys.exit()

                elif e.type == pygame.MOUSEBUTTONDOWN:
                    if back.collidepoint(e.pos):
                        return

            pygame.display.flip()

    # =====================
    # 重み付きランダム選択
    # =====================
    pairs = [(p1, p2) for p1, p2, w in valid_pairs]
    weights = [w for p1, p2, w in valid_pairs]

    p1, p2 = random.choices(pairs, weights=weights)[0]

    # =====================
    # 結果入力
    # =====================
    d = select_result(p1, p2)
    if d is None:
        return

    while True:

        screen.fill(WHITE)

        draw_text("確認",50,30,30)
        draw_text(f"P1: {p1.name} (レート: {p1.rating})",50,100)
        draw_text(f"P2: {p2.name} (レート: {p2.rating})",50,150)
        draw_text(f"結果: {d}",50,200)

        b1 = button("はい",200,300,100,50)
        b2 = button("いいえ",400,300,100,50)

        for e in pygame.event.get():

            if e.type == pygame.QUIT:
                save_players()
                pygame.quit()
                sys.exit()

            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return

            elif e.type == pygame.MOUSEBUTTONDOWN:

                if b1.collidepoint(e.pos):

                    da, db = calc_change(p1, p2, d)

                    old1, old2 = p1.rating, p2.rating

                    p1.rating += da
                    p2.rating += db

                    p1.count += 1
                    p2.count += 1

                    while True:

                        screen.fill(WHITE)

                        draw_text("結果",50,30,30)

                        draw_text(
                            f"{p1.name}: {old1} -> {p1.rating} ({da:+})",
                            50,100
                        )

                        draw_text(
                            f"{p2.name}: {old2} -> {p2.rating} ({db:+})",
                            50,150
                        )

                        back = button("戻る",300,400,200,50)

                        for ee in pygame.event.get():

                            if ee.type == pygame.QUIT:
                                save_players()
                                pygame.quit()
                                sys.exit()

                            elif ee.type == pygame.KEYDOWN and (ee.key == pygame.K_ESCAPE or ee.key == pygame.K_RETURN):
                                return

                            elif ee.type == pygame.MOUSEBUTTONDOWN:

                                if back.collidepoint(ee.pos):
                                    return

                        pygame.display.flip()
                        clock.tick(60)

                elif b2.collidepoint(e.pos):
                    return

        pygame.display.flip()
        clock.tick(60)

# =====================
# レート確認（クラス切替＋ページング）
# =====================
# =====================
# レート確認（クラス切替＋ページング）
# =====================
# =====================
# レート確認（クラス切替＋ページング）
# =====================
def show_ratings():
    current_class = "A"  # 初期表示はクラスA
    page = 0
    PAGE_SIZE = 10

    while True:
        screen.fill(WHITE)

        # クラス選択ボタン
        bA = button("クラスA", 50, 30, 100, 40)
        bB = button("クラスB", 200, 30, 100, 40)

        # 表示するプレイヤーリスト
        if current_class == "A":
            sorted_list = sorted(classA, key=lambda x: x.rating, reverse=True)
        else:
            sorted_list = sorted(classB, key=lambda x: x.rating, reverse=True)

        total_pages = math.ceil(len(sorted_list)/PAGE_SIZE)
        start = page * PAGE_SIZE
        display_list = sorted_list[start:start+PAGE_SIZE]

        # 列幅をピクセル単位で計算（日本語対応）
        name_width = max((font.size(p.name)[0] for p in display_list), default=80) + 40
        rating_width = max((font.size(str(p.rating))[0] for p in display_list), default=60) + 40
        rank_width = max((font.size(f"{start+i+1}位")[0] for i in range(len(display_list))), default=60) + 40

        # X座標決定
        x_name = 80
        x_rating = x_name + name_width + 40
        x_rank = x_rating + rating_width + 40

        # ヘッダー
        draw_text("名前", x_name, 90, 24)
        draw_text("レート", x_rating, 90, 24)
        draw_text("順位", x_rank, 90, 24)

        # プレイヤー描画（同じレートなら同じ順位）
        rank = 1
        prev_rating = None
        same_rank_count = 0

        for i, p in enumerate(sorted_list):
            # ページに含まれるか確認
            if i < start or i >= start + PAGE_SIZE:
                # 順位カウントだけ進める
                if prev_rating is None:
                    prev_rating = p.rating
                    same_rank_count = 1
                else:
                    if p.rating == prev_rating:
                        same_rank_count += 1
                    else:
                        rank += same_rank_count
                        same_rank_count = 1
                        prev_rating = p.rating
                continue

            y = 130 + (i - start)*30
            draw_text(p.name, x_name, y)
            draw_text(str(p.rating), x_rating, y)

            # 順位計算
            if prev_rating is None:
                display_rank = rank
                same_rank_count = 1
            else:
                if p.rating == prev_rating:
                    display_rank = rank
                    same_rank_count += 1
                else:
                    rank += same_rank_count
                    display_rank = rank
                    same_rank_count = 1
            prev_rating = p.rating

            draw_text(f"{display_rank}位", x_rank, y)

        # ページ表示
        draw_text(f"ページ {page+1}/{total_pages}", 700, 30, 20)

        # 戻るボタン
        back = button("戻る", 700, 500, 120, 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_players()
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back.collidepoint(event.pos):
                    return
                elif bA.collidepoint(event.pos):
                    current_class = "A"
                    page = 0
                elif bB.collidepoint(event.pos):
                    current_class = "B"
                    page = 0
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                elif event.key == pygame.K_RIGHT:
                    page = (page + 1) % total_pages
                elif event.key == pygame.K_LEFT:
                    page = (page - 1) % total_pages

        pygame.display.flip()
        clock.tick(60)

# =====================
# メインメニュー
# =====================
def main_menu():
    while True:
        screen.fill(WHITE)
        draw_text("メインメニュー", 350, 100, 40)
        b1 = button("1. レート戦",300,200,300,50)
        b2 = button("2. ランダムレート戦",300,280,300,50)
        b3 = button("3. レートの確認",300,360,300,50)
        b4 = button("4. 終了",300,440,300,50)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: save_players(); pygame.quit(); sys.exit()
            elif e.type==pygame.KEYDOWN:
                if e.key==pygame.K_1: rate_battle()
                elif e.key==pygame.K_2: random_battle()
                elif e.key==pygame.K_3: show_ratings()
                elif e.key==pygame.K_4 or e.key==pygame.K_ESCAPE: save_players(); pygame.quit(); sys.exit()
            elif e.type==pygame.MOUSEBUTTONDOWN:
                if b1.collidepoint(e.pos): rate_battle()
                elif b2.collidepoint(e.pos): random_battle()
                elif b3.collidepoint(e.pos): show_ratings()
                elif b4.collidepoint(e.pos): save_players(); pygame.quit(); sys.exit()
        pygame.display.flip()
        clock.tick(60)

# =====================
# メインループ開始
# =====================
if __name__ == "__main__":
    try:
        main_menu()
    except Exception as e:
        import traceback
        print("\n[エラーが発生しました]:", file=sys.stderr)
        traceback.print_exc()
        input("\nEnterキーを押して終了してください...")
