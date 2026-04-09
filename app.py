import streamlit as st
import openai
import anthropic
import google.generativeai as genai
from datetime import datetime
import base64
from fpdf import FPDF
import json
import io
from PIL import Image

# ===== Page Config =====
st.set_page_config(
    page_title="ChartPulse.ai - AI Chart Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== Custom CSS =====
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800;900&display=swap');

* {font-family: 'Cairo', sans-serif !important;}

[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0a0a1a 0%, #0d1117 25%, #161b22 50%, #0d1117 75%, #0a0a1a 100%);
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117, #161b22);
    border-right: 1px solid #00ff8833;
}

.main-title {
    font-size: 4rem;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(135deg, #00ff88, #00ccff, #0088ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
    animation: glow 3s ease-in-out infinite;
}

@keyframes glow {
    0%, 100% {filter: brightness(1);}
    50% {filter: brightness(1.3);}
}

.subtitle {
    text-align: center;
    color: #8b949e;
    font-size: 1.2rem;
    margin-top: -10px;
    margin-bottom: 30px;
}

.analysis-card {
    background: linear-gradient(135deg, #161b22, #1c2333);
    border: 1px solid #00ff8844;
    border-radius: 20px;
    padding: 30px;
    margin: 15px 0;
    box-shadow: 0 0 30px rgba(0, 255, 136, 0.1);
}

.metric-card {
    background: linear-gradient(135deg, #1a1f2e, #252d3d);
    border: 1px solid #00ff8833;
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    margin: 5px;
}

.metric-value {
    font-size: 2rem;
    font-weight: 800;
    color: #00ff88;
}

.metric-label {
    color: #8b949e;
    font-size: 0.9rem;
}

.buy-signal {
    background: linear-gradient(135deg, #0a2e1a, #1a4a2e);
    border: 2px solid #00ff88;
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    font-size: 1.5rem;
    color: #00ff88;
    font-weight: 800;
}

.sell-signal {
    background: linear-gradient(135deg, #2e0a0a, #4a1a1a);
    border: 2px solid #ff4444;
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    font-size: 1.5rem;
    color: #ff4444;
    font-weight: 800;
}

.wait-signal {
    background: linear-gradient(135deg, #2e2a0a, #4a441a);
    border: 2px solid #ffaa00;
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    font-size: 1.5rem;
    color: #ffaa00;
    font-weight: 800;
}

.stButton > button {
    background: linear-gradient(135deg, #00ff88, #00ccff) !important;
    color: #000 !important;
    font-weight: 800 !important;
    font-size: 1.2rem !important;
    border: none !important;
    border-radius: 15px !important;
    padding: 15px 40px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 0 20px rgba(0,255,136,0.3) !important;
}

.stButton > button:hover {
    transform: scale(1.05) !important;
    box-shadow: 0 0 40px rgba(0,255,136,0.5) !important;
}

.report-section {
    background: #0d111788;
    border-left: 4px solid #00ff88;
    padding: 15px 20px;
    margin: 10px 0;
    border-radius: 0 10px 10px 0;
    color: #e6edf3;
}

.feature-badge {
    display: inline-block;
    background: #00ff8822;
    color: #00ff88;
    padding: 5px 15px;
    border-radius: 20px;
    font-size: 0.8rem;
    margin: 3px;
    border: 1px solid #00ff8844;
}

.powered-by {
    text-align: center;
    color: #484f58;
    font-size: 0.8rem;
    margin-top: 50px;
    padding: 20px;
    border-top: 1px solid #21262d;
}

.stFileUploader {
    border: 2px dashed #00ff8844 !important;
    border-radius: 20px !important;
    padding: 20px !important;
}

div[data-testid="stFileUploader"] {
    background: #161b2244;
    border-radius: 20px;
    padding: 10px;
}

.history-item {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
    cursor: pointer;
    transition: all 0.3s;
}

.history-item:hover {
    border-color: #00ff88;
    box-shadow: 0 0 15px rgba(0,255,136,0.2);
}

h1, h2, h3, h4, h5, h6, p, span, div, label {
    color: #e6edf3 !important;
}
</style>
""", unsafe_allow_html=True)

# ===== Session State =====
if 'analyses' not in st.session_state:
    st.session_state.analyses = []
if 'current_report' not in st.session_state:
    st.session_state.current_report = None
if 'analysis_count' not in st.session_state:
    st.session_state.analysis_count = 0

# ===== API Setup =====
def setup_apis():
    apis = {}
    try:
        apis['openai'] = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    except:
        apis['openai'] = None
    try:
        apis['claude'] = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    except:
        apis['claude'] = None
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        apis['gemini'] = genai.GenerativeModel('gemini-1.5-pro')
    except:
        apis['gemini'] = None
    return apis

apis = setup_apis()

# ===== Analysis Prompt =====
MASTER_PROMPT = """
أنت أعظم محلل أسواق مالية في العالم، خبرة 30 سنة في جميع الأسواق.
حلل هذا الشارت بدقة متناهية باستخدام جميع مدارس التحليل التالية:

📊 التحليل الفني الكلاسيكي:
- خطوط الدعم والمقاومة الرئيسية والفرعية
- خطوط الاتجاه (Trendlines)
- القنوات السعرية (Channels)
- الأنماط الكلاسيكية (Head & Shoulders, Double Top/Bottom, Triangles, Flags, Wedges...)
- المتوسطات المتحركة (MA, EMA)

📐 فيبوناتشي:
- مستويات التصحيح (23.6%, 38.2%, 50%, 61.8%, 78.6%)
- مستويات الامتداد
- FIB Time Zones

🌊 موجات إليوت:
- تحديد الموجة الحالية (1-5 أو A-B-C)
- توقع الموجة القادمة
- درجة الموجة

🦋 الهارمونيك:
- أنماط Gartley, Butterfly, Bat, Crab, Shark, Cypher
- نقاط الانعكاس المحتملة

☁️ إيشيموكو:
- Tenkan-sen, Kijun-sen
- Senkou Span A & B
- Chikou Span
- موقع السعر من السحابة

💰 Smart Money Concepts (SMC/ICT):
- Order Blocks (OB)
- Fair Value Gaps (FVG)
- Liquidity Sweeps
- Break of Structure (BOS)
- Change of Character (CHoCH)
- Premium/Discount Zones

📊 Volume Analysis:
- Volume Profile
- VWAP
- Volume Divergence

🔮 المؤشرات الفنية (إذا ظاهرة):
- RSI
- MACD
- Stochastic
- Bollinger Bands
- ATR

اكتب التقرير بالشكل التالي بالعربية الفصحى:

═══════════════════════════════
📈 تقرير ChartPulse.ai الشامل
═══════════════════════════════

🔍 معلومات عامة:
- الأصل المالي: [حدده من الشارت]
- الإطار الزمني: [حدده من الشارت]
- السعر الحالي التقريبي: [حدده]
- الاتجاه العام: [صاعد/هابط/عرضي]
- قوة الاتجاه: [ضعيف/متوسط/قوي/قوي جداً]

📊 التحليل الفني الكلاسيكي:
[تحليل مفصل]

🌊 تحليل موجات إليوت:
[تحليل مفصل]

💰 تحليل Smart Money (SMC):
[تحليل مفصل]

🦋 تحليل الهارمونيك:
[تحليل مفصل]

📐 مستويات فيبوناتشي:
[تحليل مفصل]

☁️ تحليل إيشيموكو:
[تحليل مفصل]

📊 تحليل الحجم:
[تحليل مفصل]

═══════════════════════════════
🎯 التوصية النهائية
═══════════════════════════════

📌 التوصية: [🟢 شراء / 🔴 بيع / 🟡 انتظار]
📍 نقطة الدخول: [السعر]
🎯 الهدف الأول: [السعر]
🎯 الهدف الثاني: [السعر]
🎯 الهدف الثالث: [السعر]
🛑 وقف الخسارة: [السعر]
📊 نسبة المخاطرة للعائد: [النسبة]
💯 نسبة النجاح المتوقعة: [النسبة]%
⏰ المدة المتوقعة: [الفترة]

═══════════════════════════════
⚠️ ملاحظات مهمة
═══════════════════════════════
[ملاحظات وتحذيرات]

═══════════════════════════════
🔄 سيناريوهات بديلة
═══════════════════════════════
السيناريو البديل 1: [وصف]
السيناريو البديل 2: [وصف]
"""

# ===== Analysis Functions =====
def analyze_with_gpt4o(client, image_base64):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": MASTER_PROMPT},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                        "detail": "high"
                    }}
                ]
            }],
            max_tokens=4000,
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"خطأ GPT-4o: {str(e)}"

def analyze_with_claude(client, image_base64):
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_base64
                        }
                    },
                    {"type": "text", "text": MASTER_PROMPT}
                ]
            }]
        )
        return response.content[0].text
    except Exception as e:
        return f"خطأ Claude: {str(e)}"

def analyze_with_gemini(model, image_bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes))
        response = model.generate_content(
            [MASTER_PROMPT, image],
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=4000
            )
        )
        return response.text
    except Exception as e:
        return f"خطأ Gemini: {str(e)}"

def merge_analyses(client, analyses):
    merge_prompt = f"""
أنت خبير دمج تحليلات الأسواق المالية.
لديك التحليلات التالية من أقوى 3 نماذج ذكاء اصطناعي:

{'='*50}
تحليل النموذج الأول:
{'='*50}
{analyses[0] if len(analyses) > 0 else 'غير متوفر'}

{'='*50}
تحليل النموذج الثاني:
{'='*50}
{analyses[1] if len(analyses) > 1 else 'غير متوفر'}

{'='*50}
تحليل النموذج الثالث:
{'='*50}
{analyses[2] if len(analyses) > 2 else 'غير متوفر'}

ادمج هذه التحليلات في تقرير واحد شامل ومتماسك بنفس التنسيق المطلوب.
ركز على النقاط التي اتفقت عليها النماذج الثلاثة.
إذا اختلفت النماذج، اذكر ذلك واعطِ الترجيح الأقوى.
اجعل التقرير النهائي احترافياً جداً ومفصلاً.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": merge_prompt}],
            max_tokens=5000,
            temperature=0.1
        )
        return response.choices[0].message.content
    except:
        return analyses[0] if analyses else "لم يتم التحليل"

def create_pdf_report(report_text, image_bytes=None):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Header
    pdf.set_fill_color(13, 17, 23)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(0, 255, 136)
    pdf.cell(0, 20, 'ChartPulse.ai', ln=True, align='C')
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(139, 148, 158)
    pdf.cell(0, 10, f'Analysis Report - {datetime.now().strftime("%Y-%m-%d %H:%M")}', ln=True, align='C')
    pdf.ln(10)

    # Chart Image
    if image_bytes:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img_path = "/tmp/chart_temp.png"
            img.save(img_path)
            pdf.image(img_path, x=10, w=190)
            pdf.ln(10)
        except:
            pass

    # Report Content
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', '', 10)

    for line in report_text.split('\n'):
        clean_line = line.encode('latin-1', 'replace').decode('latin-1')
        if any(c in line for c in ['===', '---']):
            pdf.set_draw_color(0, 255, 136)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
        elif line.strip().startswith(('📈', '🔍', '📊', '🌊', '💰', '🦋', '📐', '☁️', '🎯', '⚠️', '🔄')):
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(0, 150, 100)
            pdf.multi_cell(0, 7, clean_line)
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
        elif line.strip().startswith(('📌', '📍', '🎯', '🛑', '💯', '⏰')):
            pdf.set_font('Helvetica', 'B', 11)
            pdf.set_text_color(0, 100, 200)
            pdf.multi_cell(0, 7, clean_line)
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.multi_cell(0, 6, clean_line)

    # Footer
    pdf.ln(20)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, 'Powered by ChartPulse.ai - AI-Powered Chart Analysis', ln=True, align='C')
    pdf.cell(0, 5, 'This is not financial advice. Always do your own research.', ln=True, align='C')

    return pdf.output(dest='S')

# ===== Sidebar =====
with st.sidebar:
    st.markdown("### ⚙️ إعدادات التحليل")

    analysis_mode = st.selectbox(
        "وضع التحليل",
        ["🔥 هجين (3 نماذج AI)", "⚡ GPT-4o فقط", "🧠 Claude فقط", "💎 Gemini فقط"],
        index=0
    )

    st.markdown("---")

    market_type = st.selectbox(
        "نوع السوق",
        ["🔄 تحديد تلقائي", "📈 فوركس", "₿ كريبتو", "📊 أسهم", "🥇 سلع", "📉 مؤشرات"],
        index=0
    )

    timeframe = st.selectbox(
        "الإطار الزمني",
        ["🔄 تحديد تلقائي", "1 دقيقة", "5 دقائق", "15 دقيقة", "30 دقيقة",
         "1 ساعة", "4 ساعات", "يومي", "أسبوعي", "شهري"],
        index=0
    )

    st.markdown("---")
    st.markdown("### 📚 التحليلات السابقة")

    if st.session_state.analyses:
        for i, analysis in enumerate(reversed(st.session_state.analyses[-10:])):
            with st.expander(f"📊 تحليل #{len(st.session_state.analyses)-i} - {analysis['time']}"):
                st.write(analysis['summary'][:200] + "...")
                if st.button(f"عرض التقرير الكامل", key=f"view_{i}"):
                    st.session_state.current_report = analysis['report']
    else:
        st.info("لا توجد تحليلات سابقة بعد")

    st.markdown("---")
    st.markdown(f"""
    ### 📊 إحصائيات
    - إجمالي التحليلات: **{st.session_state.analysis_count}**
    - النماذج النشطة: **{sum([1 for k,v in apis.items() if v is not None])}**/3
    """)

# ===== Main Content =====
st.markdown("<h1 class='main-title'>📈 ChartPulse.ai</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>أقوى محلل شارتات بالذكاء الاصطناعي في العالم | يدمج 3 نماذج AI معاً</p>", unsafe_allow_html=True)

# Features
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("""
    <div class='metric-card'>
        <div class='metric-value'>3</div>
        <div class='metric-label'>نماذج AI مدمجة</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class='metric-card'>
        <div class='metric-value'>10+</div>
        <div class='metric-label'>مدرسة تحليل</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class='metric-card'>
        <div class='metric-value'>PDF</div>
        <div class='metric-label'>تقرير احترافي</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown("""
    <div class='metric-card'>
        <div class='metric-value'>∞</div>
        <div class='metric-label'>حفظ التحليلات</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Upload Section
st.markdown("### 📤 ارفع صورة الشارت")

uploaded_file = st.file_uploader(
    "اسحب الصورة هنا أو اضغط للاختيار",
    type=["png", "jpg", "jpeg", "webp"],
    help="يدعم PNG, JPG, JPEG, WEBP - أقصى حجم 200MB"
)

if uploaded_file:
    col_img, col_info = st.columns([2, 1])

    with col_img:
        st.image(uploaded_file, caption="📊 الشارت المرفوع", use_container_width=True)

    with col_info:
        st.markdown(f"""
        <div class='metric-card'>
            <p>📁 <strong>{uploaded_file.name}</strong></p>
            <p>📏 الحجم: {uploaded_file.size / 1024:.1f} KB</p>
            <p>🖼️ النوع: {uploaded_file.type}</p>
            <p>⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='metric-card' style='margin-top:10px;'>
            <p>🔧 <strong>الإعدادات:</strong></p>
            <p>الوضع: {analysis_mode}</p>
            <p>السوق: {market_type}</p>
            <p>الفريم: {timeframe}</p>
        </div>
        """, unsafe_allow_html=True)

    if st.button("🚀 ابدأ التحليل الشامل الآن", type="primary", use_container_width=True):

        image_bytes = uploaded_file.getvalue()
        base64_image = base64.b64encode(image_bytes).decode()

        analyses_results = []
        progress_bar = st.progress(0)
        status = st.empty()

        # GPT-4o
        if apis['openai'] and analysis_mode in ["🔥 هجين (3 نماذج AI)", "⚡ GPT-4o فقط"]:
            status.info("🤖 جاري التحليل بواسطة GPT-4o Vision...")
            result = analyze_with_gpt4o(apis['openai'], base64_image)
            analyses_results.append(result)
            progress_bar.progress(33)

        # Claude
        if apis['claude'] and analysis_mode in ["🔥 هجين (3 نماذج AI)", "🧠 Claude فقط"]:
            status.info("🧠 جاري التحليل بواسطة Claude 3.5 Sonnet...")
            result = analyze_with_claude(apis['claude'], base64_image)
            analyses_results.append(result)
            progress_bar.progress(66)

        # Gemini
        if apis['gemini'] and analysis_mode in ["🔥 هجين (3 نماذج AI)", "💎 Gemini فقط"]:
            status.info("💎 جاري التحليل بواسطة Gemini 1.5 Pro...")
            result = analyze_with_gemini(apis['gemini'], image_bytes)
            analyses_results.append(result)
            progress_bar.progress(90)

        # Merge
        if len(analyses_results) > 1 and apis['openai']:
            status.info("🔄 جاري دمج التحليلات في تقرير واحد شامل...")
            final_report = merge_analyses(apis['openai'], analyses_results)
        elif analyses_results:
            final_report = analyses_results[0]
        else:
            final_report = "❌ لم يتم العثور على أي API Key فعال. يرجى إضافة مفاتيح API في الإعدادات."

        progress_bar.progress(100)
        status.empty()

        # Save
        st.session_state.analysis_count += 1
        analysis_record = {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'report': final_report,
            'summary': final_report[:300],
            'image_name': uploaded_file.name,
            'mode': analysis_mode,
            'market': market_type,
            'timeframe': timeframe
        }
        st.session_state.analyses.append(analysis_record)
        st.session_state.current_report = final_report

        # Display
        st.success(f"✅ تم التحليل بنجاح! (تم استخدام {len(analyses_results)} نموذج AI)")

        st.markdown("---")
        st.markdown("## 📋 التقرير الشامل")

        st.markdown(f"<div class='analysis-card'>{final_report}</div>", unsafe_allow_html=True)

        st.markdown("---")

        # Actions
        col_pdf, col_copy, col_new = st.columns(3)

        with col_pdf:
            pdf_bytes = create_pdf_report(final_report, image_bytes)
            st.download_button(
                label="📥 تحميل التقرير PDF",
                data=pdf_bytes,
                file_name=f"ChartPulse_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        with col_copy:
            st.download_button(
                label="📋 تحميل كنص",
                data=final_report,
                file_name=f"ChartPulse_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )

        with col_new:
            if st.button("🔄 تحليل جديد", use_container_width=True):
                st.rerun()

# Show saved report
elif st.session_state.current_report:
    st.markdown("## 📋 آخر تقرير تم حفظه")
    st.markdown(f"<div class='analysis-card'>{st.session_state.current_report}</div>", unsafe_allow_html=True)

# Welcome
else:
    st.markdown("""
    <div class='analysis-card' style='text-align:center; padding:50px;'>
        <h2 style='color:#00ff88 !important;'>👋 مرحباً بك في ChartPulse.ai</h2>
        <p style='font-size:1.2rem; color:#8b949e !important;'>
            ارفع صورة من أي شارت (فوركس، كريبتو، أسهم، سلع، مؤشرات)<br>
            وسيقوم الذكاء الاصطناعي بتحليلها بجميع مدارس التحليل<br>
            وإخراج تقرير شامل مع توصية واضحة
        </p>
        <br>
        <div>
            <span class='feature-badge'>SMC / ICT</span>
            <span class='feature-badge'>Elliott Wave</span>
            <span class='feature-badge'>Harmonic</span>
            <span class='feature-badge'>Fibonacci</span>
            <span class='feature-badge'>Ichimoku</span>
            <span class='feature-badge'>Volume Profile</span>
            <span class='feature-badge'>Classic TA</span>
            <span class='feature-badge'>Order Flow</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div class='powered-by'>
    <p>Powered by <strong style='color:#00ff88 !important;'>ChartPulse.ai</strong> | Built with GPT-4o + Claude 3.5 + Gemini 1.5 Pro</p>
    <p>⚠️ هذا ليس نصيحة مالية. تداول على مسؤوليتك الخاصة.</p>
    <p>© 2025 ChartPulse.ai - All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)
