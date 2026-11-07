import os
import shutil

# =====================
# 設定値
# =====================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.txt")
BACKUP_DIR = os.path.join(BASE_DIR, "backup")

OLD_K = 50
NEW_K = 80

NEW_SEASON = 2

BASE_RATING = 1500

# =====================
# バックアップ作成
# =====================

old_season = NEW_SEASON - 1

os.makedirs(BACKUP_DIR, exist_ok=True)

backup_file = os.path.join(
    BACKUP_DIR,
    f"data_{old_season}.txt"
)

shutil.copy(DATA_FILE, backup_file)

print(f"バックアップ作成: {backup_file}")

# =====================
# レート変換
# =====================

new_lines = []

with open(DATA_FILE, "r", encoding="utf-8") as f:

    for line in f:

        line = line.strip()

        if not line:
            continue

        pid, name, char, rating, count = line.split(",")

        rating = int(rating)

        # =====================
        # レート変換
        # =====================

        # BASE_RATING を中心にスケーリング
        #
        # 例:
        # OLD_K = 50
        # NEW_K = 100
        #
        # 1600 -> 1700
        # 1400 -> 1300
        #

        new_rating = BASE_RATING + (
            (rating - BASE_RATING) * NEW_K / OLD_K
        )

        new_rating = round(new_rating)

        # =====================
        # count をリセット
        # =====================

        new_count = 0

        new_lines.append(
            f"{pid},{name},{char},{new_rating},{new_count}\n"
        )

# =====================
# data.txt 更新
# =====================

with open(DATA_FILE, "w", encoding="utf-8") as f:

    f.writelines(new_lines)

print("シーズン変更完了")
