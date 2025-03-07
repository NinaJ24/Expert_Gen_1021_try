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

# --added
# 初始化 session_state 变量
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None



def encode_image(image_bytes):

    return base64.b64encode(image_bytes).decode("utf-8")


def describe_image(uploaded_file):

    try:
        if uploaded_file is None:
            return "No image uploaded or pasted."

        # Send image to GPT-4o Vision model
        # base64_image = encode_image(image_bytes)  

        image = Image.open(uploaded_file)
# -------------------convert to legal format------
        # Ensure the image is in a supported format
        if image.mode in ("RGBA", "P"):  # Convert images with transparency to RGB
            image = image.convert("RGB")

        # Save the image as a clean, standard PNG or JPEG
        image_buffer = io.BytesIO()
        image.save(image_buffer, format="PNG")  # Ensure valid PNG format
        image_bytes = image_buffer.getvalue()
        # -------------------convert to legal format------
        # image_bytes = uploaded_file.read()

        # Encode the image bytes
        base64_image = encode_image(image_bytes)
        # base64_image = encode_image(uploaded_file)  
        
        response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "You are an AI specialized in extracting text, questions, tables, and figures from uploaded images. Extract only the questions, tables, and diagrams without adding explanations or unnecessary details. Maintain the original structure of the content as much as possible.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
    )

        st.session_state.uploaded_file = None # added to clear
        return response.choices[0].message.content  # Return AI-generated response

    except Exception as e:
        return f"Error processing the image: {str(e)}"

def get_response_content(query):
    # Create a Message object using the input text
    msg = Message(content=query)

    # Call the chat function with the Message object
    resp = assistant.chat(messages=[msg])

    # Extract the content part of the response
    answer = resp.get("message", {}).get("content", "")

    # Output and return the content part
    # print(answer)
    # display(Markdown(content_text))
    # print(f'get_response_content: {answer}')  # Debug print - 0310
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


def process_input(uploaded_file=None, prompt=""): 
    image_description = ""  # Variable to store extracted text from image
    # Step 1: Process Uploaded Image
    if uploaded_file:
        if isinstance(uploaded_file, io.BytesIO):
            image = Image.open(uploaded_file)
        else:
            image = uploaded_file  # Directly use pasted images if they are already PIL objects

        # Display the uploaded image
        st.image(image, caption="Uploaded Image", use_container_width=True)

        # # Convert image to bytes for processing
        # image_bytes = io.BytesIO()
        # if isinstance(image, Image.Image):  
        #     image.save(image_bytes, format="PNG")
        # else:
        #     image_bytes.write(uploaded_file.getvalue())
        # image_bytes = image_bytes.getvalue()

        # Extract text, tables, and figures from the image using GPT-4o
        # image_description = describe_image(image_bytes)
        
        image_description = describe_image(uploaded_file)

        # Store extracted content in chat history
        st.session_state.messages.append({"role": "assistant", "content": f"**Extracted Content from Image:**\n{image_description}"})

        # Display extracted content
        with st.chat_message("assistant"):
            st.markdown(f"**Extracted Content from Image:**\n\n{image_description}")

    # Step 2: Combine Extracted Image Text with User Prompt
    combined_prompt = f"{image_description}\n\nUser Query: {prompt}".strip() if image_description else prompt
    st.session_state.uploaded_file = None
    return combined_prompt  # Only return the combined prompt




# uploaded_file = st.file_uploader("Upload an image or paste from clipboard", type=["png", "jpg", "jpeg"], accept_multiple_files=False)  # Enabled clipboard paste support for images - 0310  # Allow users to upload images for AI processing - 0310

# paste_result = pbutton("📋 Paste an image")
# added/=========
# **文件上传区域**
uploaded_file = st.file_uploader("Upload an image or paste from clipboard", type=["png", "jpg", "jpeg"])
if uploaded_file:
    st.session_state.uploaded_file = uploaded_file

# **粘贴按钮**
paste_result = pbutton("📋 Paste an image")
if paste_result.image_data is not None:
    st.session_state.uploaded_file = paste_result.image_data

# **确保上传文件被正确存储**
if st.session_state.uploaded_file:
    uploaded_file = st.session_state.uploaded_file
# added/=========


if paste_result.image_data is not None:  # Corrected variable name for pasted image - 0310
    uploaded_file = paste_result.image_data  # Use correct attribute for clipboard pasting - 0310  # Enabled clipboard paste support for images - 0310  # Allow users to upload images for AI processing - 0310
# prompt = st.chat_input("Ask your query about civil engineering")
# combined_prompt = process_input(uploaded_file=uploaded_file, prompt=prompt)

if prompt := st.chat_input("Ask your query about civil engineering"):
   
    combined_prompt =  process_input(uploaded_file, prompt)
    enhanced_prompt = f"{combined_prompt} Explain why and also provide me the source cited text"
    st.session_state.messages.append({"role": "user", "content": enhanced_prompt})

    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt if prompt else "[Uploaded Image]")  # Show text prompt or an image placeholder

    # Display "I am thinking..." placeholder in assistant's response
    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("I am thinking...")

    # Generate actual response using the assistant
    answer = get_response_content(enhanced_prompt)  # Use the processed combined prompt

    # Update the placeholder with the actual response
    thinking_placeholder.markdown(answer)

    # Add assistant response to chat history
    print(f'Final response generated: {answer}')  # Debug print - 0310
    st.session_state.messages.append({"role": "assistant", "content": answer})
        # 存储回答
    # st.session_state.messages.append({"role": "assistant", "content": answer})

    # # **关键：自动清除图片并刷新页面**
    # st.session_state.uploaded_file = None
    # st.rerun()
    # **关键：清除上传的图片，并刷新页面**
    st.session_state.uploaded_file = None  # ✅ 清除上传的图片
    st.session_state.pasted_image = None  # ✅ 清除粘贴的图片
    st.rerun()  # ✅ 让 UI 重新加载，确保 `file_uploader` 变为空
