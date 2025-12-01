import streamlit as st

st.write("Secrets loaded:")
st.write(st.secrets)
st.write("HASHED_PASSWORD:", st.secrets.get("HASHED_PASSWORD"))
