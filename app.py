import streamlit as st
st.title('DCS Project')
st.markdown("<h1 style='text-align: center;'>Online Examination System</h1>", unsafe_allow_html=True)
left_col, middle_col, right_col = st.columns([1.5, 2, 1.5])
with middle_col:
    username = st.text_input("username", key="dcs_user")
    password = st.text_input("Password", type="password", key="dcs_pass")
