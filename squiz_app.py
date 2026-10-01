import pandas as pd
import streamlit as st
import random
import time
import base64
import os

st.set_page_config(page_title="化学式・化学反応式クイズ", page_icon="🧪")

# --------------------------------------------------
# 背景動的設定関数（画面ごとに画像ファイルを切り替え）
# --------------------------------------------------
def set_background(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            data = f.read()
        b64_data = base64.b64encode(data).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{b64_data}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            .main .block-container {{
                background-color: rgba(255, 255, 255, 0.90);
                padding: 2rem;
                border-radius: 16px;
                margin-top: 1rem;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
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
    for _, row in df.iterrows():
        q_type = str(row["type"]).strip()
        q_data = {
            "id": int(row["id"]),
            "type": q_type,
            "title": str(row["title"]),
        }
        if q_type == "equation":
            q_data["left_coef"] = [x.strip() for x in str(row["left_coef"]).split(",") if x.strip()]
            q_data["left_sub"] = [x.strip() for x in str(row["left_substance"]).split(",") if x.strip()]
            q_data["right_coef"] = [x.strip() for x in str(row["right_coef"]).split(",") if x.strip()]
            q_data["right_sub"] = [x.strip() for x in str(row["right_substance"]).split(",") if x.strip()]
        else:
            q_data["correct"] = str(row["correct_answer"]).strip()
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
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "time_limit" not in st.session_state:
    st.session_state.time_limit = 30
if "answered" not in st.session_state:
    st.session_state.answered = False

# --------------------------------------------------
# 画面1: オープニング画面（タイトル用背景を表示）
# --------------------------------------------------
if st.session_state.level is None:
    # タイトル画面用の背景を設定（タイトル用画像が存在しない場合は既存の bg.jpg 等を使用）
    set_background("title_bg.jpg")

    st.title("🧪 化学式・化学反応式クイズ")
    st.subheader("挑戦するコースを選択してください")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🌱 初級編\n(制限時間 30秒 / 係数のみ)", use_container_width=True):
            st.session_state.level = "初級"
            st.session_state.time_limit = 30
            st.session_state.shuffled_questions = random.sample(all_questions, len(all_questions))
            st.session_state.q_index = 0
            st.session_state.score = 0
            st.session_state.start_time = time.time()
            st.session_state.answered = False
            st.rerun()
            
    with col2:
        if st.button("🔥 上級編\n(制限時間 60秒 / 完全解答)", use_container_width=True):
            st.session_state.level = "上級"
            st.session_state.time_limit = 60
            st.session_state.shuffled_questions = random.sample(all_questions, len(all_questions))
            st.session_state.q_index = 0
            st.session_state.score = 0
            st.session_state.start_time = time.time()
            st.session_state.answered = False
            st.rerun()

# --------------------------------------------------
# 画面2: クイズ出題画面（ゲーム用背景を表示）
# --------------------------------------------------
else:
    # ゲーム画面用の背景を設定
    set_background("game_bg.jpg")

    st.title("🧪 化学式・化学反応式クイズ")

    # 1. サイドバー（途中退出ボタン）
    st.sidebar.markdown(f"### コース: {st.session_state.level}編")
    if st.sidebar.button("🚪 途中退出（タイトルへ）", use_container_width=True):
        st.session_state.level = None
        st.rerun()

    # 2. 制限時間（タイマー）計算
    elapsed_time = time.time() - st.session_state.start_time
    remaining_time = max(0, int(st.session_state.time_limit - elapsed_time))

    # 3. 試験管メーター（プログレスバー）計算
    total_q_count = len(st.session_state.shuffled_questions)
    gauge_ratio = (st.session_state.score % total_q_count) / total_q_count if total_q_count > 0 else 0.0

    # 画面上部インフォメーション表示
    col_t1, col_t2 = st.columns([1, 1])
    with col_t1:
        st.metric(label="⏱ 制限時間", value=f"{remaining_time} 秒")
    with col_t2:
        st.metric(label="🧪 試験管の液体", value=f"{int(gauge_ratio * 100)} %")
    
    # 試験管メーター
    st.progress(gauge_ratio, text=f"🧪 試薬蓄積度: 正解数 {st.session_state.score} 問")

    st.markdown("---")

    # 4. タイムアップ判定
    if remaining_time <= 0:
        st.error("⏰ タイムアップ！制限時間終了です。")
        st.balloons()
        st.subheader(f"🎉 最終スコア: {st.session_state.score} 問正解！")
        if st.button("タイトルに戻る", type="primary"):
            st.session_state.level = None
            st.rerun()

    # 5. 通常の問題出題
    else:
        q_list = st.session_state.shuffled_questions
        q = q_list[st.session_state.q_index]

        st.subheader(f"問題 {st.session_state.q_index + 1}: {q['title']}")

        # --- 単純化学式問題 (single) ---
        if q["type"] == "single":
            st.write("該当する化学式を入力してください。")
            user_input = st.text_input("解答欄", key=f"single_{q['id']}_{st.session_state.q_index}").strip()
            
            if st.button("答え合わせ", type="primary", disabled=st.session_state.answered):
                st.session_state.answered = True
                if user_input == q["correct"]:
                    st.success("🎉 正解です！試験管に液体が溜まりました！")
                    st.session_state.score += 1
                else:
                    st.error(f"❌ 不正解です。 正解: **{q['correct']}**")

        # --- 化学反応式問題 (equation) ---
        else:
            if st.session_state.level == "初級":
                st.write("化学反応式の**係数（□に入る数字）**を入力してください。（1の場合は空欄可）")
                left_inputs = []
                cols_l = st.columns(len(q["left_sub"]) * 2)
                for i in range(len(q["left_sub"])):
                    with cols_l[i * 2]:
                        val = st.text_input(f"左係数_{i}", key=f"l_c_{q['id']}_{st.session_state.q_index}_{i}", label_visibility="collapsed", placeholder="係数")
                        left_inputs.append(val.strip())
                    with cols_l[i * 2 + 1]:
                        st.write(f"**{q['left_sub'][i]}**" + (" ＋ " if i < len(q["left_sub"]) - 1 else ""))

                st.markdown("### ➔")

                right_inputs = []
                cols_r = st.columns(len(q["right_sub"]) * 2)
                for i in range(len(q["right_sub"])):
                    with cols_r[i * 2]:
                        val = st.text_input(f"右係数_{i}", key=f"r_c_{q['id']}_{st.session_state.q_index}_{i}", label_visibility="collapsed", placeholder="係数")
                        right_inputs.append(val.strip())
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
                correct_left = [(c if c != "1" else "") + s for c, s in zip(q["left_coef"], q["left_sub"])]
                correct_right = [(c if c != "1" else "") + s for c, s in zip(q["right_coef"], q["right_sub"])]

                left_inputs = []
                cols_l = st.columns(len(q["left_sub"]) * 2 - 1)
                for i in range(len(q["left_sub"])):
                    with cols_l[i * 2]:
                        val = st.text_input(f"左_{i}", key=f"l_f_{q['id']}_{st.session_state.q_index}_{i}", label_visibility="collapsed")
                        left_inputs.append(val.strip())
                    if i < len(q["left_sub"]) - 1:
                        with cols_l[i * 2 + 1]:
                            st.markdown("### ＋")

                st.markdown("### ➔")

                right_inputs = []
                cols_r = st.columns(len(q["right_sub"]) * 2 - 1)
                for i in range(len(q["right_sub"])):
                    with cols_r[i * 2]:
                        val = st.text_input(f"右_{i}", key=f"r_f_{q['id']}_{st.session_state.q_index}_{i}", label_visibility="collapsed")
                        right_inputs.append(val.strip())
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

        # --- 次の問題進むロジック ---
        if st.session_state.answered:
            if st.button("次の問題へ ➔"):
                st.session_state.answered = False
                next_index = st.session_state.q_index + 1
                if next_index >= len(q_list):
                    st.session_state.shuffled_questions = random.sample(all_questions, len(all_questions))
                    st.session_state.q_index = 0
                else:
                    st.session_state.q_index = next_index
                st.rerun()