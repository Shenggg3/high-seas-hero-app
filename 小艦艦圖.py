import streamlit as st
import google.generativeai as genai
import urllib.parse
import random
from PIL import Image
import datetime

# ==========================================
# 1. 頁面配置與 CSS
# ==========================================
st.set_page_config(
    page_title="全球遊戲廣告素材指揮官",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* 全局深色主題 */
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    
    /* 標題特效 */
    .title-text { 
        color: #A855F7; 
        text-align: center; 
        font-weight: 800; 
        letter-spacing: 2px; 
        font-size: 2.5em; 
        text-shadow: 0 0 15px rgba(168, 85, 247, 0.4); 
    }
    .subtitle { text-align: center; color: #94A3B8; margin-bottom: 20px; }

    /* 場景卡片 */
    .scene-card { 
        background-color: #1E293B; 
        border: 1px solid #334155; 
        border-radius: 12px; 
        padding: 20px; 
        margin-bottom: 25px;
        border-left: 6px solid #A855F7; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    
    /* 聲音標籤 */
    .audio-vo { color: #FACC15; font-weight: bold; } 
    .audio-dialogue { color: #C084FC; font-weight: bold; }
    .audio-sfx { color: #F87171; font-weight: bold; font-size: 0.9em; }
    
    /* 影片指令區 */
    .video-prompt-box {
        background-color: #020617;
        border: 1px dashed #2DD4BF;
        padding: 12px;
        border-radius: 6px;
        font-family: 'Courier New', monospace;
        color: #2DD4BF;
        font-size: 0.85em;
        margin-top: 10px;
    }
    
    /* 自訂指令區塊 (新功能) */
    .custom-note-box {
        border: 2px solid #A855F7;
        border-radius: 8px;
        padding: 5px;
        margin-top: 10px;
        background-color: #1e1b4b;
    }
</style>
""", unsafe_allow_html=True)

# Session State
if 'fetched_models' not in st.session_state: st.session_state.fetched_models = []
if 'is_connected' not in st.session_state: st.session_state.is_connected = False

# ==========================================
# 2. 側邊欄：設定
# ==========================================
with st.sidebar:
    st.title("⚙️ 系統設定")
    api_key = st.text_input("🔑 Google API Key", type="password")
    
    if st.button("🔗 連線系統"):
        if not api_key:
            st.error("請輸入 API Key")
        else:
            try:
                genai.configure(api_key=api_key)
                models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                if models:
                    st.session_state.fetched_models = models
                    st.session_state.is_connected = True
                    st.success(f"✅ 連線成功")
                else:
                    st.error("無可用模型")
            except Exception as e:
                st.error(f"錯誤: {e}")
    
    st.divider()
    
    selected_model = None
    if st.session_state.is_connected:
        default_idx = 0
        for i, m in enumerate(st.session_state.fetched_models):
            if "flash" in m and "1.5" in m: default_idx = i; break
        selected_model = st.selectbox("🧠 選用模型", st.session_state.fetched_models, index=default_idx)

# ==========================================
# 3. 主畫面：參數設定
# ==========================================
st.markdown("<h1 class='title-text'>🌍 全球遊戲廣告素材指揮官</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>導演特別指示 • Veo3/Sora 優化 • 精準受眾鎖定</p>", unsafe_allow_html=True)

with st.container():
    # --- Row 1: 基礎遊戲資訊 ---
    c1, c2 = st.columns([1, 1])
    with c1:
        game_name = st.text_input("🎮 遊戲名稱", placeholder="Ex: 絕區零")
    with c2:
        platform = st.selectbox("🕹️ 遊戲平台", ["手機遊戲 (Mobile)", "PC/Steam", "主機 (Console)", "網頁遊戲"])

    st.markdown("---")

    # --- Row 2: 地區與風格 ---
    c3, c4, c5 = st.columns(3)
    with c3:
        target_region = st.selectbox("🌐 投放地區 (語言)", [
            "台灣 (Taiwan) - 繁體中文", "日本 (Japan) - 日文", "美國 (USA) - 英文", 
            "韓國 (Korea) - 韓文", "中國大陸 (China) - 簡體中文", "東南亞 (SEA) - 英文/當地語"
        ])
    with c4:
        ad_tone = st.selectbox("🎭 影片調性/風格", [
            "🤪 搞笑/諧音梗 (Funny)", "🔥 熱血/中二感 (Epic)", "😱 懸疑/驚悚 (Thriller)", 
            "😭 感人/情感共鳴 (Emotional)", "😎 專業/硬核介紹 (Professional)", "🤑 誇張/暴發戶感 (Aggressive)"
        ]) 
    with c5:
        ad_format = st.selectbox("📢 廣告腳本形式", [
            "戰力飆升 (Lv1 vs Lv100)", "失敗挑戰 (Fail Run)", "CG 動畫大片 (Cinematic)", 
            "實機試玩 (Gameplay)", "福利放送 (Gacha/Freebies)", "真人情境劇 (Live Action Skit)"
        ])

    # --- Row 3: 精準受眾儀表板 ---
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🎯 受眾精準鎖定 (Targeting Details)", expanded=False):
        d1, d2, d3, d4 = st.columns(4)
        with d1: ta_gender = st.selectbox("👤 性別傾向", ["不限", "男性為主", "女性為主"])
        with d2: ta_age = st.slider("🎂 年齡層", 12, 60, (18, 35))
        with d3: ta_time = st.selectbox("⏰ 投放時段", ["通勤(早)", "午休(中)", "下班(晚)", "深夜", "不限"])
        with d4: ta_holiday = st.text_input("🎉 節慶/節氣", placeholder="Ex: 春節") or "平日"

    # --- Row 4: 其他 ---
    c6, c7 = st.columns([1, 1])
    with c6:
        duration = st.select_slider("⏱️ 廣告時長", options=[15, 30, 45, 60], value=30)
    with c7:
        uploaded_file = st.file_uploader("📸 參考圖 (選填)", type=["jpg", "png"])

    # --- [NEW] Row 5: 導演特別指示 ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📝 導演特別指示 (Custom Director's Note)")
    st.caption("在這裡輸入您的具體劇情要求、指定台詞或創意細節。AI 將會 **優先執行** 這裡的指令。")
    
    # 使用 container 來增加醒目度
    with st.container():
        st.markdown('<div class="custom-note-box">', unsafe_allow_html=True)
        custom_instructions = st.text_area(
            label="請輸入您的客製化需求 (選填)", 
            height=100,
            placeholder="例如：我要一個劇情是主角在路上撿到一把劍，然後突然變成魔王。旁白要很激動地說『這也太爽了吧！』...",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 4. 生成核心
# ==========================================
if st.button("🚀 執行導演指令 (生成腳本)"):
    if not st.session_state.is_connected or not game_name:
        st.warning("請先連線並輸入遊戲名稱")
    else:
        model = genai.GenerativeModel(selected_model)
        
        # 視覺分析
        visual_info = ""
        if uploaded_file:
            img = Image.open(uploaded_file)
            with st.spinner("正在分析參考圖..."):
                res = model.generate_content(["Describe the visual style.", img])
                visual_info = f"Visual Ref: {res.text}"

        # 構建 Prompt (加入 Custom Note)
        prompt = f"""
        You are a World-Class Game Ad Director.
        
        **Configuration:**
        - Game: {game_name} ({platform})
        - Region: {target_region}
        - Tone: {ad_tone}
        - Format: {ad_format}
        - Target: {ta_gender}, Age {ta_age[0]}-{ta_age[1]}
        - Context: Time: {ta_time}, Holiday: {ta_holiday}
        - Duration: {duration}s
        - {visual_info}
        
        **CRITICAL - DIRECTOR'S CUSTOM NOTE:**
        "{custom_instructions}"
        (Prioritize this note above all other settings if there is a conflict. Implement these specific plot points or requests exactly.)
        
        **Task:**
        1. **Strategy:** Analyze the approach.
        2. **Script (The Trinity Audio System):**
           * **Voiceover (Narrator):** Native Language.
           * **Dialogue (Characters):** Native Language. Format: "Character: Line".
           * **SFX:** Sound effects.
           * **Visuals:** Traditional Chinese descriptions.
        3. **Video Prompt (Next-Gen):** English prompts for Veo3/Sora/Kling.
        
        **Output Format (Separator '|||'):**
        
        [STRATEGY]
        策略與創意: [Traditional Chinese analysis]
        |||
        Scene 1
        Time: [Start-End]s
        Visual: [Traditional Chinese visual desc]
        Voiceover: [Native Language Narrator (or "None")]
        Dialogue: [Native Language Dialogue (or "None")]
        SFX: [Sound effect desc]
        Text: [Native Language Overlay]
        Video Prompt: [English detailed prompt]
        |||
        (Repeat)
        """

        with st.spinner("🧠 正在整合導演指示與AI創意..."):
            try:
                response = model.generate_content(prompt)
                full_text = response.text
                
                # 解析
                if "[STRATEGY]" in full_text:
                    parts = full_text.split("|||")
                    strategy = parts[0].replace("[STRATEGY]", "").strip()
                    scenes = parts[1:]
                else:
                    strategy = "無策略分析"
                    scenes = full_text.split("|||")
                
                # 顯示策略
                st.markdown(f"""
                <div class="strategy-box" style="background-color:#1e293b; padding:20px; border-radius:10px; border-top:4px solid #FACC15; margin-bottom:25px;">
                    <h3 style="color:#FACC15; margin:0;">🧠 綜合策略分析</h3>
                    <pre style="white-space: pre-wrap; color: #cbd5e1; font-family: sans-serif;">{strategy}</pre>
                </div>
                """, unsafe_allow_html=True)
                
                st.subheader(f"🎬 {game_name} - 客製化腳本")
                
                for i, scene in enumerate(scenes):
                    if len(scene.strip()) < 10: continue
                    
                    lines = scene.strip().split('\n')
                    data = {"Time": "N/A", "Visual": "無", "Voiceover": "無", "Dialogue": "無", "SFX": "無", "Text": "無", "Video Prompt": ""}
                    for line in lines:
                        for k in data.keys():
                            if f"{k}:" in line: data[k] = line.split(":", 1)[1].strip()
                    
                    with st.container():
                        c_text, c_img = st.columns([3, 2])
                        with c_text:
                            # 聲音分軌
                            audio_html = ""
                            if data['Voiceover'] not in ["None", "無"]:
                                audio_html += f'<span class="audio-vo">🗣️ 旁白:</span> {data["Voiceover"]}<br>'
                            if data['Dialogue'] not in ["None", "無"]:
                                audio_html += f'<span class="audio-dialogue">💬 對話:</span> {data["Dialogue"]}<br>'
                            
                            st.markdown(f"""
                            <div class="scene-card">
                                <span class="time-badge">Scene {i+1} | {data['Time']}</span>
                                <br><br>
                                <b>🎥 畫面:</b> {data['Visual']}<br>
                                <b>📝 壓字:</b> {data['Text']}<br>
                                <hr style="border-color: #334155;">
                                {audio_html}
                                <span class="audio-sfx">🔊 音效:</span> {data['SFX']}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("**👇 Veo3 / Sora / Kling 指令:**")
                            st.markdown(f'<div class="video-prompt-box">{data["Video Prompt"]}</div>', unsafe_allow_html=True)
                        
                        with c_img:
                            if data['Video Prompt']:
                                w, h, ratio = (576, 1024, "9:16") if "手機" in platform or "Mobile" in platform else (1024, 576, "16:9")
                                clean_p = urllib.parse.quote(f"{data['Video Prompt']}, {game_name} style, cinematic lighting, 8k")
                                seed = random.randint(0, 9999)
                                url = f"https://image.pollinations.ai/prompt/{clean_p}?width={w}&height={h}&seed={seed}&nologo=true&model=flux"
                                st.image(url, caption=f"視覺示意 ({ratio})", use_container_width=True)

                st.success("🎉 客製化腳本製作完成！")

            except Exception as e:
                st.error(f"生成錯誤: {e}")