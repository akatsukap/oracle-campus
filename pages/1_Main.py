# ...existing code...
import streamlit as st
from utils import load_data, normalize_onchain_market, merge_markets
import time
from datetime import datetime

# 互換性ありの再実行ヘルパー
def _safe_rerun():
    """st.experimental_rerun が無ければ内部の RerunException を投げる / 最終フォールバックで停止する"""
    try:
        # 標準的な API があれば使う
        if hasattr(st, "experimental_rerun"):
            st.rerun()
            return
    except Exception:
        pass

    # internal API に頼る（存在すれば例外を投げて再実行させる）
    try:
        from streamlit.runtime.scriptrunner.script_runner import RerunException
        raise RerunException()
    except Exception:
        # 最終フォールバック: セッションフラグを立てて処理を止める
        st.session_state["_rerun_requested"] = True
        st.stop()

# --- Web3 の安全な初期化（失敗時は None を返す） ---
@st.cache_resource
def get_web3_manager_safe():
    try:
        # data ディレクトリにある fibase モジュールを利用
        from data.fibase import Web3Manager
        mgr = Web3Manager()
        return mgr
    except Exception as e:
        # 初期化失敗は UI に表示するが例外は投げない
        st.session_state.setdefault("_web3_init_error", str(e))
        return None

# メインページ：ダッシュボード
st.title("Oracle Campus 🎓")
st.subheader("予測市場ダッシュボード（メイン画面）")

# ユーザーIDの取得
user_id = st.session_state.get("user_id")

if not user_id:
    st.warning("まずトップページでユーザーを選択してください。")
    st.stop()

# データの読み込み（ローカル）- uses caching internally
data = load_data() or {}
users = data.get("users", {}) if isinstance(data, dict) else {}
local_markets = data.get("markets", []) if isinstance(data, dict) else []

# Web3 マネージャの取得（キャッシュ）
web3_mgr = get_web3_manager_safe()

# オンチェーン市場を取得（可能なときのみ）。手動更新ボタンを提供
col1, col2 = st.columns([1, 3])
with col1:
    if web3_mgr is None:
        st.info("ブロックチェーン接続が無効です（環境変数やABI、RPC URL を確認してください）。")
        if st.session_state.get("_web3_init_error"):
            st.caption(st.session_state["_web3_init_error"])
    else:
        if st.button("オンチェーン市場を更新"):
            # キャッシュをクリアして再取得
            get_web3_manager_safe.clear()
            web3_mgr = get_web3_manager_safe()

with col2:
    if web3_mgr:
        try:
            onchain_raw = web3_mgr.get_all_markets() or []
        except Exception as e:
            st.warning(f"オンチェーン市場の取得に失敗しました: {e}")
            onchain_raw = []
    else:
        onchain_raw = []

# Use shared function for on-chain market normalization
onchain_markets = [normalize_onchain_market(m) for m in onchain_raw]

# Use shared function for merging markets
markets = merge_markets(local_markets, onchain_markets)

# ユーザー情報の確認
user = users.get(user_id)

if not user:
    st.error(f"ユーザー {user_id} の情報が見つかりません。管理者に連絡してください。")
    st.stop()

# ─────────────────────────────
# 1. 自分のポイント情報（ローカル表示）
# ─────────────────────────────
st.markdown("### 👤 あなたのステータス")
st.write(f"- ユーザーID：`{user_id}`")
st.write(f"- 所持ポイント：**{user.get('points', 0)} OCP**")

# オプション：サーバー側の Web3 アカウント残高を表示（存在する場合のみ）
if web3_mgr:
    try:
        bal = web3_mgr.get_balance()
        st.write(f"- コントラクトに登録されたサーバーアカウント残高（参考）：**{bal} OCP**")
    except Exception:
        pass

st.divider()

# ─────────────────────────────
# 2. 募集中のイベント一覧（マージ結果）
# ─────────────────────────────
st.markdown("### 📈 募集中の予測イベント")

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

        # 投票ページへの遷移（session_state に選択マーケットを入れる）
        market_id = m.get("id")
        if st.button("このイベントに投票する 🗳️", key=f"vote_{market_id}"):
            st.session_state["selected_market"] = market_id
            _safe_rerun()

        st.divider()

# ─────────────────────────────
# 3. 終了済みイベント（サマリ）
# ─────────────────────────────
st.markdown("### ✅ 終了したイベント（サマリ）")

closed_markets = [m for m in markets if m.get("status") == "closed"]
closed_markets.sort(key=lambda x: x.get("end_time", 0) or 0, reverse=True)

if not closed_markets:
    st.write("まだ終了したイベントはありません。")
else:
    for m in closed_markets:
        st.markdown(f"- **{m.get('title', 'タイトル未設定')}**：結果 → `{m.get('result', '未確定')}` （ソース：`{m.get('source')}`）")