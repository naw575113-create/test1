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
        
    return [
        {"q": "Nuclear shielding matching: Which material is most effective for neutron attenuation?", "options": ["Lead (Pb)", "Water / Paraffin", "Aluminum (Al)", "Copper (Cu)"], "correct": "Water / Paraffin"},
        {"q": "The 555 Timer IC operating in Astable mode produces which type of output waveform?", "options": ["Sine Wave", "Square Wave", "Triangular Wave", "Sawtooth Wave"], "correct": "Square Wave"}
    ]

def get_student_users_from_sheet():
    base_users = {
        "student": "student123",
        "Roll1": "12345",
        "Roll2": "12345"
    }
    try:
        df = pd.read_csv(CSV_USERS_URL)
        if df is not None and not df.empty:
            df.columns = df.columns.str.strip()
            user_col = [c for c in df.columns if 'user' in c.lower()][0]
            pwd_col = [c for c in df.columns if 'pass' in c.lower()][0]
            
            for _, row in df.iterrows():
                if pd.notna(row[user_col]) and pd.notna(row[pwd_col]):
                    base_users[str(row[user_col]).strip()] = str(row[pwd_col]).strip()
    except:
        pass
    return base_users

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

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_role" not in st.session_state: st.session_state.user_role = None
if "username" not in st.session_state: st.session_state.username = None
if "submitted" not in st.session_state: st.session_state.submitted = False

# 1. Sidebar မှာ Logo ပေါ်စေရန် 
with st.sidebar:
    try:
        st.image("Pu_logo.png", use_container_width=True)
    except Exception:
        try:
            st.image("pu_logo.png", use_container_width=True)
        except Exception:
            pass
    st.markdown("<h4 style='text-align: center;'>Pyay University</h4>", unsafe_allow_html=True)
    st.markdown("---")
# Main Page Header Logo
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image("pu_logo.png", width=150)
    except:
        pass

if not st.session_state.logged_in:
    st.title("🔐 Secure Online Examination System")
    st.subheader("Department of Physics, Pyay University")
    
    username = st.text_input("Username (Case-sensitive)")
    password = st.text_input("Password", type="password")
    
    if st.button("Secure Login", type="primary"):
        if username == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.session_state.user_role = "admin"
            st.session_state.username = "admin"
            st.rerun()
        else:
            valid_students = get_student_users_from_sheet()
            if username in valid_students and str(password).strip() == str(valid_students[username]).strip():
                sheet_data = get_results_from_sheet()
                submitted_users = [str(r[1]) for r in sheet_data if len(r) > 1]
                submitted_users += [str(r[1]) for r in st.session_state.global_results_pool]
                
                if username in submitted_users:
                    st.error(f"❌ Access Denied: User '{username}' has already submitted the exam. Account Locked.")
                else:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "student"
                    st.session_state.username = username
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
        
    # --- ADMIN PANEL ---
    if st.session_state.user_role == "admin":
        st.title("👩‍🏫 Admin Control Panel (Secure Mode)")
        
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
            st.subheader("Inject New Question to Pool Permanently")
            st.info("💡 ဤနေရာတွင် မေးခွန်းအသစ်များကို Google Sheet (Sheet2) ထဲသို့ တိုက်ရိုက်သွားရောက်တိုးပေးရပါမည်။")
                    
    # --- STUDENT PANEL ---
    elif st.session_state.user_role == "student":
        st.title("✍️ Student Examination Terminal")
        st.write(f"Active Session User: **{st.session_state.username}**")
        
        all_questions = get_questions_from_sheet()
        
        if not st.session_state.submitted:
            # --- TIMER LOGIC ---
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
            
            # --- QUESTIONS UI ---
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
                st.warning("⚠️ မေးခွန်းများ Cloud တွင်းမှ ဆွဲယူနေဆဲ ဖြစ်ပါသည်။ ခေတ္တစောင့်ဆိုင်းပေးပါရန်။")
        else:
            disp_score = st.session_state.final_score if 'final_score' in st.session_state else 0
            st.success(f"🎉 သင်၏ ရမှတ်မှာ {disp_score}/{len(all_questions)} ဖြစ်ပြီး စနစ်မှ သိမ်းဆည်းကာ Lock ချထားပြီး ဖြစ်ပါသည်။")
            st.balloons()

