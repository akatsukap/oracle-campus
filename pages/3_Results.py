import time
from typing import Dict, List

import pandas as pd
import streamlit as st


@st.cache_resource
def get_web3_manager_safe():
    """Create Web3Manager with caching; return None when setup fails."""
    try:
        from utils.web3_manager import Web3Manager

        return Web3Manager()
    except Exception as exc:  # noqa: BLE001
        st.session_state.setdefault("_web3_init_error", str(exc))
        return None


def _normalize_market(raw: Dict) -> Dict:
    """Convert contract market dict into a uniform shape used in the UI."""
    try:
        end_ts = int(raw.get("endTime") or 0)
    except Exception:  # noqa: BLE001
        end_ts = 0

    now_ts = int(time.time())
    if raw.get("resolved"):
        status = "closed"
    elif end_ts == 0 or end_ts > now_ts:
        status = "open"
    else:
        status = "closed"

    return {
        "id": str(raw.get("id")),
        "title": raw.get("title") or "タイトル未設定",
        "end_time": end_ts,
        "yes_bets": int(raw.get("totalYes", 0)),
        "no_bets": int(raw.get("totalNo", 0)),
        "status": status,
        "result": raw.get("outcome") if raw.get("resolved") else None,
    }


def _pull_markets(web3_mgr) -> List[Dict]:
    if not web3_mgr:
        return []
    try:
        onchain_raw = web3_mgr.get_all_markets() or []
    except Exception as exc:  # noqa: BLE001
        st.warning(f"オンチェーン市場の取得に失敗しました: {exc}")
        return []
    return [_normalize_market(m) for m in onchain_raw]


def _parse_address_lines(raw: str) -> List[str]:
    addrs = []
    for line in raw.splitlines():
        addr = line.strip()
        if addr:
            addrs.append(addr)
    return addrs


st.title("結果・ランキング")

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("トップページでユーザーを選択してください。")
    st.stop()

web3_mgr = get_web3_manager_safe()

status_col1, status_col2 = st.columns(2)
with status_col1:
    if web3_mgr and web3_mgr.w3.is_connected():
        st.success("Web3 接続中 ✅")
    else:
        st.error("Web3 接続に失敗しました。環境変数と ABI を確認してください。")
        if st.session_state.get("_web3_init_error"):
            st.caption(st.session_state.get("_web3_init_error"))

with status_col2:
    pass

if not web3_mgr:
    st.stop()

with st.spinner("オンチェーンから市場データを取得中..."):
    markets = _pull_markets(web3_mgr)

open_markets = [m for m in markets if m.get("status") == "open"]
closed_markets = [m for m in markets if m.get("status") == "closed"]

total_volume = sum(m.get("yes_bets", 0) + m.get("no_bets", 0) for m in markets)

metric_cols = st.columns(3)
metric_cols[0].metric("開催中の市場", len(open_markets))
metric_cols[1].metric("終了した市場", len(closed_markets))
metric_cols[2].metric("合計プールサイズ", total_volume)

st.markdown("---")
st.subheader("あなたのオンチェーン状況")

user_address = st.text_input(
    "成績を確認するウォレットアドレス",
    value=getattr(web3_mgr.account, "address", ""),
    help="空の場合は接続中ウォレットを使用します。",
)

target_address = user_address.strip() or getattr(web3_mgr.account, "address", None)
if not target_address:
    st.error("ウォレットアドレスを入力してください。")
    st.stop()

balance = 0
user_bets: List[Dict] = []
try:
    balance = web3_mgr.get_balance(target_address)
    user_bets = web3_mgr.get_all_user_bets(target_address)
except Exception as exc:  # noqa: BLE001
    st.error(f"ウォレット情報の取得に失敗しました: {exc}")

left, right, third = st.columns(3)
left.metric("OCP 残高", balance)
right.metric("保有ベット件数", len(user_bets))
third.metric("対象ウォレット", target_address)

