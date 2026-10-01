import pandas as pd
import streamlit as st
import random
import time
import base64
import os
import unicodedata

st.set_page_config(page_title="化学式・化学反応式クイズ", page_icon="🧪")

# 全角英数字・記号を半角に正規化する関数
def normalize_str(text):
    if not text:
        return ""
    return unicodedata.normalize('NFKC', str(text)).strip()

# --------------------------------------------------
# 背景動的設定関数（最上部ヘッダー透明化＆入力欄視認性向上）
# --------------------------------------------------
def set_background(image_file, is_title=False):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            data = f.read()
        b64_data = base64.b64encode(data).decode()
        
        top_margin = "200px" if is_title else "80px"
        
        st.markdown(
            f"""
            <style>
            /* Streamlitの最上部ヘッダー帯を完全透明化 */
            header[data-testid="stHeader"] {{
                background-color: transparent !important;
            }}
            
            /* アプリ全体の最上部背景 */
            .stApp {{
                background-image: url("data:image/png;base64,{b64_data}");
                background-size: cover;
                background-position: top center;
                background-repeat: no-repeat;
                background-attachment: fixed;
                background-color: transparent !important;
            }}
            
            /* 中央メインカード */
            [data-testid="stMainBlockContainer"] {{
                background-color: rgba(255, 255, 255, 0.85) !important;
                padding: 2rem 2.5rem !important;
                border-radius: 16px !important;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
                margin-top: {top_margin} !important;
                margin-bottom: 2rem !important;
                max-width: 750px !important;
                backdrop-filter: blur(4px);
            }}
            
            /* 通常テキスト */
            [data-testid="stMainBlockContainer"] p, 
            [data-testid="stMainBlockContainer"] h1, 
            [data-testid="stMainBlockContainer"] h2, 
            [data-testid="stMainBlockContainer"] h3, 
            [data-testid="stMainBlockContainer"] span {{
                color: #111111 !important;
            }}

            /* テキスト入力欄の完全固定（ライト/ダークモード問わず濃い紺背景に白文字） */
            .stTextInput input {{
                color: #ffffff !important;
                background-color: #2b2d42 !important;
                -webkit-text-fill-color: #ffffff !important;
                font-weight: bold !important;
                font-size: 1.1rem !important;
            }}

            .stTextInput div[data-baseweb="input"] {{
                background-color: #2b2d42 !important;
                border: 2px solid #4a4e69 !important;
                border-radius: 8px !important;
            }}

            .stTextInput div[data-baseweb="input"]:focus-within {{
                border-color: #7209b7 !important;
                background-color: #2b2d42 !important;
            }}

            .stTextInput input::placeholder {{
                color: #a0a0a0 !important;
            }}

            /* ボタンデザイン */
            .stButton > button {{
                border-radius: 8px !important;
                font-weight: bold !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

# --- CSV読み込み関数 ---
@st.cache_data
def load_questions():
    df = pd.read_csv("questions.csv").fillna("")
    questions = []
    for idx, row in df.iterrows():
        q_type = str(row.get("type", "")).strip()
        title = str(row.get("title", "")).strip()
        if not q_type or not title:
            continue

        try:
            q_id = int(row["id"])
        except (ValueError, TypeError):
            q_id = idx + 1

        q_data = {
            "id": q_id,
            "type": q_type,
            "title": title,
        }
        if q_type == "equation":
            q_data["left_coef"] = [normalize_str(x) for x in str(row["left_coef"]).split(",") if x.strip()]
            q_data["left_sub"] = [normalize_str(x).lstrip('0123456789') for x in str(row["left_substance"]).split(",") if x.strip()]
            
            q_data["right_coef"] = [normalize_str(x) for x in str(row["right_coef"]).split(",") if x.strip()]
            q_data["right_sub"] = [normalize_str(x).lstrip('0123456789') for x in str(row["right_substance"]).split(",") if x.strip()]
        else:
            q_data["correct"] = normalize_str(row["correct_answer"])
        questions.append(q_data)
    return questions

all_questions = load_questions()

# --- セッション状態の初期化 ---
if "level" not in st.session_state:
    st.session_state.level = None
if "shuffled_questions" not in st.session_state:
    st.session_state.shuffled_questions = []
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "time_limit" not in st.session_state:
    st.session_state.time_limit = 30
if "q_start_time" not in st.session_state:
    st.session_state.q_start_time = None
if "answered" not in st.session_state:
    st.session_state.answered = False

# --------------------------------------------------
# 画面1: オープニング画面
# --------------------------------------------------
if st.session_state.level is None:
    set_background("title_bg.jpg", is_title=True)

    st.markdown("<h3 style='text-align: center; margin-bottom: 1.5rem;'>コースを選択してスタート！</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🌱 初級編\n(1問 30秒 / 係数のみ)", use_container_width=True):
            st.session_state.level = "初級"
            st.session_state.time_limit = 30
            st.session_state.shuffled_questions = random.sample(all_questions, len(all_questions))
            st.session_state.q_index = 0
            st.session_state.score = 0
            st.session_state.q_start_time = time.time()
            st.session_state.answered = False
            st.rerun()
            
    with col2:
        if st.button("🔥 上級編\n(1問 60秒 / 完全解答)", use_container_width=True):
            st.session_state.level = "上級"
            st.session_state.time_limit = 60
            st.session_state.shuffled_questions = random.sample(all_questions, len(all_questions))
            st.session_state.q_index = 0
            st.session_state.score = 0
            st.session_state.q_start_time = time.time()
            st.session_state.answered = False
            st.rerun()

# --------------------------------------------------
# 画面2: クイズ出題画面
# --------------------------------------------------
else:
    set_background("game_bg.jpg", is_title=False)

    # 1. サイドバー
    st.sidebar.markdown(f"### コース: {st.session_state.level}編")
    if st.sidebar.button("🚪 途中退出（タイトルへ）", use_container_width=True):
        st.session_state.level = None
        st.rerun()

    # 2. 残り時間の計算
    elapsed_time = time.time() - st.session_state.q_start_time
    remaining_time = max(0, int(st.session_state.time_limit - elapsed_time))

    # 3. 試験管メーター計算
    total_q_count = len(st.session_state.shuffled_questions)
    gauge_ratio = (st.session_state.score % total_q_count) / total_q_count if total_q_count > 0 else 0.0

    col_t1, col_t2 = st.columns([1, 1])
    with col_t1:
        st.metric(label="⏱ この問題の残り時間", value=f"{remaining_time} 秒")
    with col_t2:
        st.metric(label="🧪 試験管の液体", value=f"{int(gauge_ratio * 100)} %")
    
    st.progress(gauge_ratio, text=f"🧪 試薬蓄積度: 正解数 {st.session_state.score} 問")
    st.markdown("---")

    q_list = st.session_state.shuffled_questions
    q = q_list[st.session_state.q_index]

    st.subheader(f"問題 {st.session_state.q_index + 1}: {q['title']}")

    # 4. 時間切れ判定
    if remaining_time <= 0 and not st.session_state.answered:
        st.session_state.answered = True
        st.error("⏰ 時間切れです！「次の問題へ」を押してください。")

    # 5. 問題フォーム
    if q["type"] == "single":
        st.write("該当する化学式を入力してください。")
        user_input = normalize_str(st.text_input("解答欄", key=f"single_{q['id']}_{st.session_state.q_index}"))
        
        if st.button("答え合わせ", type="primary", disabled=st.session_state.answered):
            st.session_state.answered = True
            if user_input == normalize_str(q["correct"]):
                st.success("🎉 正解です！試験管に液体が溜まりました！")
                st.session_state.score += 1
            else:
                st.error(f"❌ 不正解です。 正解: **{q['correct']}**")

    else:
        if st.session_state.level == "初級":
            st.write("化学反応式の**係数（□に入る数字）**を入力してください。（1の場合は空欄可）")
            left_inputs = []
            cols_l = st.columns(len(q["left_sub"]) * 2)
            for i in range(len(q["left_sub"])):
                with cols_l[i * 2]:
                    val = st.text_input(f"左係数_{i}", key=f"l_c_{q['id']}_{st.session_state.q_index}_{i}", label_visibility="collapsed", placeholder="係数")
                    left_inputs.append(normalize_str(val))
                with cols_l[i * 2 + 1]:
                    st.write(f"**{q['left_sub'][i]}**" + (" ＋ " if i < len(q["left_sub"]) - 1 else ""))

            st.markdown("### ➔")

            right_inputs = []
            cols_r = st.columns(len(q["right_sub"]) * 2)
            for i in range(len(q["right_sub"])):
                with cols_r[i * 2]:
                    val = st.text_input(f"右係数_{i}", key=f"r_c_{q['id']}_{st.session_state.q_index}_{i}", label_visibility="collapsed", placeholder="係数")
                    right_inputs.append(normalize_str(val))
                with cols_r[i * 2 + 1]:
                    st.write(f"**{q['right_sub'][i]}**" + (" ＋ " if i < len(q["right_sub"]) - 1 else ""))

            if st.button("答え合わせ", type="primary", disabled=st.session_state.answered):
                st.session_state.answered = True
                l_ans = [inp if inp != "" else "1" for inp in left_inputs]
                r_ans = [inp if inp != "" else "1" for inp in right_inputs]
                
                if l_ans == q["left_coef"] and r_ans == q["right_coef"]:
                    st.success("🎉 正解です！試験管に液体が溜まりました！")
                    st.session_state.score += 1
                else:
                    st.error("❌ 不正解です。")
                    l_str = " + ".join([(c if c!='1' else '') + s for c, s in zip(q['left_coef'], q['left_sub'])])
                    r_str = " + ".join([(c if c!='1' else '') + s for c, s in zip(q['right_coef'], q['right_sub'])])
                    st.info(f"💡 正解: **{l_str} ➔ {r_str}**")

        else:  # 上級編
            st.write("各枠に適切な**化学式（係数含む）**を入力してください。")
            
            correct_left = [normalize_str((c if c != "1" else "") + s) for c, s in zip(q["left_coef"], q["left_sub"])]
            correct_right = [normalize_str((c if c != "1" else "") + s) for c, s in zip(q["right_coef"], q["right_sub"])]

            left_inputs = []
            cols_l = st.columns(len(q["left_sub"]) * 2 - 1)
            for i in range(len(q["left_sub"])):
                with cols_l[i * 2]:
                    val = st.text_input(f"左_{i}", key=f"l_f_{q['id']}_{st.session_state.q_index}_{i}", label_visibility="collapsed")
                    left_inputs.append(normalize_str(val))
                if i < len(q["left_sub"]) - 1:
                    with cols_l[i * 2 + 1]:
                        st.markdown("### ＋")

            st.markdown("### ➔")

            right_inputs = []
            cols_r = st.columns(len(q["right_sub"]) * 2 - 1)
            for i in range(len(q["right_sub"])):
                with cols_r[i * 2]:
                    val = st.text_input(f"右_{i}", key=f"r_f_{q['id']}_{st.session_state.q_index}_{i}", label_visibility="collapsed")
                    right_inputs.append(normalize_str(val))
                if i < len(q["right_sub"]) - 1:
                    with cols_r[i * 2 + 1]:
                        st.markdown("### ＋")

            if st.button("答え合わせ", type="primary", disabled=st.session_state.answered):
                st.session_state.answered = True
                
                if set(left_inputs) == set(correct_left) and set(right_inputs) == set(correct_right):
                    st.success("🎉 正解です！試験管に液体が溜まりました！")
                    st.session_state.score += 1
                else:
                    st.error("❌ 不正解です。")
                    st.info(f"💡 正解: **{' + '.join(correct_left)} ➔ {' + '.join(correct_right)}**")

    # --- 次の問題進むボタン ---
    if st.session_state.answered:
        if st.button("次の問題へ ➔"):
            st.session_state.answered = False
            st.session_state.q_start_time = time.time()
            next_index = st.session_state.q_index + 1
            if next_index >= len(q_list):
                st.session_state.shuffled_questions = random.sample(all_questions, len(all_questions))
                st.session_state.q_index = 0
            else:
                st.session_state.q_index = next_index
            st.rerun()

    # 6. タイマーリアルタイム更新
    if not st.session_state.answered and remaining_time > 0:
        time.sleep(1)
        st.rerun()