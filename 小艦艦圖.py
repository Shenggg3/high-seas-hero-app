import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import random

# --- 設定頁面配置 ---
st.set_page_config(
    page_title="AI 客製化重繪大師",
    page_icon="🎨",
    layout="centered"
)

# --- CSS 美化 ---
st.markdown("""
<style>
    .stApp { background-color: #f5f5f5; }
    .main-title {
        color: #333;
        text-align: center;
        font-family: 'Microsoft JhengHei', sans-serif;
        font-weight: bold;
    }
    .step-box {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    textarea {
        font-size: 1.1rem !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 初始化 Session State (用來暫存資料) ---
if 'analyzed_result' not in st.session_state:
    st.session_state.analyzed_result = ""
if 'final_image_url' not in st.session_state:
    st.session_state.final_image_url = None

# --- 側邊欄：設定 ---
st.sidebar.title("⚙️ 設定")
api_key = st.sidebar.text_input("1. 輸入 Google Gemini API Key", type="password")
st.sidebar.markdown("[取得 Gemini API Key](https://aistudio.google.com/app/apikey)")

# 自動偵測模型
model_list = []
if api_key:
    try:
        genai.configure(api_key=api_key)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                model_list.append(m.name)
    except:
        pass

selected_model = st.sidebar.selectbox("2. 選擇模型", model_list) if model_list else None

# --- 主程式區 ---
st.markdown("<h1 class='main-title'>🎨 AI 客製化重繪大師</h1>", unsafe_allow_html=True)
st.info("流程：上傳圖片 ➡️ AI 分析並撰寫中文描述 ➡️ 你編輯文字 ➡️ 生成新圖片")

# --- 步驟 1: 上傳與設定 ---
with st.container():
    st.markdown("### 1️⃣ 上傳與風格設定")
    uploaded_file = st.file_uploader("上傳參考圖片", type=["jpg", "jpeg", "png"])
    
    # 讓使用者輸入想要的風格，不再寫死
    user_style = st.text_input("想要什麼風格？(例如：賽博龐克、吉卜力動畫、小艦艦手遊風、油畫)", 
                               value="Supercell 手遊 3D 卡通風格")

    if uploaded_file and selected_model:
        image = Image.open(uploaded_file)
        st.image(image, caption='原始圖片', width=300)
        
        # 按鈕：分析圖片
        if st.button("🔍 開始分析圖片並產生提示詞"):
            try:
                model = genai.GenerativeModel(selected_model)
                with st.spinner("Gemini 正在用銳利的眼睛分析圖片細節..."):
                    
                    # 指令：請 Gemini 用繁體中文描述，並融入使用者風格
                    analysis_prompt = f"""
                    請扮演一位專業的 AI 繪圖詠唱師。
                    
                    **任務：**
                    觀察這張圖片，並結合使用者想要的風格：【{user_style}】，寫出一段詳細的圖像描述。
                    
                    **要求：**
                    1. 使用 **繁體中文**。
                    2. 詳細描述人物的動作、表情、特徵（保留原本的構圖）。
                    3. 詳細描述衣服和背景（根據【{user_style}】進行風格化改寫）。
                    4. 不要輸出多餘的廢話，直接給我可以用來生成圖片的描述段落。
                    """
                    
                    response = model.generate_content([analysis_prompt, image])
                    # 將結果存入 session_state，這樣網頁重新整理後文字還在
                    st.session_state.analyzed_result = response.text.strip()
                    # 清除之前的圖片結果
                    st.session_state.final_image_url = None 
                    
            except Exception as e:
                st.error(f"分析失敗：{e}")

# --- 步驟 2: 編輯提示詞 (只有當有分析結果時才顯示) ---
if st.session_state.analyzed_result:
    st.markdown("---")
    st.markdown("### 2️⃣ 編輯提示詞 (繁體中文)")
    st.markdown("Gemini 幫你寫好了描述，現在你可以**自由修改**！想加什麼細節直接打字。")
    
    # Text Area 讓使用者編輯，內容綁定 session_state
    user_edited_prompt = st.text_area(
        "確認你的生成指令：", 
        value=st.session_state.analyzed_result, 
        height=150
    )
    
    col1, col2 = st.columns([1, 2])
    with col1:
        generate_btn = st.button("✨ 確認並生成圖片")

    # --- 步驟 3: 翻譯並生成 ---
    if generate_btn:
        if not api_key:
            st.error("請檢查 API Key")
        else:
            try:
                model = genai.GenerativeModel(selected_model)
                with st.spinner("正在將中文指令轉譯給繪圖 AI (Flux)..."):
                    
                    # 再次呼叫 Gemini：翻譯官模式
                    # 因為目前的繪圖模型對英文理解最好，所以我們在後台偷轉成英文
                    translate_prompt = f"""
                    Act as a professional prompt translator.
                    Translate the following Traditional Chinese image description into a high-quality English prompt for AI Image Generator (Flux/Midjourney).
                    
                    **Chinese Description:**
                    "{user_edited_prompt}"
                    
                    **Requirements:**
                    - Enhance the prompt with keywords for high quality (e.g., 8k, best quality, detailed).
                    - Ensure the art style specified in the text is emphasized.
                    - Output ONLY the English prompt string.
                    """
                    
                    response_trans = model.generate_content(translate_prompt)
                    english_prompt = response_trans.text.strip()
                    
                with st.spinner("繪圖引擎啟動中..."):
                    # 呼叫 Pollinations.ai
                    encoded_prompt = urllib.parse.quote(english_prompt)
                    seed = random.randint(0, 99999)
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&nologo=true&model=flux"
                    
                    # 存入狀態
                    st.session_state.final_image_url = image_url
                    
            except Exception as e:
                st.error(f"生成失敗：{e}")

# --- 步驟 4: 顯示結果 ---
if st.session_state.final_image_url:
    st.markdown("---")
    st.markdown("### 3️⃣ 生成結果")
    st.success("🎉 完成！")
    st.image(st.session_state.final_image_url, caption="AI 重繪結果", use_container_width=True)
    
    # 讓使用者知道後台發生了什麼（選用）
    with st.expander("查看後台使用的英文咒語"):
        st.info("為了讓繪圖 AI 聽懂，我們將你的中文自動轉譯成了這段英文：")
        st.code(urllib.parse.unquote(encoded_prompt) if 'encoded_prompt' in locals() else "Prompt hidden")