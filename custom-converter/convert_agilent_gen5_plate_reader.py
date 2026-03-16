# Copyright 2024 Benchling Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Convert Agilent Gen5 plate reader TXT export to Allotrope Simple Model (ASM) JSON."""

import argparse
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_INPUT = (
    "testdata/plate_reader/agilent_gen5/"
    "010307_114129_BNCH654563_stdcurve_singleplate01.txt"
)
ASM_MANIFEST = (
    "http://purl.allotrope.org/manifests/plate-reader/REC/2025/12/plate-reader.manifest"
)


def parse_header(lines: list[str]) -> dict:
    """Extract instrument metadata from the file header.

    Args:
        lines: All lines from the input file.

    Returns:
        Dict with keys: software_version, date, time, reader_type, reader_serial,
        experiment_file, protocol_file, plate_number.
    """
    meta: dict = {}
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("Software Version"):
            parts = stripped.split("\t")
            meta["software_version"] = parts[1].strip() if len(parts) > 1 else ""
        elif stripped.startswith("Date\t"):
            meta["date"] = stripped.split("\t", 1)[1].strip()
        elif stripped.startswith("Time\t"):
            meta["time"] = stripped.split("\t", 1)[1].strip()
        elif stripped.startswith("Reader Type:"):
            meta["reader_type"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Reader Serial Number:"):
            meta["reader_serial"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Experiment File Path:"):
            meta["experiment_file"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Protocol File Path:"):
            meta["protocol_file"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Plate Number"):
            meta["plate_number"] = stripped.split("\t", 1)[1].strip()
    return meta


def parse_timestamp(date_str: str, time_str: str) -> str:
    """Parse date and time strings into ISO 8601 UTC timestamp.

    Args:
        date_str: Date in M/D/YYYY format (e.g. '10/10/2022').
        time_str: Time in H:MM:SS AM/PM format (e.g. '9:00:04 PM').

    Returns:
        ISO 8601 string with UTC offset, e.g. '2022-10-10T21:00:04+00:00'.
    """
    combined = f"{date_str} {time_str}"
    dt = datetime.strptime(combined, "%m/%d/%Y %I:%M:%S %p")
    return dt.replace(tzinfo=timezone.utc).isoformat()


def parse_results(lines: list[str]) -> list[dict]:
    """Parse the Results section into a list of well measurement dicts.

    Only the primary absorbance rows (labelled '630nmAbsRead:630') are extracted.

    Args:
        lines: All lines from the input file.

    Returns:
        List of dicts with keys: location_identifier, absorbance_value.
    """
    # Find the Results section
    results_start = None
    for i, line in enumerate(lines):
        if line.strip() == "Results":
            results_start = i
            break
    if results_start is None:
        raise ValueError("Could not find 'Results' section in file.")

    # The header row after "Results" contains column numbers
    header_line = lines[results_start + 1].strip()
    col_numbers = header_line.split("\t")[1:]  # skip leading empty cell

    measurements = []
    row_letter = None
    i = results_start + 2

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Stop at next section
        if stripped.startswith("StdCurve") or stripped == "":
            if stripped.startswith("StdCurve"):
                break
            i += 1
            continue

        parts = line.rstrip("\n").split("\t")

        # A row starting with a letter is the absorbance row
        if parts[0] and parts[0][0].isalpha() and len(parts[0]) == 1:
            row_letter = parts[0]
            values = parts[1:]
            # Determine which sub-row this is by checking the label at the end
            label = values[-1].strip() if values else ""
            if "630nmAbsRead:630" in label and "Blank" not in label:
                data_values = values[:-1]  # drop the label column
                for col_idx, val in enumerate(data_values):
                    val = val.strip()
                    if val == "" or col_idx >= len(col_numbers):
                        continue
                    col_num = col_numbers[col_idx].strip()
                    if not col_num:
                        continue
                    location = f"{row_letter}{col_num}"
                    measurements.append({
                        "location_identifier": location,
                        "absorbance_value": float(val),
                    })
        elif parts[0] == "" and row_letter is not None:
            # Continuation sub-row — check label
            values = parts[1:]
            label = values[-1].strip() if values else ""
            if "630nmAbsRead:630" in label and "Blank" not in label:
                data_values = values[:-1]
                for col_idx, val in enumerate(data_values):
                    val = val.strip()
                    if val == "" or col_idx >= len(col_numbers):
                        continue
                    col_num = col_numbers[col_idx].strip()
                    if not col_num:
                        continue
                    location = f"{row_letter}{col_num}"
                    measurements.append({
                        "location_identifier": location,
                        "absorbance_value": float(val),
                    })
        i += 1

    return measurements


def build_asm(meta: dict, measurements: list[dict], wavelength_nm: float = 630.0) -> dict:
    """Construct the ASM JSON document.

    Args:
        meta: Instrument metadata from parse_header().
        measurements: Well measurements from parse_results().
        wavelength_nm: Detector wavelength in nanometres.

    Returns:
        Dict representing the full ASM document.
    """
    timestamp = parse_timestamp(meta["date"], meta["time"])

    measurement_documents = []
    for m in measurements:
        measurement_documents.append({
            "measurement identifier": str(uuid.uuid4()),
            "absorbance": {
                "unit": "mAU",
                "value": m["absorbance_value"],
            },
            "device control aggregate document": {
                "device control document": [
                    {
                        "device type": "UV detector",
                        "detector wavelength setting": {
                            "unit": "nm",
                            "value": wavelength_nm,
                        },
                    }
                ]
            },
            "sample document": {
                "location identifier": m["location_identifier"],
                "sample identifier": m["location_identifier"],
            },
        })

    device_identifier = meta.get("reader_serial", "n/a")
    model_number = meta.get("reader_type", "n/a")

    return {
        "$asm.manifest": ASM_MANIFEST,
        "plate reader aggregate document": {
            "plate reader document": [
                {
                    "device system document": {
                        "device identifier": device_identifier,
                        "model number": model_number,
                        "data system document": {
                            "file name": meta.get("experiment_file", ""),
                            "software name": "Gen5",
                            "software version": meta.get("software_version", ""),
                            "ASM file identifier": str(uuid.uuid4()),
                        },
                    },
                    "measurement aggregate document": {
                        "measurement time": timestamp,
                        "plate well count": {
                            "unit": "#",
                            "value": 96.0,
                        },
                        "container type": "well plate",
                        "measurement document": measurement_documents,
                    },
                }
            ]
        },
    }


def convert(input_path: str, output_path: str) -> None:
    """Read instrument data and write ASM JSON to output_path.

    Args:
        input_path: Path to the Agilent Gen5 TXT file.
        output_path: Destination path for the ASM JSON file.
    """
    text = Path(input_path).read_text(encoding="utf-8")
    lines = text.splitlines()

    meta = parse_header(lines)
    measurements = parse_results(lines)
    asm = build_asm(meta, measurements)

    Path(output_path).write_text(json.dumps(asm, indent=2), encoding="utf-8")
    print(f"Wrote {len(measurements)} measurements to {output_path}")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Convert Agilent Gen5 plate reader data to ASM JSON.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Path to input TXT file")
    parser.add_argument(
        "--output",
        default=None,
        help="Path to output ASM JSON file (default: <input>.asm.json)",
    )
    args = parser.parse_args()

    output = args.output or args.input + ".asm.json"
    convert(args.input, output)


if __name__ == "__main__":
    main()
