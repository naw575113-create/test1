import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.request
import json
import time

# --- GOOGLE SHEET DATABASE CONNECTIVITY ---
SHEET_ID = "1zwZw4CpctOeI0DNBbaBl2i-FZIA8kh4hcXcBdupbGd8"

CSV_RESULTS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"
CSV_QUESTIONS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet2"
CSV_USERS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet3"

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwr8VYG1uzUpNQA4hSRuhC1nEspoCnSv1ZVRAiwPiRTRpvD3PQ2D1QXXhiorhp3DNEWNg/exec"

EXAM_DURATION_MINUTES = 5

def get_mm_now():
    return datetime.utcnow() + timedelta(hours=6, minutes=30)

if "global_results_pool" not in st.session_state:
    st.session_state.global_results_pool = []

def get_results_from_sheet():
    try:
        df = pd.read_csv(CSV_RESULTS_URL)
        return df.values.tolist()
    except:
        return []

def get_questions_from_sheet():
    try:
        df = pd.read_csv(CSV_QUESTIONS_URL)
        if df is not None and not df.empty:
            sheet_questions = []
            for row in df.values.tolist():
                if len(row) >= 6 and pd.notna(row[0]):
                    sheet_questions.append({
                        "q": str(row[0]),
                        "options": [str(row[1]), str(row[2]), str(row[3]), str(row[4])],
                        "correct": str(row[5])
                    })
            if sheet_questions:
                return sheet_questions
    except:
        pass
    return []

