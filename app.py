import streamlit as st
import requests

st.set_page_config(page_title="Customer Discovery Platform")

st.text("Sky High Analytics")
st.title("Customer Discovery Platform")

path = st.text_input("Local Directory")
google_id = st.text_input("Google Drive Folder ID")
question = st.text_input("Your Query")

if question and path and google_id:
    if st.button("Get Answer"):
        response = requests.post("http://localhost:8095/docqna", 
                                 json = {"query": question, "path": path, 
                                         "google_path": google_id})

        if response.status_code == 200:
            result = response.json()
            st.write("Answer: ", result["Answer"])
            st.write("Confidence Score (0-100): ", result["score"])
            st.write("Reference Documents: ", result["Reference Document"])
            st.write("Reference Text: ", result["Reference Text"])

        # Handle bad connections
        else:
            st.error("An error occurred while fetching the answer. Please try again.")
