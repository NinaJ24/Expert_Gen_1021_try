import streamlit as st
import random
import time
from dotenv import load_dotenv
# import threading  # 导入 threading 模块
# import logging    # 导入 logging 模块
from pinecone_plugins.assistant.models.chat import Message
from pinecone import Pinecone

import openai #added open AI
from PIL import Image #Added Image
# from streamlit_paste_button import paste_image  # Added to enable clipboard image pasting - 0310
# from streamlit_paste_button import paste_image_button as pbutton
from streamlit_paste_button import paste_image_button as pbutton
import io
import os
from openai import OpenAI
import base64  # Added to handle image conversion for GPT-4o - 0310


load_dotenv()

PINECONE_API_KEY = st.secrets['PINECONE_API_KEY']
OPENAI_API_KEY = st.secrets['OPENAI_API_KEY']  # Added to authenticate OpenAI GPT-4o API - 0310

pc = Pinecone(api_key=PINECONE_API_KEY)
assistant = pc.assistant.Assistant(assistant_name="example-assistant2")
client = OpenAI(
    api_key=OPENAI_API_KEY,  # This is the default and can be omitted
)


# def describe_image(image_bytes):  # Function to generate detailed descriptions of images using GPT-4o - 0310
#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[
#             {"role": "system", "content": "You are an AI that describes images in great detail."},
#             {"role": "user", "content": "Describe this image in detail."},
#         ],
#         max_tokens=300
#     )
#     # return response["choices"][0]["message"]["content"]
#     return response.choices[0].message.content  # Fixed TypeError: ChatCompletion object is not subscriptable - 0310
def describe_image(image_bytes):  # Function to generate detailed descriptions of images using GPT-4o - 0310
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")  # Convert image to base64
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        # messages=[
        #     {"role": "system", "content": "You are an AI that describes images in great detail."},
        #     {"role": "user", "content": f"Describe this image in detail. Here is the image data: {image_base64}"},
        # ],
        messages=[
            {"role": "system", "content": "You are an AI specialized in extracting text, questions, tables, and figures from uploaded images. Extract only the questions, tables, and diagrams without adding explanations or unnecessary details. Maintain the original structure of the content as much as possible."},
            {"role": "user", "content": f"Extract the questions, tables, and figures from this uploaded image: {image_base64}"},
        ],  # Updated to focus on extracting structured content - 0310

        max_tokens=300
    )
    print(f'Extracted text from image: {result}')  # Debug print - 0310
    return response.choices[0].message.content  # Fixed TypeError: ChatCompletion object is not subscriptable - 0310


def get_response_content(query):
    # Create a Message object using the input text
    msg = Message(content=query)

    # Call the chat function with the Message object
    resp = assistant.chat(messages=[msg])

    # Extract the content part of the response
    answer = resp.get("message", {}).get("content", "")

    # Output and return the content part
    print(answer)
    # display(Markdown(content_text))
    print(f'get_response_content: {answer}')  # Debug print - 0310
    return answer


# Streamed response emulator
def response_generator():
    response = random.choice(
        [
            "Hello there! How can I assist you today?",
            "Hi, human! Is there anything I can help you with?",
            "Do you need help?",
        ]
    )
    for word in response.split():
        yield word + " "
        time.sleep(0.05)


st.title("ExpertGen")
st.subheader("A generative AI-powered learning assistant providing professional, in-depth insights in tailored domains.")
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


uploaded_file = st.file_uploader("Upload an image or paste from clipboard", type=["png", "jpg", "jpeg"], accept_multiple_files=False)  # Enabled clipboard paste support for images - 0310  # Allow users to upload images for AI processing - 0310

# paste_result = pbutton("📋 Paste an image")  # Updated to use correct function for pasting images - 0310
# paste_result = spb.paste_image_button("📋 Paste an image")  # Ensured unique key to prevent StreamlitDuplicateElementKey issue - 0310
paste_result = pbutton("📋 Paste an image")


if paste_result.image_data is not None:  # Corrected variable name for pasted image - 0310
    uploaded_file = paste_result.image_data  # Use correct attribute for clipboard pasting - 0310  # Enabled clipboard paste support for images - 0310  # Allow users to upload images for AI processing - 0310

if uploaded_file:
    if isinstance(uploaded_file, io.BytesIO):
        image = Image.open(uploaded_file)  # Ensure compatibility with both uploaded and pasted images - 0310
    else:
        image = uploaded_file  # Directly use pasted images which are already PIL objects - 0310
    # st.image(image, caption="Uploaded Image", use_column_width=True)
    st.image(image, caption="Uploaded Image", use_container_width=True)  # Updated per Streamlit API recommendation - 0310

    
    image_bytes = io.BytesIO()  # Convert image to bytes for processing - 0310
    
    if isinstance(uploaded_file, Image.Image):
        uploaded_file.save(image_bytes, format='PNG')  # Ensure correct format conversion for pasted images - 0310
    else:
        image_bytes = uploaded_file.getvalue()  # Handle uploaded file correctly - 0310
    # No need to call getvalue() again as image_bytes is already bytes - 0310
    image_description = describe_image(image_bytes)
    print(f'Image description extracted: {image_description}')  # Debug print - 0310
    st.session_state.messages.append({"role": "user", "content": "[Uploaded Image]"})  # Store uploaded image reference in chat history - 0310
    st.session_state.messages.append({"role": "assistant", "content": image_description})  # Store GPT-4o-generated image description in chat history - 0310
    
    with st.chat_message("assistant"):
        st.markdown(image_description)

# if uploaded_file:
#     image = Image.open(uploaded_file)
#     st.image(image, caption="Uploaded Image", use_column_width=True)
    
#     image_bytes = uploaded_file.getvalue()  # Convert uploaded image to bytes for GPT-4o processing - 0310
#     image_description = describe_image(image_bytes)
#     st.session_state.messages.append({"role": "user", "content": "[Uploaded Image]"})  # Store uploaded image reference in chat history - 0310
#     st.session_state.messages.append({"role": "assistant", "content": image_description})  # Store GPT-4o-generated image description in chat history - 0310
    
#     with st.chat_message("assistant"):
#         st.markdown(image_description)
        
# # Accept user input
# if prompt := st.chat_input("Ask your query about civil engineering"):
#     # Add user message to chat history
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     # Display user message in chat message container
#     with st.chat_message("user"):
#         st.markdown(prompt)
#     answer = get_response_content(prompt)
#     # Display assistant response in chat message container
#     with st.chat_message("assistant"):
#         # response = st.write_stream(response_generator())
#         st.markdown(answer)
#     # Add assistant response to chat history
#     # st.session_state.messages.append({"role": "assistant", "content": response})
#     st.session_state.messages.append({"role": "assistant", "content": answer})

if prompt := st.chat_input("Ask your query about civil engineering"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display "I am thinking..." placeholder in assistant's response
    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("I am thinking...")

    # Generate actual response
    answer = get_response_content(prompt)

    # Update the placeholder with the actual response
    thinking_placeholder.markdown(answer)

    # Add assistant response to chat history
    print(f'Final response generated: {answer}')  # Debug print - 0310
    st.session_state.messages.append({"role": "assistant", "content": answer})
