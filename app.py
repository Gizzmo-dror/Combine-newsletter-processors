from flask import Flask, request, jsonify
from processor_v1 import process_email as process_creativity_daily
from processor_v2 import process_email as process_aotw
from processor_creative_bloq import process_email as process_creative_bloq
from processor_campaign_brief import process_email as process_campaign_brief
import logging
import json

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

@app.route('/process_email', methods=['POST'])
def process_email():
    logging.debug(f"Received request data: {request.data}")
    try:
        data = json.loads(request.data)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON: {e}")
        return jsonify({"error": "Invalid JSON format"}), 400

    if not data:
        logging.error("No JSON data received")
        return jsonify({"error": "No JSON data received"}), 400
    
    logging.debug(f"Parsed JSON data: {data}")
    
    if 'metadata' not in data:
        logging.error("Missing 'metadata' field in JSON")
        return jsonify({"error": "Missing 'metadata' field"}), 400
    
    if 'sender' not in data['metadata']:
        logging.error("Missing 'sender' field in metadata")
        return jsonify({"error": "Missing 'sender' field in metadata"}), 400
    
    sender = data['metadata']['sender']
    logging.debug(f"Sender: {sender}")
    
    if "adage@e.crainalerts.com" in sender:
        logging.debug("Processing as Creativity Daily")
        return process_creativity_daily(data)
    elif "newsletter@adsoftheworld.com" in sender:
        logging.debug("Processing as Ads of the World")
        return process_aotw(data)
    elif "creativebloq@smartbrief.com" in sender:
        logging.debug("Processing as Creative Bloq")
        return process_creative_bloq(data)
    elif "no-reply@campaignbrief.com" in sender or "no-reply@campaignbrief.co.nz" in sender:
        logging.debug("Processing as Campaign Brief")
        return process_campaign_brief(data)
    else:
        logging.error(f"Unknown newsletter source: {sender}")
        return jsonify({"error": f"Unknown newsletter source: {sender}"}), 400

application = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)