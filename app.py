import streamlit as st

# הגדרת כותרת ועיצוב הדף
st.set_page_config(page_title="סוכן ניהול משברים", layout="wide")

st.title("🛡️ מערכת אא ניהול משברים - War Room")
st.markdown("---")

# חלוקת המסך לשתי עמודות
col1, col2 = st.columns([1, 2])

with col1:
    st.header("1. הזנת נתונים")
    st.info("הזן כאן מידע גולמי מהרשת לניתוח")

    company_name = st.text_input("שם הארגון:", "אא ניהול משברים")
    platform = st.selectbox("מקור הידיעה:", ["אתר חדשות", "פייסבוק", "טוויטר/X", "טיקטוק", "אחר"])
    news_text = st.text_area("טקסט הידיעה / הפוסט החשוד:", height=250, placeholder="הדבק כאן את הטקסט...")

    analyze_btn = st.button("🚨 נתח אירוע וצור הנחיה ל-AI", type="primary")

with col2:
    st.header("2. מנוע יצירת הנחיות (Prompt Engine)")

    if analyze_btn and news_text:
        st.success("הנתונים נקלטו. מייצר הנחיה לניתוח...")

        # בניית הפרומפט המתוחכם (האלגוריתם שלך)
        prompt_logic = f"""
תפקידך: מומחה בכיר לניהול משברים ותקשורת אסטרטגית.
הלקוח: {company_name}
המקור: {platform}

טקסט האירוע לניתוח:
"{news_text}"

עליך לבצע ניתוח מעמיק ולספק מענה בפורמט הבא:

חלק 1: אבחון (מתודולוגיית SCCT - Coombs)
- סווג את המשבר (Victim / Accidental / Preventable).
- הערך את רמת האחריות (Low / High).
- הערך את רמת הסיכון למוניטין (1-10).

חלק 2: אסטרטגיית תגובה (מודל אברהם וכתר)
- בחר את האסטרטגיה המובילה (הכחשה / בידול / הפחתה / התנצלות / שינוי נרטיב).
- הסבר מדוע אסטרטגיה זו מתאימה לפרופיל המשבר שזוהה.

חלק 3: תוצרים לפרסום מיידי
1. נוסח תגובה רשמי לעיתונות (Tone: רשמי, אחראי).
2. נוסח ציוץ/פוסט לרשתות החברתיות (Tone: אמפתי, ישיר).
"""

        st.text_area("העתק את ההנחיה (Prompt) והדבק ב-Gemini:", value=prompt_logic, height=400)
        st.caption("טיפ: לחץ בתוך התיבה ועל Ctrl+A ואז Ctrl+C להעתקה מהירה.")

    elif analyze_btn and not news_text:
        st.error("נא להזין את טקסט הידיעה לפני הניתוח.")

    else:
        st.info("ממתין להזנת נתונים...")