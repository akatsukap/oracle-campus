import streamlit as st

def apply_common_style():
    """
    魔法と冒険がテーマのディズニー風・爽快デザイン
    """
    
    # 1. ページ構成の統一 (wide設定)
    st.set_page_config(
        page_title="Oracle Campus | 魔法の学び舎",
        page_icon="✨",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 2. 魔法と冒険のカスタムCSS
    st.markdown("""
        <style>
        /* メイン背景：淡い水色から白へのグラデーション（爽やかさ重視） */
        .stApp {
            background: linear-gradient(180deg, #e0f2fe 0%, #ffffff 100%);
            color: #1e293b;
        }
        
        /* サイドバー：魔法のような深みのある青 */
        [data-testid="stSidebar"] {
            background-color: #0c4a6e !important;
        }

        /* --- サイドバー全体の視認性改善 --- */
        
        /* 1. サイドバー全体の基本文字色を白に強制 */
        [data-testid="stSidebar"] {
            color: white !important;
            text-shadow: 0px 0px 10px rgba(255, 255, 255, 0.9) !important; /* 強い光の影 */
            font-weight: 700 !important; /* 太字 */
            font-size: 1.1rem !important; /* 少し大きく */

        }

        /* 2. 「透明性の証明」などの見出し・通常テキストを白く光らせる */
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] .stCaption {
            color: white !important;
            text-shadow: 0px 0px 12px rgba(255, 255, 255, 0.8) !important;
            font-weight: bold !important;
        }

        /* 3. 白い枠（コードブロック）の中の文字を濃い青にする（白飛び対策） */
        [data-testid="stSidebar"] code {
            color: #0c4a6e !important; /* 背景と同じ濃い青にすることでハッキリ見える */
            background-color: rgba(255, 255, 255, 0.9) !important;
            font-weight: bold !important;
        }

        /* 4. 白いボタン（リンクボタン）の中の文字を濃い青にする（白飛び対策） */
        [data-testid="stSidebar"] .stLinkButton a {
            background-color: white !important;
            border: 2px solid #fbbf24 !important; /* ゴールドの枠線 */
        }
        
        /* ボタン内のテキストとアイコンの色を強制指定 */
        [data-testid="stSidebar"] .stLinkButton p {
            color: #0c4a6e !important; 
            text-shadow: none !important; /* ボタン内は影なしでスッキリ */
        }

        /* 5. ナビゲーションメニューの未選択・選択中の文字色 */
        [data-testid="stSidebarNav"] span {
            color: white !important;
            font-weight: 600 !important;
        }

        /* 見出し：男子が好きな「ヒーロー・冒険」を感じる青とゴールド */
        h1 {
            color: #0369a1 !important; /* 濃い水色 */
            font-family: 'Arial Black', sans-serif;
            border-left: 10px solid #fbbf24; /* 横にゴールドのアクセント */
            padding-left: 15px;
        }
        h2, h3 {
            color: #075985 !important;
        }

        /* ボタン：クリスタルのような光沢感 */
        .stButton>button {
            background: linear-gradient(90deg, #0ea5e9, #2563eb) !important;
            color: white !important;
            border-radius: 8px;
            border: none !important;
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
            font-weight: bold;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
        }

        /* カード形式の装飾（もしあれば） */
        .stMetric {
            background-color: white;
            padding: 15px;
            border-radius: 15px;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        }
                
        /* --- 通知ボックス（success/info/warning）の視認性改善 --- */
        
        /* success（緑色の枠）の中の文字を白く太くする */
        [data-testid="stSidebar"] div[data-testid="stNotification"] {
            background-color: rgba(0, 0, 0, 0.3) !important; /* 背景を少し暗くして文字を浮かせる */
            border: 1px solid #fbbf24 !important; /* 枠線をゴールドにして魔法感を出す */
        }

        /* 中のテキストを強制的に白にする */
        [data-testid="stSidebar"] div[data-testid="stNotification"] [data-testid="stMarkdownContainer"] p {
            color: white !important;
            font-weight: bold !important;
            text-shadow: 0px 0px 5px rgba(0, 0, 0, 0.5) !important;
        }

        /* サイドバー内のアイコンの色を調整 */
        [data-testid="stSidebar"] [data-testid="stNotification"] [data-testid="stIcon"] {
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 共通ルール定数 ---
TITLE_ICON = "🏰"
HEADER_ICON = "🛡️"

# 成功・警告・エラーのアイコン
SUCCESS_EMOJI = "💎"
WARNING_EMOJI = "⚠️"
ERROR_EMOJI = "🔥"

# ローディング文言
SPINNER_TEXT = "魔法の力を溜めています..."

def draw_line():
    st.markdown("---")

def sidebar_status_success(message):
    st.sidebar.markdown(f"""
        <div style="background-color: #000; color: #fff; padding: 10px; border-radius: 5px;">
            {message}
        </div>
    """, unsafe_allow_html=True)  # ← これが絶対に必要です！