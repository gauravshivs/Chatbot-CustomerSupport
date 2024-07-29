import streamlit as st
import requests

st.title("Product Help Bot")

backend_url = "http://127.0.0.1:8000"

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if 'selected_rating' not in st.session_state:
    st.session_state.selected_rating = 1

options=[1, 2, 3, 4, 5]
st.write(options.index(st.session_state.selected_rating))

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def update_rating():
    """
    Submits the user's rating for a chatbot response to the backend server.

    This function is triggered by a change in the selected rating from a Streamlit radio button widget.
    It collects the selected rating from `st.session_state`, determines its index in the `options` list,
    and sends this rating along with the response content to a specified backend URL for feedback submission.

    The backend is expected to return a JSON response confirming the feedback submission, which is processed
    to provide user feedback.

    Parameters:
    None

    Returns:
    None
    """
    feedback_response = requests.post(f"{backend_url}/submit-feedback/", json={
        "response_content": response_content,
        "rating": options.index(st.session_state.selected_rating)
    }).json()

# User input
if prompt := st.chat_input("How can I help you today?"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Send prompt to FastAPI backend and get response
    response = requests.post(f"{backend_url}/get-response/", json={"history": str(st.session_state.messages),"prompt": prompt}).json()

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    response_content = response.get("response", "Sorry, something went wrong.")
    
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response_content)
       
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response_content})

    # Star rating feedback
    st.write("Rate this response:")
    
    st.session_state.selected_rating = st.radio(
            "Stars:",
            options=options,
            index=st.session_state.selected_rating,
            horizontal=True,
            key=f"submit_feedback_{len(st.session_state.messages)}",
            on_change=update_rating
        )
    
   