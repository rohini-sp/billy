import json
import google.generativeai as genai
import PIL.Image
import pandas as pd
import time
import os
import fitz  
from config import API_KEY
from preprocessor import InvoiceImageProcessor  

class InvoiceExtractor:
    def __init__(self, api_key: str, prompt_path: str):
        """Initialize the InvoiceExtractor with the provided API key and prompt file."""

        self.api_key = api_key
        self.prompt_path = prompt_path
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        self.prompt = self.read_prompt()  # Read the prompt during initialization

    def open_image(self, image_path: str) -> PIL.Image.Image:

        """Open the image file for invoice extraction."""

        return PIL.Image.open(image_path)

    def generate_invoice_data(self, image: PIL.Image.Image) -> dict:

        """Generate invoice data by interacting with the Generative Model."""

        time.sleep(2)  # Delay to ensure the model is ready
        response = self.model.generate_content([self.prompt, image])
        
        # Clean up and load response into JSON
        data = response.text.strip("`").strip("json")
        try:
            json_data = json.loads(data)
            return json_data
        except json.JSONDecodeError:
            raise ValueError("The response text could not be parsed as JSON.")

    def save_to_csv(self, data: list, output_file: str):

        """Convert extracted JSON data to a DataFrame and save it as CSV."""

        df = pd.json_normalize(data)
        df.to_csv(output_file, index=False)
        print(f"JSON data has been successfully converted to {output_file}")

    def process_invoice(self, file_path: str) -> dict:

        """Complete the invoice extraction process for a single file (image or PDF)."""

        file_type = self.get_file_type(file_path)
        
        if file_type == "image":
            return self.process_image_invoice(file_path)
        elif file_type == "pdf":
            return self.process_pdf_invoice(file_path)
        else:
            raise ValueError("Unsupported file type: should be either image or PDF.")

    def process_image_invoice(self, image_path: str) -> dict:

        """Process invoice when the file is an image."""

        # Process the image (binarize and enhance sharpness)
        image_processor = InvoiceImageProcessor(image_path)
        binarized_image_path = image_processor.process_image()
        print(f"Processed image saved at: {binarized_image_path}")

        # Open the binarized image for further processing
        image = self.open_image(binarized_image_path)
        
        # Generate invoice data
        data = self.generate_invoice_data(image)
        return data

    def process_pdf_invoice(self, pdf_path: str) -> dict:

        """Process invoice when the file is a PDF."""


        # Extract the first page from the PDF as an image
        pdf_document = fitz.open(pdf_path)
        page = pdf_document.load_page(0)  # Extract the first page
        pix = page.get_pixmap()  # Convert page to image
        img_path = "temp_page_image.png"
        pix.save(img_path)
        
        print(f"Extracted page saved as image: {img_path}")
        
        # Now process the image like in process_image_invoice
        return self.process_image_invoice(img_path)

    def get_file_type(self, file_path: str) -> str:

        """Determine the file type (image or pdf) based on the file extension."""


        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
            return "image"
        elif file_extension == '.pdf':
            return "pdf"
        else:
            return "unknown"

    def process_multiple_invoices(self, file_paths: list, output_file: str):
        """Process multiple invoices in batch."""


        all_data = []
        for file_path in file_paths:
            print(f"Processing invoice: {file_path}")
            data = self.process_invoice(file_path)
            all_data.append(data)
        
        # Save the extracted data for all invoices to a CSV
        self.save_to_csv(all_data, output_file)

    def read_prompt(self) -> str:
        """Read the prompt from the provided text file."""
        with open(self.prompt_path, 'r', encoding='utf-8') as file:
            return file.read()


# Usage Example:
def extraction():

    # Initialize the InvoiceExtractor object with API key and prompt file path
    extractor = InvoiceExtractor(API_KEY, r"prompt.txt")

    # List of paths to the invoice files (images or PDFs)
    file_paths = [os.path.join("downloads/", file) for file in os.listdir("downloads")]
    
    output_file = 'output.csv'

    # Process the invoices in batch
    extractor.process_multiple_invoices(file_paths, output_file)


