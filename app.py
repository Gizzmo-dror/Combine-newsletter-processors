from flask import Flask, request, jsonify
from processor_v1 import process_email as process_creativity_daily
from processor_v2 import process_email_content as process_aotw
from processor_creative_bloq import process_email as process_creative_blog
from processor_campaign_brief import process_email as process_campaign_brief
from processor_adweek_agency_daily import process_email as process_adweek_agency_daily
import logging
import json
import os
from celery import Celery
from celery.exceptions import OperationalError

app = Flask(__name__)
celery = Celery('tasks', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379'))
logging.basicConfig(level=logging.DEBUG)

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
    
    try:
        if "adage@e.crainalerts.com" in sender:
            logging.debug("Processing as Creativity Daily")
            return process_creativity_daily(data)
        elif "newsletter@adsoftheworld.com" in sender:
            logging.debug("Processing as Ads of the World")
            try:
                task = process_aotw.delay(data)
                logging.debug(f"Task created with id: {task.id}")
                return jsonify({"task_id": task.id}), 202
            except OperationalError as e:
                logging.error(f"Celery OperationalError: {str(e)}")
                return jsonify({"error": "Failed to queue task. Celery may be unavailable."}), 503
            except Exception as e:
                logging.error(f"Failed to queue task: {str(e)}")
                return jsonify({"error": "Failed to process request"}), 500
        elif "creativebloq@smartbrief.com" in sender:
            logging.debug("Processing as Creative Bloq")
            return process_creative_blog(data)
        elif "no-reply@campaignbrief.com" in sender or "no-reply@campaignbrief.co.nz" in sender:
            logging.debug("Processing as Campaign Brief")
            return process_campaign_brief(data)
        elif "email@email.adweek.com" in sender:
            logging.debug("Processing as Adweek Advertising & Agency Daily")
            return process_adweek_agency_daily(data)
        else:
            logging.error(f"Unknown newsletter source: {sender}")
            return jsonify({"error": f"Unknown newsletter source: {sender}"}), 400
    except Exception as e:
        logging.error(f"Unexpected error in process_email: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    try:
        task = process_aotw.AsyncResult(task_id)
        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'status': 'Task is pending...'
            }
        elif task.state != 'FAILURE':
            response = {
                'state': task.state,
                'status': task.info.get('status', '')
            }
            if 'result' in task.info:
                response['result'] = task.info['result']
        else:
            response = {
                'state': task.state,
                'status': str(task.info)
            }
        return jsonify(response)
    except Exception as e:
        logging.error(f"Error checking task status: {str(e)}")
        return jsonify({"error": "Failed to check task status"}), 500

# The rest of the routes (home, health_check) remain the same...

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

application = app