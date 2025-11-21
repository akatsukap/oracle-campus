from pathlib import Path
import json

# data/database.json のパス
DATA_PATH = Path(__file__).parent / "data" / "database.json"

# データの初期形
DEFAULT_DATA = {
    "users": {},
    "markets": [],
    "bets": [],
}


def load_data():
    """database.json を読み込んで dict を返す。なければ初期データを返す。"""
    if not DATA_PATH.exists():
        # ファイルがない場合は初期データを返す
        return DEFAULT_DATA.copy()

    try:
        with DATA_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        # 壊れた JSON の場合も初期データにフォールバック
        return DEFAULT_DATA.copy()

    # 必要なキーが欠けていたら補完する（安全のため）
    for key, default_value in DEFAULT_DATA.items():
        if key not in data:
            data[key] = default_value.copy() if isinstance(default_value, dict) else default_value
    return data


def save_data(data: dict):
    """dict を database.json に保存する。"""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)



def init_sample_data():
    """初回用のサンプルデータを返す。"""
    return {
        "users": {
            "user1": {"points": 1000},
            "user2": {"points": 1000},
            "user3": {"points": 1000},
        },
        "markets": [
            {
                "id": 1,
                "title": "明日の天気は晴れか？",
                "description": "明日の昼12時時点で晴れているかどうか。",
                "status": "open",
                "yes_bets": 0,
                "no_bets": 0,
                "result": None,
            },
            {
                "id": 2,
                "title": "今週の学食来客数は1,000人を超える？",
                "description": "月〜金の合計来客数。",
                "status": "open",
                "yes_bets": 0,
                "no_bets": 0,
                "result": None,
            },
        ],
        "bets": [],
    }
