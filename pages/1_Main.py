# filepath: pages/1_Main.py
import os  # 追加
import time
from datetime import datetime

import streamlit as st


# --- Web3Manager を安全に初期化（失敗してもアプリが落ちないように） ---
@st.cache_resource
def get_web3_manager():
    """data.fibase.Web3Manager をキャッシュ付きで生成する"""
    from data.fibase import Web3Manager  # 遅延インポート（起動時エラーを防ぐ）
    return Web3Manager()


# --- ページ設定（マルチページ時は二重設定されても無視されるので try で囲む） ---
try:
    st.set_page_config(page_title="Oracle Campus", page_icon="🎓")
except Exception:
    pass

st.title("Oracle Campus 🎓")
st.subheader("予測市場ダッシュボード（メイン画面）")

# ─────────────────────────────
# 0. ログイン（ユーザー選択）チェック
# ─────────────────────────────
user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("まず app.py のトップ画面でユーザーを選択してください。")
    st.stop()

st.caption(f"現在のユーザー: `{user_id}`")

st.divider()

# ─────────────────────────────
# 1. Web3 接続 & データ取得
# ─────────────────────────────
with st.spinner("ブロックチェーンから市場情報を取得しています…"):
    try:
        web3_mgr = get_web3_manager()
        # 自分の残高を取得
        my_balance = web3_mgr.get_balance()
        # 全市場リストを取得
        markets = web3_mgr.get_all_markets() or []
    except Exception as e:
        st.error(f"Web3 接続またはデータ取得に失敗しました: {e}")
        st.warning("`.env` の設定や RPC URL / コントラクトアドレスを確認してください。")
        st.stop()

# サイドバーに残高表示
st.sidebar.metric("あなたの所持ポイント", f"{my_balance} OCP")

st.divider()

# ─────────────────────────────
# 2. 募集中のイベント一覧
# ─────────────────────────────
st.markdown("### 📈 募集中の予測イベント")

# resolved == False の市場のみ
open_markets = [m for m in markets if not m.get("resolved")]
# 締め切りが近い順にソート
open_markets.sort(key=lambda x: int(m.get("endTime", 0)) if (m := x) else 0)

if not open_markets:
    st.info("現在、投票受付中のイベントはありません。管理者画面からイベントを作成してください。")
else:
    now_ts = time.time()

    for m in open_markets:
        market_id = m.get("id")
        title = m.get("title", "タイトル未設定")

        # タイムスタンプ → 日付
        try:
            end_ts = int(m.get("endTime", 0) or 0)
            end_dt = datetime.fromtimestamp(end_ts)
        except Exception:
            end_ts = 0
            end_dt = None

        is_ended = bool(end_ts and end_ts < now_ts)
        status_text = "終了" if is_ended else "受付中"

        total_yes = int(m.get("totalYes", 0) or 0)
        total_no = int(m.get("totalNo", 0) or 0)
        total_pool = total_yes + total_no

        with st.container():
            col1, col2 = st.columns([3, 1])

            # --- 左カラム：タイトル・締切・Yes率 ---
            with col1:
                st.markdown(f"#### 🟢 {title}")

                caption_parts = [f"状態: {status_text}"]
                if end_dt:
                    caption_parts.append(f"締切: {end_dt.strftime('%Y/%m/%d %H:%M')}")
                st.caption(" | ".join(caption_parts))

                if total_pool > 0:
                    yes_ratio = total_yes / total_pool
                    st.progress(yes_ratio, text=f"Yes率: {int(yes_ratio * 100)}%")
                else:
                    st.text("まだ投票がありません")

            # --- 右カラム：数値とボタン ---
            with col2:
                st.write(f"Yes: **{total_yes}** OCP")
                st.write(f"No: **{total_no}** OCP")

                if not is_ended:
                    if st.button("投票へ進む 🗳️", key=f"vote_{market_id}"):
                        # Vote ページで使うマーケットIDを保存
                        st.session_state["selected_market_id"] = market_id
                        st.success(
                            f"「{title}」を選択しました。\n"
                            "サイドバーから **Vote** ページに移動して投票してください。"
                        )
                else:
                    st.button("受付終了", disabled=True, key=f"closed_{market_id}")

            st.divider()

# ─────────────────────────────
# 3. （おまけ）デバッグ情報
# ─────────────────────────────
with st.expander("🔍 デバッグ情報（開発者向け）"):
    st.write("取得した市場データ（先頭 3 件を表示）")
    st.json(markets[:3])

# ─────────────────────────────
# 4. サイドバー: 透明性の証明
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
