# Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at http://aws.amazon.com/apache2.0/
# This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
"""Read CDK stack outputs and update dashboard/src/config.js with correct endpoints."""

import json
import subprocess
import sys


def get_stack_outputs():
    """Get outputs from the deployed CDK stack."""
    try:
        result = subprocess.run(
            ["aws", "cloudformation", "describe-stacks", "--stack-name", "AutonomousServicesStack"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            print("Make sure the backend services are deployed first (cd services && cdk deploy)")
            sys.exit(1)

        stacks = json.loads(result.stdout)
        outputs = {}
        for output in stacks["Stacks"][0]["Outputs"]:
            outputs[output["OutputKey"]] = output["OutputValue"]
        return outputs
    except FileNotFoundError:
        print("Error: AWS CLI not found. Install it and run 'aws configure'.")
        sys.exit(1)


def update_config(outputs):
    """Write config.js with the correct endpoints."""
    # Map CDK output keys to config keys
    endpoint_map = {
        "unifiedConverter": "UnifiedConverterAPIEndpoint",
        "dvaas": "DVaaSAPIEndpoint",
        "customConverter": "CustomConverterAPIEndpoint",
        "ataas": "ATaaSAPIEndpoint",
        "multiInstrument": "MultiInstrumentAPIEndpoint",
    }

    config_lines = ["// API Endpoints - Update these when deploying to a new environment"]
    config_lines.append("export const ENDPOINTS = {")

    for config_key, output_key in endpoint_map.items():
        # Try both possible output key formats (CDK generates two)
        url = outputs.get(output_key, "")
        if not url:
            # Try the auto-generated key format
            for k, v in outputs.items():
                if output_key.replace("APIEndpoint", "") in k and "execute-api" in v:
                    url = v
                    break

        # Remove trailing slash for consistency
        url = url.rstrip("/")

        config_lines.append(f"  {config_key}: '{url}',")

    config_lines.append("}")
    config_lines.append("")
    config_lines.append("// API Key - set after deployment if API key protection is enabled")
    config_lines.append("export const API_KEY = ''")
    config_lines.append("")
    config_lines.append("export function apiHeaders(contentType = 'application/json') {")
    config_lines.append("  const headers = { 'Content-Type': contentType }")
    config_lines.append("  if (API_KEY) headers['x-api-key'] = API_KEY")
    config_lines.append("  const token = localStorage.getItem('asm_token')")
    config_lines.append("  if (token) headers['Authorization'] = `Bearer ${token}`")
    config_lines.append("  return headers")
    config_lines.append("}")
    config_lines.append("")
    config_lines.append("export async function authFetch(url, options = {}) {")
    config_lines.append("  const opts = { ...options, headers: { ...apiHeaders(), ...options.headers } }")
    config_lines.append("  const response = await fetch(url, opts)")
    config_lines.append("  if (response.status === 401 || response.status === 403) {")
    config_lines.append("    localStorage.removeItem('asm_token')")
    config_lines.append("    localStorage.removeItem('asm_user')")
    config_lines.append("    window.location.reload()")
    config_lines.append("    throw new Error('Session expired. Please log in again.')")
    config_lines.append("  }")
    config_lines.append("  return response")
    config_lines.append("}")
    config_lines.append("")

    config_content = "\n".join(config_lines)

    with open("src/config.js", "w", encoding="utf-8") as f:
        f.write(config_content)

    print("Updated src/config.js:")
    print(config_content)


if __name__ == "__main__":
    print("Reading CDK stack outputs...")
    outputs = get_stack_outputs()
    print(f"Found {len(outputs)} outputs")
    update_config(outputs)
    print("\nDone. Now run: npm run build && cdk deploy --require-approval never")
