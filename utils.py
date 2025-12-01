import streamlit as st

def get_db_url():
    return (
        f"postgresql://{st.secrets['POSTGRES_USERNAME']}:"
        f"{st.secrets['POSTGRES_PASSWORD']}@"
        f"{st.secrets['POSTGRES_SERVER']}:"
        f"{st.secrets['POSTGRES_PORT']}/"
        f"{st.secrets['POSTGRES_DATABASE']}"
    )