if user_bets:
    st.write("### このウォレットのベット一覧")
    enriched = []
    market_map = {m.get("id"): m for m in markets}
    for b in user_bets:
        mid = str(b.get("market_id"))
        m = market_map.get(mid, {})
        enriched.append(
            {
                "market_id": mid,
                "title": m.get("title", "不明"),
                "amount": b.get("amount", 0),
                "direction": "Yes" if b.get("isYes") else "No",
                "claimed": b.get("claimed", False),
                "status": m.get("status", "unknown"),
                "result": m.get("result"),
            }
        )

    df_bets = pd.DataFrame(enriched)
    st.dataframe(df_bets, use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("ウォレット別ランキング（残高順）")

default_block = getattr(web3_mgr.account, "address", "")
address_block = st.text_area(
    "ランキングに含めるウォレットアドレス (1行につき1つ)",
    value=default_block,
    height=120,
)

addresses = set(_parse_address_lines(address_block))
if default_block:
    addresses.add(default_block)

rows = []
for addr in addresses:
    try:
        bal = web3_mgr.get_balance(addr)
        bets = web3_mgr.get_all_user_bets(addr)
        total_staked = sum(int(b.get("amount", 0)) for b in bets)
        rows.append(
            {
                "address": addr,
                "balance": bal,
                "active_bets": len(bets),
                "total_staked": total_staked,
            }
        )
    except Exception as exc:  # noqa: BLE001
        st.warning(f"{addr} の取得に失敗しました: {exc}")

if rows:
    df_rank = pd.DataFrame(rows)
    df_rank = df_rank.sort_values(by=["balance", "total_staked"], ascending=False).reset_index(drop=True)
    df_rank.insert(0, "rank", df_rank.index + 1)
    st.dataframe(
        df_rank,
        use_container_width=True,
        hide_index=True,
        column_config={
            "balance": st.column_config.NumberColumn("残高 (OCP)", format="%d"),
            "total_staked": st.column_config.NumberColumn("累計ベット額", format="%d"),
            "active_bets": st.column_config.NumberColumn("ベット件数"),
        },
    )
else:
    st.info("ランキング対象のウォレットがありません。")

st.markdown("---")
st.subheader("市場の結果とプールランキング")

if not markets:
    st.info("オンチェーン市場がまだありません。")
else:
    top_by_pool = sorted(
        markets,
        key=lambda m: m.get("yes_bets", 0) + m.get("no_bets", 0),
        reverse=True,
    )
    st.caption("プール=Yes/Noに積まれたOCPの合計です。")
    pool_df = pd.DataFrame(
        [
            {
                "title": m.get("title"),
                "status": m.get("status"),
                "result": m.get("result", "未確定"),
                "pool": m.get("yes_bets", 0) + m.get("no_bets", 0),
                "yes": m.get("yes_bets", 0),
                "no": m.get("no_bets", 0),
            }
            for m in top_by_pool
        ]
    )
    st.dataframe(
        pool_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "pool": st.column_config.NumberColumn("プール合計", format="%d"),
            "yes": st.column_config.NumberColumn("Yes", format="%d"),
            "no": st.column_config.NumberColumn("No", format="%d"),
        },
    )




    
# import sys
# import os
# sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# import streamlit as st
# import pandas as pd

# from utils import load_data, save_data

# # =========================================================
# # 【修正箇所】
# # エラーが出る 'utils.web3_manager' ではなく、
# # 1_Main.py で正常に動いている 'data.fibase' を使います。
# # =========================================================
# try:
#     from data.fibase import Web3Manager
# except ImportError:
#     # 万が一 data.fibase が無い場合は元のファイル（非推奨）に戻す
#     from utils.web3_manager import Web3Manager

# # Web3Manager をキャッシュ化して読み込む（1_Main.py と同じ方式）
# @st.cache_resource
# def get_web3_manager():
#     try:
#         return Web3Manager()
#     except Exception:
#         return None

# # マネージャーの初期化
# web3_mgr = get_web3_manager()

# # サイドバーへの接続状態表示
# if web3_mgr:
#     # 実際に接続確認
#     if web3_mgr.w3.is_connected():
#         st.sidebar.success("Web3 接続成功 ✅")
#     else:
#         st.sidebar.warning("Web3 インスタンスは作成されましたが、接続に失敗しています。")
#         web3_mgr = None
# else:
#     st.sidebar.warning("Web3 利用不可（フォールバックモード）")


# def main():
#     st.title("結果・ランキング")

#     # データ読み込み: ユーザー／bets はローカルを参照、
#     # markets は可能ならオンチェーンを優先して取得する
#     local_data = load_data() or {}
#     users = local_data.get("users", {})
#     bets = local_data.get("bets", [])

