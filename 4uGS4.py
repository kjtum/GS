
import streamlit as st
import random
import matplotlib.pyplot as plt
from PIL import Image
import os
from best20_prefs import BEST_PREFS

MEN = ["A", "B", "C", "D"]
WOMEN = ["X", "Y", "Z", "W"]
IMAGE_DIR = "img"

st.set_page_config(layout="wide")
st.title("安定結婚問題 - GS法（女性からの提案）段階シミュレーション")

def reset_session_state(men_prefs, women_prefs):
    st.session_state.men_prefs = men_prefs
    st.session_state.women_prefs = women_prefs
    st.session_state.step = 0
    st.session_state.proposals = {w: [] for w in WOMEN}
    st.session_state.engaged = {}
    st.session_state.free_women = WOMEN[:]
    st.session_state.received = {m: [] for m in MEN}

def generate_random_prefs():
    men = {m: random.sample(WOMEN, len(WOMEN)) for m in MEN}
    women = {w: random.sample(MEN, len(MEN)) for w in WOMEN}
    return men, women

preset_keys = sorted(BEST_PREFS.keys())
choice = st.sidebar.selectbox("好みパターン番号を選択", preset_keys)
col1, col2 = st.sidebar.columns(2)
if col1.button("プリセットで初期化"):
    reset_session_state(*BEST_PREFS[choice])
if col2.button("ランダムで初期化"):
    reset_session_state(*generate_random_prefs())

if "men_prefs" not in st.session_state:
    reset_session_state(*BEST_PREFS[preset_keys[0]])

st.subheader("現在の好み")
col1, col2 = st.columns(2)
with col1:
    for m in MEN:
        row = st.columns([0.3, 3])
        with row[0]:
            img_path = os.path.join(IMAGE_DIR, f"{m}.png")
            if os.path.exists(img_path):
                st.image(img_path, width=30)
        with row[1]:
            prefs = st.multiselect(f"{m} の好み", WOMEN, st.session_state.men_prefs[m], key=f"men_{m}")
            if len(prefs) == len(WOMEN):
                st.session_state.men_prefs[m] = prefs

with col2:
    for w in WOMEN:
        row = st.columns([0.3, 3])
        with row[0]:
            img_path = os.path.join(IMAGE_DIR, f"{w}.png")
            if os.path.exists(img_path):
                st.image(img_path, width=30)
        with row[1]:
            prefs = st.multiselect(f"{w} の好み", MEN, st.session_state.women_prefs[w], key=f"women_{w}")
            if len(prefs) == len(MEN):
                st.session_state.women_prefs[w] = prefs

def calculate_satisfaction(matching, men_prefs, women_prefs):
    if not matching:
        return 0, 0, 0, 0, 0

    man_score = sum(men_prefs[m].index(w) for m, w in matching)
    woman_score = sum(women_prefs[w].index(m) for m, w in matching)
    total_dissat = man_score + woman_score
    max_dissat = max(max(men_prefs[m].index(w), women_prefs[w].index(m)) for m, w in matching)
    n = len(matching)
    man_satis = 3 * n - man_score
    woman_satis = 3 * n - woman_score
    total_satis = man_satis + woman_satis
    min_satis = 3 - max_dissat
    diff = abs(man_satis - woman_satis)
    return total_satis, man_satis, woman_satis, diff, min_satis

def draw_state_with_proposals(matching, proposals, men_prefs, women_prefs):
    fig, ax = plt.subplots(figsize=(2.0, 1.0), dpi=800)
    ax.axis('off')
    spacing = 0.3
    x_men, x_women = 0.2, 0.8
    hoff, woff = 0.07, 0.07
    for i, m in enumerate(MEN):
        y = -i * spacing
        path = os.path.join(IMAGE_DIR, f"{m}.png")
        if os.path.exists(path):
            img = Image.open(path).resize((45, 36))
            ax.imshow(img, extent=(x_men-woff, x_men+woff, y-hoff, y+hoff), zorder=2)
        ax.text(x_men - 0.12, y, f"(0) {m}", fontsize=5, va='center', ha='right')
    for i, w in enumerate(WOMEN):
        y = -i * spacing
        path = os.path.join(IMAGE_DIR, f"{w}.png")
        if os.path.exists(path):
            img = Image.open(path).resize((45, 36))
            ax.imshow(img, extent=(x_women-woff, x_women+woff, y-hoff, y+hoff), zorder=2)
        ax.text(x_women + 0.12, y, f"(0) {w}", fontsize=5, va='center', ha='left')
    for m, w in st.session_state.engaged.items():
        y_m = -MEN.index(m) * spacing
        y_w = -WOMEN.index(w) * spacing
        ax.plot([x_men, x_women], [y_m, y_w], color='black', lw=0.5, zorder=1)
    if len(st.session_state.free_women) == 0:
        for m, w in matching:
            y_m = -MEN.index(m) * spacing
            y_w = -WOMEN.index(w) * spacing
            ax.plot([x_men, x_women], [y_m, y_w], color='blue', lw=1.0, zorder=1)
    ax.set_xlim(0, 1)
    ax.set_ylim(- (len(MEN)-1) * spacing - 0.3, 0.3)
    plt.subplots_adjust(top=1, bottom=0, left=0, right=1, hspace=0)
    return fig

if st.button("1ステップ進める") and st.session_state.free_women:
    woman = st.session_state.free_women[0]
    prefs = st.session_state.women_prefs[woman]
    for man in prefs:
        if man not in st.session_state.proposals[woman]:
            st.session_state.proposals[woman].append(man)
            st.session_state.received[man].append(woman)
            if man not in st.session_state.engaged:
                st.session_state.engaged[man] = woman
                st.session_state.free_women.pop(0)
            else:
                current = st.session_state.engaged[man]
                if st.session_state.men_prefs[man].index(woman) < st.session_state.men_prefs[man].index(current):
                    st.session_state.engaged[man] = woman
                    st.session_state.free_women.pop(0)
                    st.session_state.free_women.append(current)
            break

matching = [(m, w) for m, w in st.session_state.engaged.items()]
total, ms, ws, diff, min_satis = calculate_satisfaction(matching, st.session_state.men_prefs, st.session_state.women_prefs)
st.markdown(f"#### 満足度: 合計={total}, 男性側={ms}, 女性側={ws}, 差={diff}, 最小満足度={min_satis}")

col1, col2 = st.columns([1, 1])
with col1:
    st.pyplot(draw_state_with_proposals(matching, st.session_state.proposals,
                                        st.session_state.men_prefs, st.session_state.women_prefs))
