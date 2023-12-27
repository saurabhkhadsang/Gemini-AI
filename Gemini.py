import streamlit as st
import google.generativeai as genai
import PIL.Image
from io import BytesIO
import textwrap


# Configure API key
GOOGLE_API_KEY = "GOOGLE_API_KEY"  # Replace with your actual API key
genai.configure(api_key=GOOGLE_API_KEY)

# Function to format text as Markdown
def to_markdown(parts):
    text = "".join(part.text for part in parts)
    text = text.replace('•', '  *')
    return textwrap.indent(text, '> ', predicate=lambda _: True)

# Function to process the uploaded image
def process_uploaded_image(uploaded_file):
    if uploaded_file is not None:
        # Read the image file
        image = PIL.Image.open(uploaded_file)
        return image
    return None

# Streamlit app
st.title("Gemini-AI")

# List available models
models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]

# Display information about the available models
st.subheader('Available Models:')
for m in models:
    st.write(f"- {m}")

# Select the model
selected_model = st.selectbox('Select a model:', models, index=0)
model = genai.GenerativeModel(selected_model)

# Input prompt
prompt_key = "prompt_input"
prompt = st.text_area('Enter your prompt:', "Write code for a linked list in C++ with an explanation.", key=prompt_key)

# Display the uploaded image if available
image = None
if selected_model == 'models/gemini-pro-vision':
    uploaded_image = st.file_uploader("Upload an image file (JPG or PNG)", type=["jpg", "png"])
    image = process_uploaded_image(uploaded_image)

    if image:
        st.image(image, caption="Uploaded Image", use_column_width=True)

# Generate content
generate_button_key = "generate_button"
if st.button('Generate', key=generate_button_key):
    # Create an empty container for the response
    response_container = st.empty()

    if selected_model == 'models/gemini-pro-vision' and image:
        response = model.generate_content([prompt, image], stream=True)
        response.resolve()
    else:
        response = model.generate_content(prompt)

    # Check if there are any candidates in the response
    if response.candidates:
        # Check if text is available in the first candidate
        if hasattr(response.candidates[0], 'content') and hasattr(response.candidates[0].content, 'parts'):
            # Display response above the input question
            response_container.markdown(to_markdown(response.candidates[0].content.parts), unsafe_allow_html=True)
        else:
            # If parts are not available, show a message
            st.warning("The response does not contain parts.")
    else:
        # If there are no candidates, show a message
        st.warning("No candidates returned. Check the response.prompt_feedback to see if the prompt was blocked.")

        # Print the level of unsafe content
        st.subheader("Probability of Unsafe Content:")
        for rating in response.prompt_feedback.safety_ratings:
            category_mapping = {
                9: "Hate Speech",
                8: "Harassment",
                7: "Dangerous Content",
                10: "Sexually Explicit"
            }
            category_label = category_mapping.get(rating.category, "Unknown Category")
            probability_label = "High" if rating.probability >= 4 else "Medium" if rating.probability >= 2 else "Low"

            st.warning(f"{category_label}: {probability_label}")
