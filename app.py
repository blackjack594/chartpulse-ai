import streamlit as st
import google.generativeai as genai
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

# ===== Page Config =====
st.set_page_config(
    page_title="ChartPulse.ai",
    page_icon="📈",
    layout="wide"
)

# ===== Custom CSS =====
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');

* {font-family: 'Cairo', sans-serif !important;}

[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0a0a1a, #0d1117);
}

.main-title {
    font-size: 3.5rem;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(90deg, #00ff88, #00ccff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtitle {
    text-align: center;
    color: #8b949e;
    margin-bottom: 30px;
}

.analysis-box {
    background: #161b22;
    border: 1px solid #00ff8844;
    border-radius: 15px;
    padding: 25px;
    margin: 20px 0;
}

.stButton > button {
    background: linear-gradient(90deg, #00ff88, #00ccff) !important;
    color: black !important;
    font-weight: bold !important;
    border-radius: 10px !important;
}

.report-text {
    background: #0d1117;
    padding: 20px;
    border-radius: 10px;
    border-left: 3px solid #00ff88;
    white-space: pre-wrap;
}
</style>
""", unsafe_allow_html=True)

# ===== Title =====
st.markdown("<h1 class='main-title'>📈 ChartPulse.ai</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>محلل الشارتات بالذكاء الاصطناعي</p>", unsafe_allow_html=True)

# ===== API Setup =====
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    api_ready = True
except:
    api_ready = False
    st.error("❌ مفتاح API غير موجود. أضفه في Settings → Secrets")

# ===== Upload =====
uploaded_file = st.file_uploader("📤 ارفع صورة الشارت", type=["png", "jpg", "jpeg", "webp"])

if uploaded_file:
    st.image(uploaded_file, caption="الشارت المرفوع", use_container_width=True)
    
    if st.button("🚀 ابدأ التحليل", type="primary", use_container_width=True):
        if not api_ready:
            st.error("❌ يرجى إضافة مفتاح API أولاً")
        else:
            with st.spinner("جاري التحليل..."):
                try:
                    image = Image.open(uploaded_file)
                    
                    prompt = """
أنت محلل أسواق مالية محترف. حلل هذا الشارت بدقة واكتب تقريراً بالعربية يتضمن:

1. الأصل المالي والإطار الزمني
2. الاتجاه العام (صاعد/هابط/عرضي)
3. مستويات الدعم والمقاومة
4. الأنماط الفنية الظاهرة
5. التوصية: شراء 🟢 / بيع 🔴 / انتظار 🟡
6. نقطة الدخول المقترحة
7. وقف الخسارة
8. الأهداف
9. نسبة النجاح المتوقعة

اكتب التقرير بشكل منظم واحترافي.
"""
                    
                    response = model.generate_content([prompt, image])
                    report = response.text
                    
                    st.success("✅ تم التحليل بنجاح!")
                    st.markdown("---")
                    st.markdown("## 📋 التقرير")
                    st.markdown(f"<div class='report-text'>{report}</div>", unsafe_allow_html=True)
                    
                    # Download
                    st.download_button(
                        label="📥 تحميل التقرير TXT",
                        data=report,
                        file_name=f"ChartPulse_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain"
                    )
                    
                except Exception as e:
                    st.error(f"❌ حدث خطأ: {str(e)}")
                    st.info("تأكد من أن مفتاح API صحيح وأن الصورة واضحة")

# ===== Footer =====
st.markdown("---")
st.markdown("<p style='text-align:center; color:#484f58;'>© 2025 ChartPulse.ai | Powered by Gemini AI</p>", unsafe_allow_html=True)
