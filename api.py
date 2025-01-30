from flask import Flask, request, jsonify, send_file
import os
import shutil
from werkzeug.utils import secure_filename
from EmailProcessor import GET_FILE, SEND_FILE
from gemini import parser
import pandas as pd
from flask_cors import CORS



UPLOAD_FOLDER = 'downloads'
PROCESSED_FILE = 'output.csv'

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_files():
    """Endpoint to upload invoice files."""
    if 'files' not in request.files:
        return jsonify({"error": "No files part in the request."}), 400

    files = request.files.getlist('files')
    for file in files:
        if file.filename == '':
            return jsonify({"error": "No selected file."}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

    return jsonify({"message": "Files successfully uploaded."}), 200

@app.route('/parse-invoices', methods=['GET'])
def parse_invoices():
    """Endpoint to parse uploaded invoice files."""
    try:
        if not os.listdir(UPLOAD_FOLDER):
            return jsonify({"error": "No files available for processing."}), 400

        parser()  # This will process and generate the CSV output
        if not os.path.exists(PROCESSED_FILE):
            return jsonify({"error": "Failed to process invoices."}), 500

        df = pd.read_csv(PROCESSED_FILE)
        data_preview = df.head(5).to_dict(orient='records')

        return jsonify({"message": "Parsing successful.", "data": data_preview}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/send-email', methods=['POST'])
def send_invoice_email():
    """Endpoint to send parsed invoice data via email."""
    data = request.json
    recipient_email = data.get('email')

    if not recipient_email or '@' not in recipient_email:
        return jsonify({"error": "Invalid email address."}), 400

    try:
        SEND_FILE(recipient_email)
        return jsonify({"message": f"File successfully sent to {recipient_email}."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/fetch-latest-invoice', methods=['GET'])
def fetch_latest_invoice():
    """Endpoint to fetch the latest invoice from Gmail."""
    try:
        GET_FILE()
        return jsonify({"message": "Latest invoice successfully fetched from Gmail."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download-parsed-file', methods=['GET'])
def download_parsed_file():
    """Endpoint to download the processed CSV file."""
    if os.path.exists(PROCESSED_FILE):
        return send_file(PROCESSED_FILE, as_attachment=True)
    return jsonify({"error": "Processed file not found."}), 404

if __name__ == '__main__':
    app.run(debug=True)
