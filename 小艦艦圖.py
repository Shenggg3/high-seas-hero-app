import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import random

# --- 設定頁面配置 ---
st.set_page_config(
    page_title="小艦艦超勇 - 嚴格構圖版",
    page_icon="⚓",
    layout="centered"
)

# --- CSS 美化 ---
st.markdown("""
<style>
    .stApp { background-color: #545d5e; }
    .title-text {
        color: #0277bd;
        text-align: center;
        font-family: 'Comic Sans MS', sans-serif;
        font-weight: bold;
        text-shadow: 2px 2px #4f4949;
    }
    .stButton>button {
        width: 100%;
        background-color: #ffca28;
        color: #000;
        font-weight: bold;
        border: none;
        padding: 10px;
        border-radius: 10px;
    }
    .stButton>button:hover {
        background-color: #ffc107;
    }
    .warning-text {
        color: #d32f2f;
        font-size: 0.85em;
        background-color: #ffebee;
        padding: 8px;
        border-radius: 5px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 主標題 ---
st.markdown("<h1 class='title-text'>⚓ 小艦艦超勇：嚴格構圖版 ⚓</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>專注還原動作與背景的風格轉換</p>", unsafe_allow_html=True)

# --- 側邊欄 ---
st.sidebar.title("⚙️ 系統設定")
api_key = st.sidebar.text_input("1. 請先輸入 Google Gemini API Key", type="password")
st.sidebar.markdown("[取得 Gemini API Key](https://aistudio.google.com/app/apikey)")

selected_model_name = None

# --- 載入模型列表 ---
if api_key:
    try:
        genai.configure(api_key=api_key)
        model_list = []
        with st.sidebar:
            with st.spinner("讀取可用模型..."):
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        model_list.append(m.name)
        
        if model_list:
            default_index = 0
            for i, name in enumerate(model_list):
                if "flash" in name and "1.5" in name:
                    default_index = i
                    break
            st.sidebar.success("✅ 連線成功")
            selected_model_name = st.sidebar.selectbox("2. 選擇模型", model_list, index=default_index)
        else:
            st.sidebar.error("無可用模型")
    except Exception as e:
        st.sidebar.error(f"連線錯誤：{e}")

# --- 圖片上傳區 ---
st.divider()
uploaded_file = st.file_uploader("3. 上傳照片", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption='原始照片', use_container_width=True)
    
    # 說明文字
    st.markdown("""
    <div class='warning-text'>
    <b>💡 原理說明：</b><br>
    此版本會命令 AI <b>「嚴格描述你的動作與背景細節」</b>，盡量讓生成的構圖與原圖一致。<br>
    但因為是「重新繪製」，細微角度仍可能會有差異。
    </div>
    """, unsafe_allow_html=True)

    if selected_model_name:
        if st.button('🚀 嚴格鎖定並變身！'):
            try:
                model = genai.GenerativeModel(selected_model_name)
                bar = st.progress(0, text=f"Gemini 正在掃描骨架與構圖...")

                # --- 1. 關鍵修改：命令 Gemini 成為「場景複製機」 ---
                prompt_instruction = """
                You are a strict scene describer for Image Reconstruction.
                
                **Goal:** 
                Write a prompt to recreate this EXACT image content but in a specific art style.
                
                **Strict Rules for Observation:**
                1.  **Composition:** Describe the exact camera angle (e.g., selfie, full body, low angle), framing, and subject position.
                2.  **Pose:** Describe the limbs, head tilt, and hand positions precisely (e.g., "right hand holding a cup", "arms crossed").
                3.  **Background:** Keep the background EXACTLY as it is in the photo (e.g., "office desk with computer", "street with cars"). DO NOT change the background to a pirate ship unless the user is already on a ship.
                4.  **Outfit:** Keep the person's outfit shape but stylize the texture to look like a "Naval Commander" uniform (add gold buttons/epaulets to existing clothes).
                
                **Target Art Style (Apply this filter over the scene):**
                "Supercell style, 3D cartoon render, vivid colors, clay material, cute stylized proportions."
                
                **Output:** 
                A highly detailed descriptive prompt that starts with the art style.
                """
                
                response = model.generate_content([prompt_instruction, image])
                final_prompt = response.text.strip()
                
                bar.progress(60, text="正在進行風格化重繪...")

                # --- 2. 繪圖設定 (Flux) ---
                # 這裡不再強制加入 "ocean background"，而是依賴 Gemini 對原圖背景的描述
                # 但加強風格關鍵字
                style_boost = "Supercell art style, 3D render, best quality"
                combined_prompt = f"{style_boost}, {final_prompt}"
                
                encoded_prompt = urllib.parse.quote(combined_prompt)
                seed = random.randint(0, 99999)
                
                # 使用 Flux 模型 (對構圖理解較好)
                image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&nologo=true&model=flux"
                
                bar.progress(100, text="完成！")
                
                st.success("🎉 生成完成！")
                st.image(image_url, caption="保留構圖的風格化結果", use_container_width=True)
                
                with st.expander("查看 AI 如何描述你的照片"):
                    st.text(final_prompt)

            except Exception as e:
                st.error(f"錯誤：{e}")
    else:
        st.warning("請先輸入 API Key")