#     # markets をオンチェーンから取得（可能なら）
#     markets = []
#     if web3_mgr:
#         try:
#             onchain_raw = web3_mgr.get_all_markets() or []
#             for m in onchain_raw:
#                 status = "closed" if m.get("resolved") else "open"
#                 markets.append({
#                     "id": m.get("id"),
#                     "title": m.get("title"),
#                     "description": "",
#                     "status": status,
#                     "yes_bets": int(m.get("totalYes", 0)),
#                     "no_bets": int(m.get("totalNo", 0)),
#                     "result": m.get("outcome") if m.get("resolved") else None,
#                 })
#         except Exception as e:
#             # オンチェーン取得に失敗したらローカルにフォールバック
#             try:
#                 st.warning(f"オンチェーン市場の取得に失敗しました（フォールバック）: {e}")
#             except Exception:
#                 pass
#             markets = local_data.get("markets", [])
#     else:
#         markets = local_data.get("markets", [])

#     # セッションから選択ユーザーを取得（`app.py` で選択されていることを前提とする）
#     user_id = st.session_state.get("user_id")
#     if not user_id:
#         st.error("セッションにユーザーが設定されていません。トップページでユーザーを選択してください。")
#         st.stop()

#     # ベースポイント
#     base_points = int(users.get(user_id, {}).get("points", 0))

#     # ---------------------------------------------------------
#     # オンチェーン残高を取得して表示する
#     # ---------------------------------------------------------
#     onchain_points = 0
#     if web3_mgr:
#         try:
#             # 自分のアドレス（.envの秘密鍵のアドレス）の残高を取得
#             onchain_points = web3_mgr.get_balance()
#         except Exception as e:
#             # エラー時は静かに0にする
#             onchain_points = 0

#     # ---------------------------------------------------------

#     # ユーザーが獲得したスコア（bets の集計）
#     got_score = 0
#     participated_market_ids = []
#     for b in bets:
#         try:
#             if b.get("user") == user_id:
#                 if "reward" in b and b.get("reward") is not None:
#                     got_score += int(b.get("reward", 0))
#                 else:
#                     got_score += int(b.get("amount", 0))
#                 participated_market_ids.append(str(b.get("market_id")))
#         except Exception:
#             continue

#     total_score = base_points + got_score

#     # 参加したイベント情報を取得
#     participated_markets = [m for m in markets if str(m.get("id")) in participated_market_ids]

#     # 参加者ランキングを作成
#     participants = []
#     for uid, info in users.items():
#         pts = int(info.get("points", 0))
#         extra = 0
#         for b in bets:
#             if b.get("user") == uid:
#                 extra += int(b.get("reward", b.get("amount", 0) or 0))
#         name = "自分" if uid == user_id else uid
#         score = pts + extra
#         participants.append({"name": name, "score": score})

#     # サンプルユーザー
#     sample = [
#         {"name": "Aさん", "score": 120},
#         {"name": "Bさん", "score": 95},
#         {"name": "Cさん", "score": 80},
#         {"name": "Dさん", "score": 60},
#     ]
#     existing_names = {p["name"] for p in participants}
#     for s in sample:
#         if s["name"] not in existing_names:
#             participants.append(s)

#     # DataFrame にして順位付け
#     df = pd.DataFrame(participants)
#     df = df.sort_values(by="score", ascending=False).reset_index(drop=True)
#     df["rank"] = df.index + 1

#     # 自分の行を取得して表示
#     me_row = df[df["name"] == "自分"]
#     if not me_row.empty:
#         my_score = int(me_row.iloc[0]["score"])
#         my_rank = int(me_row.iloc[0]["rank"])
#     else:
#         my_score = total_score
#         higher = (df["score"] > my_score).sum()
#         my_rank = int(higher) + 1

#     # 画面表示
#     cols = st.columns([1, 2, 1])
#     cols[0].metric(label="あなたのベースポイント", value=base_points)
#     cols[1].metric(label="今回獲得したスコア", value=got_score)
#     cols[2].metric(label="オンチェーン残高", value=onchain_points)

#     st.markdown("---")
#     st.metric(label="合計スコア（ベース + 獲得）", value=total_score)
#     st.metric(label="あなたの順位", value=f"{my_rank} / {len(df)}")

#     st.markdown("---")
#     st.subheader("今回参加したイベント")
#     if participated_markets:
#         for m in participated_markets:
#             st.markdown(f"- **{m.get('title', 'タイトル未設定')}** （ID: {m.get('id')}） - ステータス: `{m.get('status')}`")
#     else:
#         st.write("このユーザーはまだイベントに参加していません。")

