# filepath: pages/1_Main.py

import os
import time
from datetime import datetime

import streamlit as st
import style_config as sc

#デザイン統一
sc.apply_common_style()

# ─────────────────────────────
# 0. 互換性ありの再実行ヘルパー
# ─────────────────────────────
def _safe_rerun():
    """
    st.experimental_rerun が無ければ内部の RerunException を投げる /
    最終フォールバックで処理を停止する
    """
    try:
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
            return
    except Exception:
        pass

    try:
        from streamlit.runtime.scriptrunner.script_runner import RerunException

        raise RerunException()
    except Exception:
        st.session_state["_rerun_requested"] = True
        st.stop()


# ─────────────────────────────
# 1. Web3 の安全な初期化（失敗時は None を返す）
# ─────────────────────────────
@st.cache_resource
def get_web3_manager_safe():
    """
    utils.web3_manager.Web3Manager をキャッシュ付きで生成する。

    - 成功 : Web3Manager インスタンス
    - 失敗 : None（UI 側で「接続できません」と表示する）
    """
    try:
        from utils.web3_manager import Web3Manager

        mgr = Web3Manager()
        return mgr
    except Exception as e:
        st.session_state.setdefault("_web3_init_error", str(e))
        return None


# ─────────────────────────────
# 2. ページヘッダ & ユーザー確認
# ─────────────────────────────
st.title("🎓Oracle Campus ")
st.subheader("予測市場ダッシュボード（メイン画面）")

# app.py でセットされたユーザーID
user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("まずトップページでユーザーを選択してください。")
    st.stop()


# ─────────────────────────────
# 3. Web3 / オンチェーン市場データの取得
# ─────────────────────────────
web3_mgr = get_web3_manager_safe()

col1, col2 = st.columns([1, 3])

# 左カラム：Web3 接続の状態 & 更新ボタン
with col1:
    if web3_mgr is None:
        st.info("ブロックチェーン接続が無効です（環境変数や ABI、RPC URL を確認してください）。")
        if st.session_state.get("_web3_init_error"):
            st.caption(st.session_state["_web3_init_error"])
    else:
        if st.button("オンチェーン市場を更新"):
            get_web3_manager_safe.clear()
            web3_mgr = get_web3_manager_safe()

# 右カラム：オンチェーン市場データ取得
with col2:
    if web3_mgr:
        try:
            # ★ ここで Web3.py 経由でブロックチェーンのスマートコントラクトからデータ取得
            onchain_raw = web3_mgr.get_all_markets() or []
        except Exception as e:
            st.warning(f"オンチェーン市場の取得に失敗しました: {e}")
            onchain_raw = []
    else:
        onchain_raw = []


# onchain_raw をアプリ内部の market 形式に変換
def _to_local_market(m):
    """
    Web3Manager.get_all_markets() が返す dict を、
    アプリ内部で扱いやすい統一フォーマットに変換する。
    """
    try:
        end_ts = int(m.get("endTime") or 0)
    except Exception:
        end_ts = 0

    now_ts = int(time.time())
    if m.get("resolved"):
        status = "closed"
    elif end_ts == 0 or end_ts > now_ts:
        status = "open"
    else:
        status = "closed"

    return {
        "id": str(m.get("id")),
        "title": m.get("title") or "タイトル未設定",
        "description": m.get("description", "") or "",
        "end_time": end_ts,
        "yes_bets": int(m.get("totalYes", 0)),
        "no_bets": int(m.get("totalNo", 0)),
        "status": status,
        "result": m.get("outcome") if m.get("resolved") else None,
        "source": "onchain",
    }


# ★ ここが唯一のデータソース：オンチェーンのみ
markets = [_to_local_market(m) for m in onchain_raw]


# ─────────────────────────────
# 4. 自分のポイント情報（オンチェーン残高表示）
# ─────────────────────────────
st.markdown("### 👤 あなたのステータス")
st.write(f"- ユーザーID：`{user_id}`")

if web3_mgr:
    try:
        bal = web3_mgr.get_balance()
        st.write(f"- 所持ポイント（オンチェーン）：**{bal} OCP**")
    except Exception as e:
        st.warning(f"オンチェーン残高の取得に失敗しました: {e}")
else:
    st.info("Web3 に接続できていないため、オンチェーン残高は表示できません。")

st.divider()


# ─────────────────────────────
# 5. 募集中のイベント一覧（オンチェーンのみ）
# ─────────────────────────────
st.markdown("### 📈 募集中の予測イベント（オンチェーン）")

open_markets = [m for m in markets if m.get("status") == "open"]
open_markets.sort(key=lambda x: x.get("end_time", 0) or 0)

if not open_markets:
    st.info("現在、投票受付中のイベントはありません。")
else:
    for m in open_markets:
        st.markdown(f"#### 🟢 {m.get('title', 'タイトル未設定')}")
        if desc := m.get("description"):
            st.write(desc)

        st.write(
            f"- Yes 合計：**{m.get('yes_bets', 0)}** OCP  "
            f"- No 合計：**{m.get('no_bets', 0)}** OCP  "
            f"- ソース：`{m.get('source')}`"
        )

        market_id = m.get("id")
        if st.button("このイベントに投票する 🗳️", key=f"vote_{market_id}"):
            st.session_state["selected_market"] = market_id
            _safe_rerun()

        st.divider()


# ─────────────────────────────
# 6. 終了済みイベント（オンチェーン）
# ─────────────────────────────
st.markdown("### ✅ 終了したイベント（オンチェーン）")

closed_markets = [m for m in markets if m.get("status") == "closed"]
closed_markets.sort(key=lambda x: x.get("end_time", 0) or 0, reverse=True)

if not closed_markets:
    st.write("まだ終了したイベントはありません。")
else:
    for m in closed_markets:
        st.markdown(
            f"- **{m.get('title', 'タイトル未設定')}**："
            f"結果 → `{m.get('result', '未確定')}` （ソース：`{m.get('source')}`）"
        )


# ─────────────────────────────
# 7. サイドバー: Web3 透明性の証明（スマートコントラクト情報）
# ─────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown("### ⛓️ 透明性の証明")

contract_address = os.getenv("CONTRACT_ADDRESS")

if contract_address:
    st.sidebar.caption("接続中スマートコントラクト:")
    st.sidebar.code(contract_address)

    etherscan_url = f"https://sepolia.etherscan.io/address/{contract_address}"
    st.sidebar.link_button("🔍 Etherscanで投票履歴を確認", etherscan_url)
else:
    st.sidebar.caption("接続中スマートコントラクト: 未設定")
    st.sidebar.warning("`.env` の CONTRACT_ADDRESS が設定されていません。")
