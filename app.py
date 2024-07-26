import streamlit as st
import requests

st.title("Product Help Bot")

backend_url = "http://localhost:8000"  # Change to your FastAPI URL if hosted differently

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Send prompt to FastAPI backend and get response
    response = requests.post(f"{backend_url}/get-response/", json={"prompt": prompt}).json()
    response_content = response.get("response", "Sorry, something went wrong.")
    
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response_content)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response_content})

    # Star rating feedback
    st.write("Rate this response:")
    stars = st.radio("Stars:", options=[1, 2, 3, 4, 5], index=4, horizontal=True, key=f"stars_{len(st.session_state.messages)}")
    if st.button("Submit Feedback", key=f"submit_feedback_{len(st.session_state.messages)}"):
        feedback_response = requests.post(f"{backend_url}/submit-feedback/", json={
            "response_content": response_content,
            "rating": stars
        }).json()
        st.success(feedback_response.get("message", "Feedback saved."))