#     st.markdown("---")
#     st.subheader("全参加者のランキング")

#     display_df = df[["rank", "name", "score"]].copy()
#     display_df = display_df.rename(columns={"rank": "順位", "name": "名前", "score": "スコア"})

#     def format_row(row):
#         if row["名前"] == "自分":
#             return f"**{row['名前']} (あなた)**"
#         return row["名前"]

#     disp = display_df.copy()
#     disp["名前"] = disp.apply(format_row, axis=1)
#     st.table(disp)

#     # 開催中と終了済みイベントの表示
#     st.markdown("---")
#     st.subheader("開催中のイベント")
    
#     # オンチェーン市場が取得できていればマージ
#     onchain_markets = []
#     if web3_mgr:
#         try:
#             onchain_raw = web3_mgr.get_all_markets() or []
#             for m in onchain_raw:
#                 status = "closed" if m.get("resolved") else "open"
#                 open_m = {
#                     "id": m.get("id"),
#                     "title": m.get("title"),
#                     "description": "",
#                     "status": status,
#                     "yes_bets": int(m.get("totalYes", 0)),
#                     "no_bets": int(m.get("totalNo", 0)),
#                     "result": m.get("outcome") if m.get("resolved") else None,
#                 }
#                 onchain_markets.append(open_m)
#         except Exception:
#             pass

#     merged = {str(m.get("id")): m for m in markets}
#     for m in onchain_markets:
#         merged[str(m.get("id"))] = m
#     all_markets = list(merged.values())

#     open_markets = [m for m in all_markets if m.get("status") == "open"]
#     if open_markets:
#         for m in open_markets:
#             st.markdown(f"- **{m.get('title', 'タイトル未設定')}** （ID: {m.get('id')}）")
#     else:
#         st.write("開催中のイベントはありません。")

#     st.markdown("---")
#     st.subheader("終了したイベント")
#     closed_markets = [m for m in all_markets if m.get("status") == "closed"]
#     if closed_markets:
#         for m in closed_markets:
#             st.markdown(f"- **{m.get('title', 'タイトル未設定')}** （ID: {m.get('id')}） - 結果: `{m.get('result', '未確定')}`")
#     else:
#         st.write("まだ終了したイベントはありません。")

#     # 管理者用: 市場を確定するボタン
#     if user_id == "admin":
#         st.markdown("---")
#         st.subheader("🛠 管理者操作: 市場の結果を確定")
    
#         if web3_mgr:
#             st.success(f"Web3接続中: {web3_mgr.account.address}")
#         else:
#             st.error("⚠️ Web3に接続されていません。書き込みはできません。")

#         with st.expander("オンチェーンで市場を確定（resolve）"):
#             mid = st.text_input("市場 ID を入力", key="resolve_mid")
#             outcome = st.selectbox("結果を選択", ["yes", "no"], key="resolve_outcome")
            
#             if st.button("確定（オンチェーン実行）"):
#                 if not mid:
#                     st.error("市場 ID を入力してください")
#                 elif not web3_mgr:
#                     st.error("Web3マネージャーが起動していないため、ブロックチェーンに書き込めません。")
#                 else:
#                     try:
#                         with st.spinner("ブロックチェーンに書き込み中...（10〜20秒かかります）"):
#                             onchain_outcome = True if outcome == "yes" else False
#                             receipt = web3_mgr.resolve_market(int(mid), onchain_outcome)
                            
#                             st.balloons()
#                             st.success("✅ 書き込み成功！")
                            
#                             # トランザクションハッシュの表示（存在する場合）
#                             tx_hash = getattr(receipt, 'transactionHash', None)
#                             if tx_hash:
#                                 st.info(f"Tx Hash: {tx_hash.hex()}")
#                                 st.markdown(f"[Etherscanで確認](https://sepolia.etherscan.io/tx/{tx_hash.hex()})")
#                             else:
#                                 st.info("トランザクション完了")

#                             # ローカルデータも更新
#                             for m in markets:
#                                 if str(m.get("id")) == str(mid):
#                                     m["status"] = "closed"
#                                     m["result"] = outcome
#                             local_data["markets"] = markets
#                             save_data(local_data)
                            
#                     except Exception as e:
#                         st.error(f"❌ 書き込み失敗: {e}")
#                         st.warning("ヒント: `.env`の秘密鍵は、コントラクトを作った人のものと同じですか？")


# if __name__ == "__main__":
#     main()

