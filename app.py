import streamlit as st
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
from EmailProcessor import GET_FILE, SEND_FILE
from gemini import InvoiceExtractor
from config import API_KEY, PROMPT_PATH, OUTPUT_FILE
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

def settings_page():
    st.title("🛠️ Settings")
    
    # Personal Information
    st.subheader("Personal Information")
    name = st.text_input("Your Name", value=st.session_state.get("name", ""))
    email = st.text_input("Email Address", value=st.session_state.get("email", ""))
    
    # Language Preferences
    st.subheader("Language Preferences")
    language = st.selectbox("Choose Language", ("English", "Spanish", "French"), index=["English", "Spanish", "French"].index(st.session_state.get("language", "English")))

    # File Format Preferences
    st.subheader("File Format Preferences")
    file_format = st.radio("Preferred File Format", ("CSV", "Excel"), index=["CSV", "Excel"].index(st.session_state.get("file_format", "CSV")))

    # Save settings to session state
    if st.button("Save Settings"):
        st.session_state.name = name
        st.session_state.email = email
        st.session_state.language = language
        st.session_state.file_format = file_format
        st.success("Settings saved successfully!")

    # Display Current Settings
    st.subheader("Current Settings")
    st.write(f"Name: {st.session_state.get('name', 'Not set')}")
    st.write(f"Email: {st.session_state.get('email', 'Not set')}")
    st.write(f"Language: {st.session_state.get('language', 'Not set')}")
    st.write(f"Preferred File Format: {st.session_state.get('file_format', 'Not set')}")

# Configuration
def main_page():
    st.title("📄 Invoice Parsing App")

    # Input Method Selection
    st.sidebar.header("Upload Method")
    input_method = st.sidebar.radio("Choose an option:", ("Upload File", "Fetch from Gmail"))

    uploaded_file = None
    if input_method == "Upload File":
        uploaded_files = st.file_uploader("Upload Invoices (Image/PDF)", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_ext = uploaded_file.name.split('.')[-1].lower()
                if file_ext in ['jpg', 'jpeg', 'png']:
                    st.image(uploaded_file, caption=f'Preview - {uploaded_file.name}', use_column_width=True)
                elif file_ext == 'pdf':
                    import fitz
                    pdf_document = fitz.open(stream=uploaded_file.read(), filetype='pdf')
                    page = pdf_document.load_page(0)
                    pix = page.get_pixmap()
                    img_path = os.path.join(os.getcwd(), 'downloads', f'preview_{uploaded_file.name}.png')
                    pix.save(img_path)
                    st.image(img_path, caption=f'PDF Preview - {uploaded_file.name}', use_column_width=True)
            file_path = os.path.join(os.getcwd(), "downloads", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"File {uploaded_file.name} uploaded successfully!")
            # Preview File Feature
            file_path = os.path.join("downloads", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"File {uploaded_file.name} uploaded successfully!")

    elif input_method == "Fetch from Gmail":
        st.info("Fetching the latest invoice from Gmail...")
        try:
            GET_FILE()
            st.success("File successfully retrieved from Gmail!")
        except Exception as e:
            st.error(f"Error fetching file: {e}")

    # Parsing Button
    if st.button("Parse Invoice"):
        if uploaded_file or input_method == "Fetch from Gmail":
            extractor = InvoiceExtractor(api_key=API_KEY, prompt_path=PROMPT_PATH)
            file_paths = [os.path.join("downloads/", file) for file in os.listdir("downloads")]
            st.info(file_paths)
            extractor.process_multiple_invoices(file_paths, OUTPUT_FILE)
            st.success("Parsing complete! Data extracted successfully.")
            # Clean up temporary files
            for file in os.listdir(os.path.join(os.getcwd(), "downloads")):
                file_path = os.path.join(os.getcwd(), "downloads", file)
                if file != OUTPUT_FILE:
                    os.remove(file_path)
        else:
            st.warning("Please upload a file or fetch one from Gmail.")

    # Display Results
    if os.path.exists(OUTPUT_FILE):
        df = pd.read_csv(OUTPUT_FILE)
        st.subheader("Extracted Data Preview")
        st.dataframe(df.head(3))
        
        # Download & Send Options
        st.download_button(
            label="Download CSV",
            data=open(OUTPUT_FILE, "rb").read() if OUTPUT_FILE else None,
            file_name="parsed_invoice.csv",
            mime="text/csv"
        )
        recipient_email = st.text_input("Recipient Email Address")
        if st.button("Send via Gmail"):
            if recipient_email and "@" in recipient_email:
                SEND_FILE(recipient_email)
                st.success(f"File sent successfully to {recipient_email}!")
                os.remove(["processed_invoice.jpg", "temp_page_image.png", "final_binarized_invoice.jpg"] )
            else:
                st.error("Please enter a valid email address.")


def app():
    pages = ["Main Page", "Settings"]
    selected_page = st.sidebar.radio("Select a page:", pages)

    if selected_page == "Main Page":
        main_page()
    elif selected_page == "Settings":
        settings_page()

if __name__ == "__main__":
    app()