import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import random

# --- 設定頁面配置 ---
st.set_page_config(
    page_title="AI 繪圖萬能變身器",
    page_icon="🎨",
    layout="centered"
)

# --- 初始化 Session State (這是記住你編輯內容的關鍵) ---
if 'analyzed_content' not in st.session_state:
    st.session_state.analyzed_content = ""
if 'step' not in st.session_state:
    st.session_state.step = 1  # 1: 上傳, 2: 編輯, 3: 完成

# --- CSS 美化 ---
st.markdown("""
<style>
    .stApp { background-color: #f5f5f5; }
    .title-text {
        color: #333;
        text-align: center;
        font-weight: bold;
    }
    .step-box {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 主標題 ---
st.markdown("<h1 class='title-text'>🎨 AI 照片萬能變身器</h1>", unsafe_allow_html=True)

# --- 側邊欄：設定 ---
st.sidebar.title("⚙️ 設定")
api_key = st.sidebar.text_input("輸入 Gemini API Key", type="password")
st.sidebar.markdown("[取得 Gemini API Key](https://aistudio.google.com/app/apikey)")

# 自動選取模型邏輯
selected_model_name = None
if api_key:
    try:
        genai.configure(api_key=api_key)
        model_list = []
        with st.sidebar:
            with st.spinner("連線中..."):
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        model_list.append(m.name)
        
        if model_list:
            # 優先找 flash
            idx = 0
            for i, name in enumerate(model_list):
                if "flash" in name and "1.5" in name:
                    idx = i
                    break
            st.sidebar.success("✅ 連線成功")
            selected_model_name = st.sidebar.selectbox("使用模型", model_list, index=idx)
    except Exception as e:
        st.sidebar.error(f"連線失敗: {e}")

# ==========================================
#  Step 1: 上傳與初步分析
# ==========================================
st.markdown("### 步驟 1: 上傳照片")
uploaded_file = st.file_uploader("上傳你要轉換的人物照片", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption='原始照片', use_container_width=True)
    
    # 只有當還沒分析過，或想重新分析時顯示按鈕
    if st.button("🔍 分析照片特徵 (產生中文描述)"):
        if not api_key or not selected_model_name:
            st.error("請先設定 API Key")
        else:
            try:
                model = genai.GenerativeModel(selected_model_name)
                with st.spinner("Gemini 正在用繁體中文描述這張照片..."):
                    # 指令：要求用繁體中文詳細描述
                    analyze_prompt = """
                    請擔任專業的視覺描述師。
                    請用「繁體中文」詳細描述這張圖片的人物外觀、動作、表情、穿著與背景。
                    重點放在視覺細節，不需要過多的文學修飾。
                    直接輸出描述段落即可。
                    """
                    response = model.generate_content([analyze_prompt, image])
                    st.session_state.analyzed_content = response.text
                    st.session_state.step = 2
                    st.rerun() # 重新整理頁面以進入下一步
            except Exception as e:
                st.error(f"分析錯誤: {e}")

# ==========================================
#  Step 2: 客製化編輯與風格選擇
# ==========================================
if st.session_state.step >= 2 and uploaded_file is not None:
    st.markdown("---")
    st.markdown("### 步驟 2: 編輯提示詞與風格")
    
    with st.container():
        st.info("👇 下面是 AI 分析出的結果，你可以自由修改！例如把「穿西裝」改成「穿太空衣」。")
        
        # 讓使用者編輯中文提示詞
        user_edited_prompt = st.text_area(
            "編輯畫面描述 (繁體中文):", 
            value=st.session_state.analyzed_content,
            height=150
        )
        
        # 風格選擇器
        style_options = {
            "小艦艦超勇 (Q版海戰)": "Supercell art style, 3D chibi character, cute, big head, mobile game asset, isometric view, vibrant colors, ocean background",
            "皮克斯動畫風 (Pixar)": "Pixar style, 3D animation render, disney style, cute, high detail, cinematic lighting",
            "日系動漫風 (Anime)": "Japanese anime style, Studio Ghibli style, 2D cell shading, detailed, vibrant",
            "賽博龐克 (Cyberpunk)": "Cyberpunk 2077 style, neon lights, futuristic city background, high tech armor, realistic 8k",
            "寫實攝影 (Realistic)": "Cinematic photography, 8k, photorealistic, shot on 35mm lens, highly detailed texture",
            "不指定 (僅依描述生成)": "High quality, masterpiece"
        }
        
        selected_style_name = st.selectbox("選擇畫風模板:", list(style_options.keys()))
        
        # 如果使用者想自訂風格指令
        custom_style = st.text_input("或者輸入自訂風格關鍵字 (英文佳，例如: Watercolor style):")

        # 生成按鈕
        if st.button("✨ 確認並生成圖片"):
            if not api_key:
                st.error("API Key 遺失，請重新輸入")
            else:
                try:
                    # 準備最終的風格字串
                    final_style_prompt = custom_style if custom_style else style_options[selected_style_name]
                    
                    model = genai.GenerativeModel(selected_model_name)
                    
                    with st.spinner("正在翻譯並將你的創意轉化為圖像咒語..."):
                        # 這是關鍵步驟：把使用者的「中文描述」+「風格」轉譯成「英文繪圖 Prompt」
                        # 因為繪圖模型通常對英文的理解力遠高於中文
                        translation_prompt = f"""
                        You are an expert AI Prompt Engineer for Flux/Midjourney.
                        
                        **Input Description (Traditional Chinese):** 
                        "{user_edited_prompt}"
                        
                        **Target Art Style:**
                        "{final_style_prompt}"
                        
                        **Task:**
                        1. Translate the Chinese description into detailed English.
                        2. Combine it with the Target Art Style.
                        3. Ensure the prompt describes the visual content accurately based on the input.
                        
                        **Output:** 
                        Return ONLY the final English prompt string.
                        """
                        
                        response_prompt = model.generate_content(translation_prompt)
                        english_prompt = response_prompt.text.strip()
                        
                    # 呼叫繪圖 API
                    with st.spinner("正在繪製圖片中... (約需 5-10 秒)"):
                        encoded_prompt = urllib.parse.quote(english_prompt)
                        seed = random.randint(0, 99999)
                        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&nologo=true&model=flux"
                        
                        st.success("🎉 生成完成！")
                        st.image(image_url, caption=f"風格: {selected_style_name}", use_container_width=True)
                        
                        with st.expander("查看 AI 使用的英文咒語"):
                            st.code(english_prompt)
                            
                except Exception as e:
                    st.error(f"生成失敗: {e}")

# 頁尾重置按鈕
if st.session_state.step >= 2:
    st.markdown("---")
    if st.button("🔄 重新開始 (清除所有設定)"):
        st.session_state.analyzed_content = ""
        st.session_state.step = 1
        st.rerun()