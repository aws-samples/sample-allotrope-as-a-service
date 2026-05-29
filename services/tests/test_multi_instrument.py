# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import pytest


# ---------------------------------------------------------------------------
# detect_instrument_type
# ---------------------------------------------------------------------------

class TestDetectInstrumentType:
    def test_plate_reader_well(self, multi_mod):
        assert multi_mod.detect_instrument_type("well A1 value 0.5", "unknown") == "plate_reader"

    def test_plate_reader_absorbance(self, multi_mod):
        assert multi_mod.detect_instrument_type("absorbance reading 0.3", "unknown") == "plate_reader"

    def test_plate_reader_od(self, multi_mod):
        assert multi_mod.detect_instrument_type("OD measurement 0.8", "unknown") == "plate_reader"

    def test_cell_counter_viability(self, multi_mod):
        assert multi_mod.detect_instrument_type("cell viability 95%", "unknown") == "cell_counter"

    def test_cell_counter_count(self, multi_mod):
        assert multi_mod.detect_instrument_type("cell count measurement", "unknown") == "cell_counter"

    def test_solution_analyzer_concentration(self, multi_mod):
        content = "concentration ph temperature sample"
        assert multi_mod.detect_instrument_type(content, "unknown") == "solution_analyzer"

    def test_default_fallback(self, multi_mod):
        assert multi_mod.detect_instrument_type("unrecognized content here", "unknown") == "solution_analyzer"


# ---------------------------------------------------------------------------
# convert_plate_reader
# ---------------------------------------------------------------------------

class TestConvertPlateReader:
    def test_manifest_url(self, multi_mod):
        result = multi_mod.convert_plate_reader("header\nA1,0.5\n", "test")
        assert "plate-reader" in result["$asm.manifest"]

    def test_measurement_document_structure(self, multi_mod):
        csv = "well,absorbance\nA1,0.5\nA2,0.8\n"
        result = multi_mod.convert_plate_reader(csv, "test-vendor")
        assert "measurement document" in result
        assert len(result["measurement document"]) == 2

    def test_empty_input_returns_empty_doc(self, multi_mod):
        result = multi_mod.convert_plate_reader("only header\n", "test")
        assert "measurement document" in result
        assert len(result["measurement document"]) == 0

    def test_measurement_ids_unique(self, multi_mod):
        csv = "well,absorbance\nA1,0.5\nA2,0.8\nA3,1.1\n"
        result = multi_mod.convert_plate_reader(csv, "test")
        ids = [m["measurement identifier"] for m in result["measurement document"]]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# convert_cell_counter
# ---------------------------------------------------------------------------

class TestConvertCellCounter:
    def test_manifest_url(self, multi_mod):
        result = multi_mod.convert_cell_counter("header\nS1,500000,95.0\n", "test")
        assert "cell-counter" in result["$asm.manifest"]

    def test_measurement_document_populated(self, multi_mod):
        csv = "NAME,SAMPLE ID,TOTAL\nSAMPLE-1,S001,500000\nSAMPLE-2,S002,350000\n"
        result = multi_mod.convert_cell_counter(csv, "test")
        assert len(result["measurement document"]) == 2

    def test_with_real_example_csv(self, multi_mod, cell_counter_csv):
        result = multi_mod.convert_cell_counter(cell_counter_csv, "chemometec")
        assert isinstance(result["measurement document"], list)
        assert len(result["measurement document"]) > 0

    def test_single_line_empty(self, multi_mod):
        result = multi_mod.convert_cell_counter("header only\n", "test")
        assert len(result["measurement document"]) == 0


# ---------------------------------------------------------------------------
# convert_solution_analyzer
# ---------------------------------------------------------------------------

class TestConvertSolutionAnalyzer:
    def test_manifest_url(self, multi_mod):
        result = multi_mod.convert_solution_analyzer("header\nS1,4.5,7.1,37.0\n", "test")
        assert "solution-analyzer" in result["$asm.manifest"]

    def test_measurement_document_populated(self, multi_mod):
        csv = "sample,conc,ph,temp\nS001,4.5,7.1,37.0\nS002,3.2,7.3,36.5\n"
        result = multi_mod.convert_solution_analyzer(csv, "test")
        assert len(result["measurement document"]) == 2

    def test_empty_returns_empty_doc(self, multi_mod):
        result = multi_mod.convert_solution_analyzer("header\n", "test")
        assert len(result["measurement document"]) == 0

    def test_measurement_time_present(self, multi_mod):
        csv = "sample,conc\nS001,4.5\n"
        result = multi_mod.convert_solution_analyzer(csv, "test")
        docs = result["measurement document"]
        assert len(docs) > 0
        assert "measurement time" in docs[0]
