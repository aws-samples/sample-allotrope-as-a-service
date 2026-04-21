# Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at http://aws.amazon.com/apache2.0/
# This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import sys
import os

# Add parent directory to path to import converter
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
CORS(app)

ENDPOINTS = {
    'unified': 'https://tqzatn5bse.execute-api.us-east-1.amazonaws.com/prod',
    'dvaas': 'https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod'
}

@app.route('/api/convert', methods=['POST'])
def convert():
    data = request.json
    file_content = data.get('file_content', '')
    file_name = data.get('file_name', '')
    
    # Check if it's a Nova FLEX2 CSV file
    if file_name.endswith('.csv') and 'Sample ID' in file_content and 'pH' in file_content:
        # Use custom Nova FLEX2 converter
        try:
            from nova_flex2_converter import convert_csv_to_asm_batch
            results = convert_csv_to_asm_batch(file_content)
            
            if results and results[0]['success']:
                return jsonify({
                    'conversion_id': 'CUSTOM-NOVA-FLEX2',
                    'method': 'custom_converter',
                    'converter_used': 'nova_flex2',
                    'asm_output': results[0]['asm'],
                    'total_samples': len(results),
                    'success': True
                }), 200
            else:
                return jsonify({'error': 'Conversion failed'}), 500
        except Exception as e:
            print(f"Custom converter error: {e}")
            # Fall through to unified converter
    
    # Use unified converter for other files
    response = requests.post(
        f"{ENDPOINTS['unified']}/convert",
        json=data,
        timeout=60
    )
    return jsonify(response.json()), response.status_code

@app.route('/api/validate', methods=['POST'])
def validate():
    data = request.json
    response = requests.post(
        f"{ENDPOINTS['dvaas']}/validate",
        json=data,
        timeout=30
    )
    return jsonify(response.json()), response.status_code

@app.route('/api/customer-asm', methods=['GET'])
def get_customer_asm():
    """Load customer's original ASM file"""
    try:
        import json
        with open('../demo-samples/SampleResults2025-November-1.json', 'r') as f:
            customer_asm = json.load(f)
        return jsonify(customer_asm), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    print("Starting proxy server...")
    print("Custom Nova FLEX2 converter enabled")
    app.run(port=5000, debug=True)
