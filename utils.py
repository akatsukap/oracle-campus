from pathlib import Path
import json
import time

# data/database.json のパス
DATA_PATH = Path(__file__).parent / "data" / "database.json"

# データの初期形
DEFAULT_DATA = {
    "users": {},
    "markets": [],
    "bets": [],
}

# Cache for load_data to avoid repeated file reads
_data_cache = {"data": None, "mtime": 0}


def load_data():
    """database.json を読み込んで dict を返す。なければ初期データを返す。
    
    Uses caching to avoid repeated file reads when the file hasn't changed.
    """
    if not DATA_PATH.exists():
        # ファイルがない場合は初期データを返す
        return DEFAULT_DATA.copy()

    try:
        # Check if file has been modified since last read
        current_mtime = DATA_PATH.stat().st_mtime
        if _data_cache["data"] is not None and _data_cache["mtime"] == current_mtime:
            # Return cached data (deep copy to prevent mutation)
            return json.loads(json.dumps(_data_cache["data"]))
        
        with DATA_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Update cache
        _data_cache["data"] = data
        _data_cache["mtime"] = current_mtime
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
    # Invalidate cache after save
    _data_cache["data"] = None
    _data_cache["mtime"] = 0



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


def get_market_by_id(markets, market_id):
    """Efficiently find a market by ID using dictionary lookup.
    
    Args:
        markets: List of market dictionaries
        market_id: The market ID to find
    
    Returns:
        The market dict if found, None otherwise
    """
    market_id_str = str(market_id)
    for m in markets:
        if str(m.get("id")) == market_id_str:
            return m
    return None


def create_market(data, title, description, end_datetime):
    """Create a new market in the provided data dict.
    
    Args:
        data: The data dict containing markets list
        title: Market title
        description: Market description
        end_datetime: End datetime in ISO format
    
    Returns:
        The new market ID
    """
    markets = data.get("markets", [])
    # Find max ID
    max_id = max((m.get("id", 0) for m in markets), default=0)
    new_id = max_id + 1
    
    markets.append({
        "id": new_id,
        "title": title,
        "description": description,
        "end_datetime": end_datetime,
        "status": "open",
        "yes_bets": 0,
        "no_bets": 0,
        "result": None,
    })
    data["markets"] = markets
    return new_id


def resolve_market(data, market_id, result):
    """Resolve a market with the given result.
    
    Args:
        data: The data dict containing markets list
        market_id: The market ID to resolve
        result: The result value ("Yes" or "No")
    
    Returns:
        True if market was found and resolved, False otherwise
    """
    market = get_market_by_id(data.get("markets", []), market_id)
    if market:
        market["result"] = result
        market["status"] = "closed"
        return True
    return False


def list_markets(data):
    """List all markets from the data dict.
    
    Args:
        data: The data dict containing markets list
    
    Returns:
        List of market dicts
    """
    return data.get("markets", [])


def normalize_onchain_market(m):
    """Convert an on-chain market to local format.
    
    This shared function eliminates duplication across pages.
    
    Args:
        m: Raw on-chain market dict with keys like endTime, totalYes, etc.
    
    Returns:
        Normalized market dict matching local format
    """
    try:
        end_ts = int(m.get("endTime") or 0)
    except (ValueError, TypeError):
        end_ts = 0
    
    is_resolved = m.get("resolved", False)
    is_past_end = end_ts != 0 and end_ts <= int(time.time())
    status = "closed" if is_resolved or is_past_end else "open"
    
    return {
        "id": str(m.get("id")),
        "title": m.get("title") or "タイトル未設定",
        "description": m.get("description", "") or "",
        "end_time": end_ts,
        "yes_bets": int(m.get("totalYes", 0)),
        "no_bets": int(m.get("totalNo", 0)),
        "status": status,
        "result": m.get("outcome") if is_resolved else None,
        "source": "onchain",
    }


def merge_markets(local_markets, onchain_markets):
    """Merge local and on-chain markets, with on-chain taking priority.
    
    Args:
        local_markets: List of local market dicts
        onchain_markets: List of on-chain market dicts (already normalized)
    
    Returns:
        List of merged market dicts
    """
    # Add source flag to local markets
    for lm in local_markets:
        lm.setdefault("id", str(lm.get("id", "")))
        lm.setdefault("end_time", lm.get("end_datetime") or 0)
        lm.setdefault("source", "local")
    
    # Merge with on-chain priority
    merged = {str(m.get("id")): m for m in local_markets}
    for m in onchain_markets:
        merged[str(m.get("id"))] = m
    
    return list(merged.values())
