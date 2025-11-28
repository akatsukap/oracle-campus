# ...existing code...
import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any

DATA_FILE = os.path.join(os.path.dirname(__file__), "markets.json")

def _ensure_file():
    if not os.path.exists(DATA_FILE):
        _save_markets([])

def _load_markets() -> List[Dict[str, Any]]:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception:
        return []

def _save_markets(markets: List[Dict[str, Any]]) -> None:
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(markets, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)

def create_market(title: str, description: str, end_datetime_iso: str) -> Dict[str, Any]:
    """
    新しいマーケットを作成して保存する。戻り値は作成したマーケット辞書。
    """
    _ensure_file()
    markets = _load_markets()
    m = {
        "id": uuid.uuid4().hex,
        "title": title,
        "description": description,
        "end_datetime": end_datetime_iso,
        "status": "open",
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    markets.append(m)
    _save_markets(markets)
    return m

def list_markets() -> List[Dict[str, Any]]:
    """
    保存済みのマーケット一覧を返す（順序は作成順）。
    """
    _ensure_file()
    return _load_markets()

def get_market(market_id: str) -> Dict[str, Any]:
    for m in list_markets():
        if m.get("id") == market_id:
            return m
    raise KeyError("market not found")

def resolve_market(market_id: str, result: str) -> Dict[str, Any]:
    """
    指定マーケットを確定（close）し、result を保存する。
    """
    markets = _load_markets()
    found = False
    for m in markets:
        if m.get("id") == market_id:
            m["status"] = "closed"
            m["result"] = result
            m["resolved_at"] = datetime.utcnow().isoformat() + "Z"
            found = True
            break
    if not found:
        raise KeyError(f"market {market_id} not found")
    _save_markets(markets)
    return m
# ...existing code...