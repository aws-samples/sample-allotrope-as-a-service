#!/usr/bin/env python3
# Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at http://aws.amazon.com/apache2.0/
# This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
"""
Bundle DVaaS Lambda with dependencies including reportlab
"""

import os
import shutil
import subprocess
import sys

def bundle_dvaas():
    print("Bundling DVaaS Lambda with dependencies...")
    
    # Create temp directory
    bundle_dir = "dvaas-bundle"
    if os.path.exists(bundle_dir):
        shutil.rmtree(bundle_dir)
    os.makedirs(bundle_dir)
    
    # Copy Lambda code
    print("Copying Lambda code...")
    shutil.copy("dvaas/lambda_function.py", f"{bundle_dir}/lambda_function.py")
    shutil.copy("dvaas/validate_asm.py", f"{bundle_dir}/validate_asm.py")
    shutil.copy("dvaas/generate_certification_report.py", f"{bundle_dir}/generate_certification_report.py")
    
    # Install dependencies
    print("Installing dependencies...")
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "-r", "dvaas/requirements.txt",
        "-t", bundle_dir,
        "--upgrade"
    ], check=True)
    
    print(f"\nBundle created in {bundle_dir}/")
    print("Update CDK to use this directory:")
    print(f'  code=_lambda.Code.from_asset("{bundle_dir}")')
    
    return bundle_dir

if __name__ == "__main__":
    bundle_dvaas()
