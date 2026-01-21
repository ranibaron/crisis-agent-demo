import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import urllib.parse
import json

# --- 1. הגדרות דף ועיצוב RTL (מימין לשמאל) ---
st.set_page_config(page_title="Crisis Guardian AI", layout="wide", page_icon="🛡️")

# הזרקת CSS כדי להפוך את הממשק לעברית מלאה
st.markdown("""
<style>
    /* כיוון כללי של האפליקציה */
    .stApp {
        direction: rtl;
        text-align: right;
    }

    /* יישור טקסטים בכותרות ופסקאות */
    h1, h2, h3, h4, h5, h6, p, div {
        text-align: right;
    }

    /* יישור שדות קלט (Input, Text Area) */
    .stTextInput input, .stTextArea textarea, .stSelectbox {
        direction: rtl; 
        text-align: right;
    }

    /* יישור רשימות (סימון הנקודות מימין) */
    ul {
        direction: rtl;
        padding-right: 20px;
    }

    /* התאמה של ה-Sidebar */
    section[data-testid="stSidebar"] {
        direction: rtl;
        text_align: right;
    }

    /* תיקון קטן לכפתורים שלא יתהפכו */
    .stButton button {
        direction: ltr; /* משאיר את הטקסט בכפתור קריא */
    }
</style>
""", unsafe_allow_html=True)

# --- 2. ניהול מפתחות ומודלים ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])


def get_available_model():
    """בחירה חכמה של מודל קיים"""
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: return m.name
                if 'pro' in m.name: return m.name
        return 'models/gemini-pro'
    except:
        return 'models/gemini-pro'


def search_news(query, limit=5):
    """חיפוש חדשות"""
    results = []
    try:
        with DDGS() as ddgs:
            ddgs_news = ddgs.news(keywords=query, region="il-he", safesearch="off", max_results=limit)
            for r in ddgs_news: results.append(r)
    except Exception as e:
        st.error(f"תקלה בחיפוש: {e}")
    return results


def generate_share_links(text):
    """יצירת לינקים לשיתוף"""
    encoded_text = urllib.parse.quote(text)
    return {
        "X (Twitter)": f"https://twitter.com/intent/tweet?text={encoded_text}",
        "WhatsApp": f"https://wa.me/?text={encoded_text}",
        "Email": f"mailto:?body={encoded_text}",
        "Facebook": "https://www.facebook.com/sharer/sharer.php"
    }


# --- 3. ממשק משתמש ---

st.title("🛡️ Crisis Guardian - ניהול משברים")
st.caption("מערכת ניטור וניהול תקשורתי בזמן אמת")
st.markdown("---")

# סרגל צד
with st.sidebar:
    st.header("⚙️ הגדרות")
    company_name = st.text_input("שם הארגון:", "אל על")
    st.info("המערכת סורקת מקורות גלויים ומנתחת באמצעות AI.")

# אתחול Session State לשמירת נתונים
if 'draft_response' not in st.session_state:
    st.session_state['draft_response'] = ""
if 'analysis_result' not in st.session_state:
    st.session_state['analysis_result'] = None

# --- שלב א': חיפוש ---
st.subheader(f"1. ניטור אזכורים: {company_name}")
if st.button("🔍 סרוק חדשות אחרונות", type="secondary"):
    with st.spinner("מבצע סריקת רשת..."):
        st.session_state['news_results'] = search_news(company_name)

if 'news_results' in st.session_state and st.session_state['news_results']:
    selected_article = st.selectbox(
        "בחר ידיעה לטיפול:",
        options=st.session_state['news_results'],
        format_func=lambda x: f"{x['title']} ({x['source']})"
    )

    if selected_article:
        st.markdown(f"**תקציר:** {selected_article['body']}")
        st.markdown(f"[קרא מקור]({selected_article['url']})")

        # כפתור הניתוח
        # כפתור הניתוח
        if st.button("🚨 נתח אירוע והכן תגובה", type="primary"):
            st.session_state['analyzing'] = True
            st.session_state['current_article'] = selected_article

            # --- שלב ב': הניתוח (המוח) ---
            # שינוי לפרומפט: מגדירים במפורש את מבנה ה-JSON הרצוי
            prompt = f"""
                    אתה מנהל משברים מומחה.
                    נתח את הידיעה: "{selected_article['title']}: {selected_article['body']}" עבור חברת {company_name}.

                    עליך להחזיר אובייקט JSON בלבד לפי המבנה הבא (ללא Markdown):
                    {{
                        "analysis": "טקסט הניתוח המלא (כולל סיווג קומבס, חומרה ואסטרטגיה)",
                        "draft": "נוסח תגובה נקי לפרסום (עד 60 מילים)"
                    }}
                    """

            with st.spinner("מעבד נתונים ומנסח תגובה..."):
                try:
                    model_name = get_available_model()

                    # --- התיקון החשוב: הגדרת מצב JSON מובנה ---
                    model = genai.GenerativeModel(
                        model_name,
                        generation_config={"response_mime_type": "application/json"}
                    )

                    response = model.generate_content(prompt)

                    # כעת אין צורך בניקוי ידני מסובך, הפלט הוא JSON טהור
                    data = json.loads(response.text)

                    # שמירה בזיכרון
                    st.session_state['analysis_result'] = data.get('analysis', 'לא התקבל ניתוח')
                    st.session_state['draft_response'] = data.get('draft', 'לא התקבלה טיוטה')

                except Exception as e:
                    st.error(f"שגיאה בעיבוד הנתונים: {e}")
                    # במקרה חירום מציגים את הטקסט הגולמי כדי לא להשאיר מסך ריק
                    st.session_state['analysis_result'] = response.text if 'response' in locals() else str(e)
                    st.session_state['draft_response'] = "נא לנסח ידנית (שגיאה ב-AI)"

# --- שלב ג': הצגת תוצאות ועריכה ---
if st.session_state['analysis_result']:
    st.markdown("---")

    # עמודה ימנית: הניתוח האקדמי
    col_analysis, col_action = st.columns([1, 1])

    with col_analysis:
        st.subheader("🧠 ניתוח אסטרטגי")
        st.info(st.session_state['analysis_result'])

    # עמודה שמאלית: ה-Action Item
    with col_action:
        st.subheader("✍️ ניהול תגובה")

        # שדה העריכה - כבר מכיל את הטקסט של ה-AI
        final_text = st.text_area(
            "ערוך את הטיוטה לפני הפצה:",
            value=st.session_state['draft_response'],
            height=200,
            key="final_edit_area"
        )

        st.caption("💡 הלינקים למטה יתעדכנו אוטומטית כשתסיים להקליד (לחץ מחוץ לתיבה).")

        # כפתורי שיתוף - צמודים לשדה העריכה
        links = generate_share_links(final_text)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.link_button("X (Twitter)", links["X (Twitter)"], use_container_width=True)
        with c2:
            st.link_button("WhatsApp", links["WhatsApp"], use_container_width=True)
        with c3:
            st.link_button("Email", links["Email"], use_container_width=True)