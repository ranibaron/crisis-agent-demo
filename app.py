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
        if st.button("🚨 נתח אירוע והכן תגובה", type="primary"):
            st.session_state['analyzing'] = True
            st.session_state['current_article'] = selected_article

            # --- שלב ב': הניתוח (המוח) ---
            prompt = f"""
            אתה מנהל משברים מומחה.
            נתח את הידיעה: "{selected_article['title']}: {selected_article['body']}" עבור חברת {company_name}.

            החזר תשובה בפורמט JSON בלבד, עם השדות הבאים:
            1. "analysis": טקסט (Markdown) הכולל ניתוח לפי מודל Coombs (סוג משבר), רמת חומרה (1-10) ואסטרטגיה מומלצת לפי אברהם וכתר.
            2. "draft": טקסט נקי של התגובה המומלצת לפרסום (עד 60 מילים, בעברית, ללא כותרות).
            """

            with st.spinner("מעבד נתונים ומנסח תגובה..."):
                try:
                    model_name = get_available_model()
                    model = genai.GenerativeModel(model_name)
                    # בקשה לפורמט JSON (אם המודל תומך, אם לא הוא ינסה טקסט רגיל)
                    response = model.generate_content(prompt)

                    # ניקוי המחרוזת ל-JSON תקין
                    clean_json = response.text.replace("```json", "").replace("```", "").strip()
                    data = json.loads(clean_json)

                    # שמירה בזיכרון
                    st.session_state['analysis_result'] = data['analysis']
                    st.session_state['draft_response'] = data['draft']

                except Exception as e:
                    st.error(f"שגיאה בעיבוד הנתונים: {e}")
                    # Fallback במקרה שהמודל לא החזיר JSON
                    st.session_state['analysis_result'] = response.text
                    st.session_state['draft_response'] = "לא ניתן היה לחלץ טיוטה אוטומטית. נא לנסח ידנית."

# --- שלב ג': הצגת תוצאות ועריכה ---
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