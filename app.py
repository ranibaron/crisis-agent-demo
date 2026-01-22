# כפתור הניתוח
if st.button("🚨 נתח אירוע והכן תגובה", type="primary"):
    st.session_state['analyzing'] = True
    st.session_state['current_article'] = selected_article

    # --- שינוי הפרומפט: פיצול ל-5 שדות נפרדים ---
    prompt = f"""
            אתה מומחה לניהול משברים. נתח את הידיעה: "{selected_article['title']}: {selected_article['body']}" עבור חברת {company_name}.

            החזר אובייקט JSON בלבד עם השדות הבאים:
            1. "coombs_type": סיווג המשבר לפי Coombs (קורבן/תאונה/נמנע) והסבר קצר.
            2. "severity_score": מספר בלבד בין 1 ל-10.
            3. "damage_assessment": ניתוח הפגיעה בחברה (תדמיתית/פיננסית/משפטית).
            4. "strategy": האסטרטגיה הנבחרת לפי אברהם וכתר והסבר מדוע.
            5. "draft": נוסח תגובה מלא לפרסום (עד 60 מילים).
            """

    with st.spinner("מעבד נתונים ומנסח תגובה..."):
        try:
            model_name = get_available_model()
            model = genai.GenerativeModel(
                model_name,
                generation_config={"response_mime_type": "application/json"}
            )

            response = model.generate_content(prompt)
            data = json.loads(response.text)

            # שמירת כל השדות בנפרד ב-session_state
            st.session_state['analysis_data'] = data
            st.session_state['draft_response'] = data.get('draft', '')

        except Exception as e:
            st.error(f"שגיאה בעיבוד הנתונים: {e}")

# --- שלב ג': הצגת תוצאות (בעיצוב חדש ומפורק) ---
if 'analysis_data' in st.session_state and st.session_state['analysis_data']:
    data = st.session_state['analysis_data']
    st.markdown("---")

    col_right, col_left = st.columns([1.2, 0.8])

    # עמודה ימנית: הניתוח המפורק
    with col_right:
        st.subheader("📊 דו\"ח ניתוח משבר")

        # 1. סיווג קומבס
        st.markdown(f"**📌 סיווג (Coombs):** {data.get('coombs_type')}")

        # 2. מד חומרה (Visual)
        score = data.get('severity_score', 0)
        st.markdown(f"**🔥 רמת חומרה:** {score}/10")
        st.progress(int(score) * 10)  # פס התקדמות ויזואלי

        # 3. ניתוח הפגיעה
        with st.expander("📉 פירוט הפגיעה בחברה", expanded=True):
            st.write(data.get('damage_assessment'))

        # 4. האסטרטגיה
        st.success(f"💡 **אסטרטגיה מומלצת:** {data.get('strategy')}")

    # עמודה שמאלית: ניהול התגובה
    with col_left:
        st.subheader("📢 טיוטה לפרסום")

        final_text = st.text_area(
            "ערוך טיוטה:",
            value=st.session_state['draft_response'],
            height=250
        )

        # כפתורי שיתוף
        links = generate_share_links(final_text)
        c1, c2, c3 = st.columns(3)
        with c1: st.link_button("X", links["X (Twitter)"], use_container_width=True)
        with c2: st.link_button("WhatsApp", links["WhatsApp"], use_container_width=True)
        with c3: st.link_button("Email", links["Email"], use_container_width=True)