import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
load_dotenv()  # take environment variables from .env.

# Set the page configuration first
st.set_page_config(page_title="Gemini Image Demo")

# Import the rest of the libraries
import os
import pathlib
import textwrap
from PIL import Image
import speech_recognition as sr
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
from st_audiorec import st_audiorec
import tempfile

# Initialize the speech recognizer
r = sr.Recognizer()

# Fetch the Google API key from environment variables
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to convert audio file to text
def convert_audio_to_text(audio_file_path):
    try:
        with sr.AudioFile(audio_file_path) as source:
            audio = r.record(source)  # Record the audio
            text = r.recognize_google(audio)
            return text.lower()  # Ensure lowercase for better input consistency
    except sr.UnknownValueError:
        st.write("Could not understand audio")
        return None
    except sr.RequestError as e:
        st.write(f"Could not request results from Google Speech Recognition service; {e}")
        return None
    except Exception as e:
        st.write(f"An error occurred: {e}")
        return None

# Streamlit app
st.title("Gemini Image Demo")

# Create a placeholder to store the recorded audio data
audio_placeholder = st.empty()

# Add an instance of the audio recorder to your streamlit app's code
audio_data = st_audiorec()

# Display the recorded audio
audio_placeholder.audio(audio_data, format="audio/wav")

# Set the header for the Streamlit app
st.header("Gemini Application")

# Initialize voice_text and chat_history outside the button click scope
voice_text = st.session_state.get("voice_text", "")
chat_history = st.session_state.get("chat_history", [])

# Create a text input field for voice text input
#voice_input = st.text_input("Input Prompt:", value=st.session_state.get("voice_input", ""))

# Convert the recorded audio file to text automatically
if audio_data:
    # Save the recorded audio data to a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_audio_file:
        temp_audio_file.write(audio_data)
        temp_audio_path = temp_audio_file.name

    # Perform the conversion
    with st.spinner("Converting audio to text..."):
        voice_text = convert_audio_to_text(temp_audio_path)
        if voice_text:
            # Populate the text input with voice text
            voice_input = st.text_input("Input Prompt:", key="voice_input", value=voice_text)

# Function to get Gemini model response based on input parameters
def get_gemini_response(voice_input, image):
    model = genai.GenerativeModel('gemini-pro-vision')

    # Check if the image variable is not empty
    if image:
        # Use the Gemini model to generate content based on the input
        response = model.generate_content([voice_input, image])
        return response.text
    else:
        st.write("No image uploaded. Please upload an image.")
        return None

# Allow users to upload an image
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png", "pdf"])
image = ""
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image.", use_column_width=True)

# Button to submit the form
submit = st.button("Submit")

# If the submit button is clicked
if submit:
    # Get Gemini model response based on user inputs
    response = get_gemini_response(st.session_state.voice_input, image)
    if response:
        st.subheader("The Response is")
        st.write(response)
        # Add user input and Gemini response to chat history
        chat_history.append(f"User: {st.session_state.voice_input}")
        chat_history.append(f"Gemini: {response}")

        # Convert the Gemini response to speech
        tts = gTTS(text=response, lang="en")

        # Save the audio to a buffer
        buffer = BytesIO()
        tts.write_to_fp(buffer)

        # Play the audio
        st.audio(buffer.getvalue(), format="audio/mp3")
    else:
        st.write("No image uploaded. Please upload an image.")

# Save the updated chat history back to session state
st.session_state.chat_history = chat_history

# Display chat history at the bottom
st.subheader("Chat History")
for message in chat_history:
    st.write(message)
