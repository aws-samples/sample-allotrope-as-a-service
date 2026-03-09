#!/usr/bin/env python3
"""
ASM Transformation Edge Client for AWS Greengrass
Monitors laboratory instrument output and securely transmits to cloud ATaaS/DVaaS
"""

import os
import json
import time
import hashlib
import requests
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

class ASMEdgeClient:
    def __init__(self, config_path="/opt/greengrass/config.json"):
        self.config = self.load_config(config_path)
        self.setup_logging()
        
    def load_config(self, config_path):
        """Load configuration from Greengrass component"""
        default_config = {
            "apiGatewayUrl": "https://2utxx41y1l.execute-api.us-east-1.amazonaws.com/prod",
            "watchDirectory": "/opt/instruments/output",
            "logLevel": "INFO",
            "auditEnabled": True
        }
        
        if os.path.exists(config_path):
            with open(config_path) as f:
                return {**default_config, **json.load(f)}
        return default_config
    
    def setup_logging(self):
        """Setup GxP-compliant logging"""
        logging.basicConfig(
            level=getattr(logging, self.config["logLevel"]),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/opt/greengrass/logs/asm_audit.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

class InstrumentFileHandler(FileSystemEventHandler):
    def __init__(self, client):
        self.client = client
        
    def on_created(self, event):
        """Handle new instrument files"""
        if not event.is_directory:
            self.client.process_file(event.src_path)

    def process_file(self, file_path):
        """Process and upload instrument file"""
        try:
            self.logger.info(f"Processing file: {file_path}")
            
            # Calculate file hash for integrity
            file_hash = self.calculate_hash(file_path)
            
            # Upload to ATaaS
            result = self.upload_to_ataas(file_path, file_hash)
            
            # Log audit trail
            self.log_audit(file_path, file_hash, result)
            
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}")
    
    def calculate_hash(self, file_path):
        """Calculate SHA256 hash for file integrity"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def upload_to_ataas(self, file_path, file_hash):
        """Upload file to ATaaS service"""
        url = f"{self.config['apiGatewayUrl']}/convert"
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            headers = {
                'X-File-Hash': file_hash,
                'X-Source': 'greengrass-edge'
            }
            
            response = requests.post(url, files=files, headers=headers, timeout=300)
            response.raise_for_status()
            
            return response.json()
    
    def log_audit(self, file_path, file_hash, result):
        """Log GxP audit trail"""
        audit_entry = {
            "timestamp": time.time(),
            "file_path": file_path,
            "file_hash": file_hash,
            "conversion_result": result.get("status"),
            "asm_generated": result.get("asm_file") is not None,
            "converter_code": result.get("converter_code") is not None
        }
        
        self.logger.info(f"AUDIT: {json.dumps(audit_entry)}")

def main():
    """Main Greengrass component entry point"""
    client = ASMEdgeClient()
    
    # Setup file watcher
    event_handler = InstrumentFileHandler(client)
    observer = Observer()
    observer.schedule(event_handler, client.config["watchDirectory"], recursive=True)
    
    client.logger.info("Starting ASM Edge Client...")
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        client.logger.info("ASM Edge Client stopped")
    
    observer.join()

if __name__ == "__main__":
    main()