def save_result_to_sheet(username, score):
    timestamp = get_mm_now().strftime("%Y-%m-%d %H:%M:%S")
    new_record = [timestamp, username, score]
    if new_record not in st.session_state.global_results_pool:
        st.session_state.global_results_pool.append(new_record)
        
    try:
        payload = json.dumps({"timestamp": timestamp, "username": username, "score": int(score)}).encode('utf-8')
        req = urllib.request.Request(WEB_APP_URL, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
        urllib.request.urlopen(req, timeout=3)
    except:
        pass

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Secure Exam Terminal", page_icon="🔐", layout="centered")

st.markdown(
    """
    <style>
    div[data-testid="stTextInput"] {
        max-width: 350px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_role" not in st.session_state: st.session_state.user_role = None
if "username" not in st.session_state: st.session_state.username = None
if "submitted" not in st.session_state: st.session_state.submitted = False

with st.sidebar:
    try:
        st.image("pu_logo.png", use_container_width=True)
    except:
        pass
    st.markdown("<h4 style='text-align: center;'>Pyay University</h4>", unsafe_allow_html=True)
    st.markdown("---")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image("pu_logo.png", width=150)
    except:
        pass

if not st.session_state.logged_in:
    st.title("🔐 Pyay University Online Examination Portal")
    st.subheader("Center for Human Resource Development")
    
    username = st.text_input("Username (Case-sensitive)")
    password = st.text_input("Password", type="password")
    
    if st.button("Secure Login", type="primary"):
        entered_user = username.strip()
        entered_pass = str(password).strip()

        # Google Sheet (Sheet3) မှ User အားလုံးကို Header မပါဘဲ တိုက်ရိုက်ဖတ်ယူခြင်း
        all_users = {}
        try:
            # header=None ထည့်လိုက်ခြင်းဖြင့် ပထမဆုံး row ကို header လို့ မသတ်မှတ်တော့ဘဲ ဒေတာအဖြစ် အကုန်ဖတ်မည်
            df_users = pd.read_csv(CSV_USERS_URL, header=None)
            if df_users is not None and not df_users.empty:
                for _, row in df_users.iterrows():
                    if len(row) >= 2 and pd.notna(row.iloc[0]) and pd.notna(row.iloc[1]):
                        u_val = str(row.iloc[0]).strip()
                        p_val = str(row.iloc[1]).strip()
                        # 'Username' ဆိုတဲ့ ခေါင်းစဉ်ပါလာလျှင် ကျော်ရန်
                        if u_val.lower() != "username":
                            all_users[u_val] = p_val
        except Exception as e:
            pass

        # Login စစ်ဆေးခြင်း
        if entered_user in all_users and entered_pass == all_users[entered_user]:
            if entered_user.lower() == "admin":
                st.session_state.logged_in = True
                st.session_state.user_role = "admin"
                st.session_state.username = "admin"
                st.rerun()
            else:
                sheet_data = get_results_from_sheet()
                submitted_users = [str(r[1]) for r in sheet_data if len(r) > 1]
                submitted_users += [str(r[1]) for r in st.session_state.global_results_pool]
                
                if entered_user in submitted_users:
                    st.error(f"❌ Access Denied: User '{entered_user}' has already submitted the exam. Account Locked.")
                else:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "student"
                    st.session_state.username = entered_user
                    st.session_state.submitted = False
                    st.session_state.start_time = get_mm_now()
                    st.rerun()
        else:
            st.error("Invalid credentials. Please try again.")
else:
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.username = None
        st.session_state.submitted = False
        if "start_time" in st.session_state: del st.session_state.start_time
        st.rerun()
        
    if st.session_state.user_role == "admin":
        st.title("👩‍🏫 Administrative Control Panel: Question Bank & Result Management")
        
        st.sidebar.subheader("⚙️ System Control")
        if st.sidebar.button("♻️ Force Reboot System", type="secondary"):
            st.session_state.global_results_pool = []
            st.sidebar.success("Memory Pool Cleared Successfully!")
            time.sleep(0.5)
            st.rerun()
        
        tab1, tab2 = st.tabs(["📝 View Results Logs", "➕ Add Secure Questions"])
        
        with tab1:
            st.subheader("🔒 Terminal Live Records")
            db_data = get_results_from_sheet()
            display_data = []
            
            for r in db_data:
                if len(r) >= 3 and str(r[0]).lower() != "timestamp":
                    display_data.append({"Timestamp": r[0], "Student Username": r[1], "Score Obtained": f"{r[2]} Points"})
            
            for r in st.session_state.global_results_pool:
                row_dict = {"Timestamp": r[0], "Student Username": r[1], "Score Obtained": f"{r[2]} Points"}
                if row_dict not in display_data:
                    display_data.append(row_dict)
            
            if display_data:
                st.table(display_data)
            else:
                st.info("💡 ဖြေဆိုထားသော ကျောင်းသား မှတ်တမ်း မရှိသေးပါ။")
                
        with tab2:
            st.subheader("➕ Inject New Question to Sheet2")
            st.info("💡 ဤနေရာမှ တဆင့် Google Sheet (Sheet2) သို့ မေးခွန်းအသစ်များကို တိုက်ရိုက် ထည့်သွင်းနိုင်ပါသည်။")
            
            with st.form("add_question_form"):
                new_q = st.text_area("မေးခွန်း (Question)")
                col_a, col_b = st.columns(2)
                with col_a:
                    opt1 = st.text_input("Option A")
                    opt2 = st.text_input("Option B")
                with col_b:
                    opt3 = st.text_input("Option C")
                    opt4 = st.text_input("Option D")
                
                correct_ans = st.text_input("အမှန်ဖြေ (Correct Answer - အထက်ပါ Options များထဲမှ တစ်ခုအတိုင်း အတိအကျရေးပါ)")
                
                submitted_q = st.form_submit_button("Google Sheet သို့ မေးခွန်းအသစ် ထည့်မည်")
                
                if submitted_q:
                    if new_q and opt1 and opt2 and opt3 and opt4 and correct_ans:
                        try:
                            payload = json.dumps({
                                "action": "add_question",
                                "q": new_q,
                                "opt1": opt1,
                                "opt2": opt2,
                                "opt3": opt3,
                                "opt4": opt4,
                                "correct": correct_ans
                            }).encode('utf-8')
                            
                            req = urllib.request.Request(WEB_APP_URL, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
                            response = urllib.request.urlopen(req, timeout=5)
                            res_data = json.loads(response.read().decode('utf-8'))
                            
                            if res_data.get("status") == "success":
                                st.success("✅ မေးခွန်းအသစ် Google Sheet သို့ အောင်မြင်စွာ ရောက်ရှိသွားပါပြီ။")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ မေးခွန်းထည့်သွင်းမှု မအောင်မြင်ပါ။")
                        except Exception as e:
                            st.error(f"⚠️ ချိတ်ဆက်မှု အမှားအယွင်း ရှိနေပါသည်: {e}")
                    else:
                        st.warning("⚠️ အချက်အလက်အားလုံးကို ပြည့်စုံစွာ ဖြည့်စွက်ပေးပါ။")
                
    elif st.session_state.user_role == "student":
        st.title("✍️ Student Examination Dashboard ")
        st.write(f"Active Session User: **{st.session_state.username}**")
        
        all_questions = get_questions_from_sheet()
        
        if not st.session_state.submitted:
            if "start_time" in st.session_state:
                end_time = st.session_state.start_time + timedelta(minutes=EXAM_DURATION_MINUTES)
                now = get_mm_now()
                remaining = end_time - now
                seconds_left = int(remaining.total_seconds())
                
                if seconds_left <= 0:
                    st.error("⏳ အချိန်ပြည့်သွားပါပြီ။ သင်ရွေးချယ်ထားသမျှ အဖြေများကို စနစ်မှ အလိုအလျောက် သိမ်းဆည်းနေပါသည်...")
                    time.sleep(1)
                    auto_score = 0
                    for i, q in enumerate(all_questions):
                        radio_key = f"q_{i}"
                        if radio_key in st.session_state and st.session_state[radio_key] == q['correct']:
                            auto_score += 1
                    save_result_to_sheet(st.session_state.username, auto_score)
                    st.session_state.submitted = True
                    st.session_state.final_score = auto_score
                    st.rerun()
                
                mins, secs = divmod(seconds_left, 60)
                timer_text = f"⏳ ကျန်ရှိချိန် - {mins:02d}:{secs:02d}"
                
                if seconds_left < 60:
                    st.sidebar.error(timer_text)
                else:
                    st.sidebar.warning(timer_text)
            
            if all_questions:
                score = 0
                user_answers = {}
                
                for i, q in enumerate(all_questions):
                    st.markdown(f"##### Q{i+1}: {q['q']}")
                    user_answers[i] = st.radio(f"Select answer for Q{i+1}:", q['options'], index=None, key=f"q_{i}")
                    st.write("---")
                    
                if st.button("Final Submit & Lock Account", type="primary"):
                    for i, q in enumerate(all_questions):
                        if i in user_answers and user_answers[i] is not None:
                            if str(user_answers[i]) == str(q['correct']):
                                score += 1
                    
                    save_result_to_sheet(st.session_state.username, score)
                    st.session_state.submitted = True
                    st.session_state.final_score = score
                    st.rerun()
            else:
                st.warning("⚠️ မေးခွန်းများ Google Sheet ထဲတွင် မတွေ့ရှိရသေးပါ။ ကျေးဇူးပြု၍ Sheet2 ကို စစ်ဆေးပါ။")
        else:
            disp_score = st.session_state.final_score if 'final_score' in st.session_state else 0
            st.success(f"🎉 သင်၏ ရမှတ်မှာ {disp_score}/{len(all_questions)} ဖြစ်ပြီး စနစ်မှ သိမ်းဆည်းကာ Lock ချထားပြီး ဖြစ်ပါသည်။")
            st.balloons()
