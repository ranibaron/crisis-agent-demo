import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import urllib.parse
from datetime import datetime

# --- הגדרות ראשוניות ---
st.set_page_config(page_title="Crisis Guardian AI", layout="wide", page_icon="🛡️")

# טעינת מפתח API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("חסר מפתח GOOGLE_API_KEY בקובץ secrets.toml")
    st.stop()


# --- פונקציות עזר ---

def search_news(query, limit=5):
    """חיפוש חדשות מהרשת בחינם"""
    results = []
    try:
        with DDGS() as ddgs:
            # חיפוש חדשות מישראל ביומיים האחרונים ('d' = day, אפשר לשנות)
            ddgs_news = ddgs.news(keywords=query, region="il-he", safesearch="off", max_results=limit)
            for r in ddgs_news:
                results.append(r)
    except Exception as e:
        st.error(f"שגיאה בחיפוש חדשות: {e}")
    return results


def generate_share_links(text, subject="עדכון ניהול משבר"):
    """יצירת לינקים לשיתוף מהיר"""
    encoded_text = urllib.parse.quote(text)
    encoded_subject = urllib.parse.quote(subject)

    links = {
        "X (Twitter)": f"https://twitter.com/intent/tweet?text={encoded_text}",
        "WhatsApp": f"https://wa.me/?text={encoded_text}",
        "Email": f"mailto:?subject={encoded_subject}&body={encoded_text}",
        "Facebook": "https://www.facebook.com/sharer/sharer.php"  # פייסבוק לא מאפשרים טקסט אוטומטי מטעמי ספאם, רק לינק
    }
    return links


def get_available_model():
    """פונקציה שמוצאת אוטומטית מודל זמין בחשבון שלך"""
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # מעדיף את פלאש כי הוא מהיר, אם לא - לוקח את פרו
                if 'flash' in m.name:
                    return m.name
                if 'pro' in m.name:
                    return m.name
        # ברירת מחדל אם לא מצא לוגיקה
        return 'models/gemini-pro'
    except Exception as e:
        return 'models/gemini-pro'


# --- ממשק משתמש ---

st.title("🛡️ Crisis Guardian - מערכת ניהול משברים אוטונומית")
st.markdown("מערכת סוכן המנטרת חדשות בזמן אמת, מזהה משברים ומייצרת מענה לפי מתודולוגיות Coombs ואברהם וכתר.")
st.markdown("---")

# סרגל צד - הגדרות
with st.sidebar:
    st.header("⚙️ הגדרות סוכן")
    company_name = st.text_input("שם החברה לניטור", "אל על")
    days_back = st.slider("טווח חיפוש (ימים)", 1, 7, 2)
    st.info(f"הסוכן יחפש אזכורים של '{company_name}' בחדשות.")

# --- שלב 1: ניטור וחיפוש ---
st.subheader(f"🕵️ ניטור רשת: {company_name}")

if st.button("סרוק חדשות אחרונות 🔍", type="primary"):
    with st.spinner("סורק את הרשת אחר אזכורים..."):
        # חיפוש חדשות אמיתי
        query = f"{company_name}"
        news_results = search_news(query, limit=5)
        st.session_state['news_results'] = news_results

        if not news_results:
            st.warning("לא נמצאו חדשות חדשות בטווח הזמן שנבחר.")

# הצגת תוצאות החיפוש (אם יש בזיכרון)
if 'news_results' in st.session_state and st.session_state['news_results']:
    st.success(f"נמצאו {len(st.session_state['news_results'])} כתבות רלוונטיות.")

    selected_article = st.selectbox(
        "בחר כתבה לניתוח עומק:",
        options=st.session_state['news_results'],
        format_func=lambda x: f"{x['title']} ({x['source']})"
    )

    if selected_article:
        st.info(f"**תקציר:** {selected_article['body']}...")
        st.markdown(f"[לקריאת הכתבה המלאה]({selected_article['url']})")

        # כפתור ניתוח לכתבה הספציפית
        if st.button("🚨 הפעל נוהל ניתוח משבר (AI Analysis)"):
            st.session_state['analyzing'] = True
            st.session_state['current_article'] = selected_article

# --- שלב 2 ו-3: ניתוח משבר ופעולה ---
if st.session_state.get('analyzing') and st.session_state.get('current_article'):
    article = st.session_state['current_article']

    st.markdown("---")
    st.subheader("🧠 ניתוח המצב והמלצות פעולה")

    prompt = f"""
    אתה יועץ תקשורת בכיר המתמחה בניהול משברים.
    הלקוח: חברת "{company_name}".
    הידיעה החדשותית: "{article['title']}: {article['body']}"

    עליך לבצע את המשימות הבאות:
    1. **האם זה משבר?** (כן/לא) והערכת חומרה (1-10).
    2. **סיווג (Coombs SCCT):** האם זה Victim, Accidental, או Preventable? הסבר בקצרה.
    3. **אסטרטגיה (אברהם וכתר):** מהי האסטרטגיה המומלצת? (למשל: התנצלות מלאה, הכחשה, עמימות, Bolstering, וכו').
    4. **ניסוח תגובה:** כתוב הודעה מומלצת לעיתונות/רשתות חברתיות שמונעת הסלמה.

    החזר את התשובה בפורמט Markdown מסודר.
    """

    with st.spinner("ג'מיני מנתח את המשבר לפי המודלים האקדמיים..."):
        try:
            # שימוש בפונקציה החדשה למציאת מודל
            model_name = get_available_model()
            # st.write(f"Using model: {model_name}") # אפשר להוריד את ההערה לדיבאגינג

            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            ai_output = response.text

            # הצגת הניתוח
            st.markdown(ai_output)

            # חילוץ התגובה (ניסיון פשטני לקחת את החלק האחרון או לתת למשתמש לערוך)
            st.markdown("---")
            st.subheader("📢 הפצת תגובה מיידית")

            final_response = st.text_area("ערוך את התגובה לפני הפצה:", value="העתק לכאן את התגובה המוצעת מלמעלה...",
                                          height=150)

            # כפתורי שיתוף
            links = generate_share_links(final_response, subject=f"תגובה רשמית: {article['title']}")

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.link_button("X (Twitter)", links["X (Twitter)"])
            with c2:
                st.link_button("WhatsApp", links["WhatsApp"])
            with c3:
                st.link_button("Email Draft", links["Email"])
            with c4:
                if st.button("📋 העתק ללוח"):
                    st.write("הטקסט הועתק! (סימולציה)")  # Streamlit מגביל גישה ללוח, בד"כ המשתמש מעתיק ידנית

        except Exception as e:
            st.error(f"שגיאה בניתוח ה-AI: {e}")