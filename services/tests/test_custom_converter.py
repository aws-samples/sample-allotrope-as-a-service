# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import pytest


# ---------------------------------------------------------------------------
# _safe_import
# ---------------------------------------------------------------------------

class TestSafeImport:
    def test_allows_csv(self, custom_mod):
        import csv as real_csv
        result = custom_mod._safe_import("csv")
        assert result is real_csv

    def test_allows_datetime(self, custom_mod):
        import datetime as real_dt
        result = custom_mod._safe_import("datetime")
        assert result is real_dt

    def test_allows_re(self, custom_mod):
        import re as real_re
        result = custom_mod._safe_import("re")
        assert result is real_re

    def test_allows_uuid(self, custom_mod):
        import uuid as real_uuid
        result = custom_mod._safe_import("uuid")
        assert result is real_uuid

    def test_allows_json(self, custom_mod):
        import json as real_json
        result = custom_mod._safe_import("json")
        assert result is real_json

    def test_allows_collections(self, custom_mod):
        import collections as real_c
        result = custom_mod._safe_import("collections")
        assert result is real_c

    def test_allows_math(self, custom_mod):
        import math as real_math
        result = custom_mod._safe_import("math")
        assert result is real_math

    def test_blocks_os(self, custom_mod):
        with pytest.raises(ImportError, match="not permitted"):
            custom_mod._safe_import("os")

    def test_blocks_subprocess(self, custom_mod):
        with pytest.raises(ImportError, match="not permitted"):
            custom_mod._safe_import("subprocess")

    def test_blocks_boto3(self, custom_mod):
        with pytest.raises(ImportError, match="not permitted"):
            custom_mod._safe_import("boto3")

    def test_blocks_requests(self, custom_mod):
        with pytest.raises(ImportError, match="not permitted"):
            custom_mod._safe_import("requests")

    def test_blocks_socket(self, custom_mod):
        with pytest.raises(ImportError, match="not permitted"):
            custom_mod._safe_import("socket")

    def test_blocks_sys(self, custom_mod):
        with pytest.raises(ImportError, match="not permitted"):
            custom_mod._safe_import("sys")

    def test_submodule_top_level_in_allowlist(self, custom_mod):
        # collections is in allowlist, so collections.abc should be allowed
        result = custom_mod._safe_import("collections.abc")
        assert result is not None

    def test_submodule_blocked_when_top_level_blocked(self, custom_mod):
        with pytest.raises(ImportError, match="not permitted"):
            custom_mod._safe_import("os.path")


# ---------------------------------------------------------------------------
# execute_converter
# ---------------------------------------------------------------------------

class TestExecuteConverter:
    def test_simple_converter(self, custom_mod):
        code = "def convert(file_content):\n    return {'key': 'value'}\n"
        result = custom_mod.execute_converter(code, "test data")
        assert result == {"key": "value"}

    def test_converter_receives_file_content(self, custom_mod):
        code = "def convert(file_content):\n    return {'received': file_content}\n"
        result = custom_mod.execute_converter(code, "hello")
        assert result["received"] == "hello"

    def test_converter_can_use_csv(self, custom_mod):
        code = (
            "import csv\n"
            "import io\n"
            "def convert(file_content):\n"
            "    reader = csv.DictReader(io.StringIO(file_content))\n"
            "    rows = list(reader)\n"
            "    return {'row_count': len(rows)}\n"
        )
        csv_data = "name,value\nfoo,1\nbar,2\n"
        result = custom_mod.execute_converter(code, csv_data)
        assert result["row_count"] == 2

    def test_missing_convert_function_raises(self, custom_mod):
        code = "x = 1\n"
        with pytest.raises(Exception, match="convert"):
            custom_mod.execute_converter(code, "data")

    def test_open_builtin_removed(self, custom_mod):
        code = (
            "def convert(file_content):\n"
            "    try:\n"
            "        open('/etc/passwd')\n"
            "        return {'open': 'succeeded'}\n"
            "    except (NameError, TypeError):\n"
            "        return {'open': 'blocked'}\n"
        )
        result = custom_mod.execute_converter(code, "")
        assert result["open"] == "blocked"

    def test_eval_builtin_removed(self, custom_mod):
        code = (
            "def convert(file_content):\n"
            "    try:\n"
            "        eval('1+1')\n"
            "        return {'eval': 'succeeded'}\n"
            "    except (NameError, TypeError):\n"
            "        return {'eval': 'blocked'}\n"
        )
        result = custom_mod.execute_converter(code, "")
        assert result["eval"] == "blocked"

    def test_exec_builtin_removed(self, custom_mod):
        code = (
            "def convert(file_content):\n"
            "    try:\n"
            "        exec('x=1')\n"
            "        return {'exec': 'succeeded'}\n"
            "    except (NameError, TypeError):\n"
            "        return {'exec': 'blocked'}\n"
        )
        result = custom_mod.execute_converter(code, "")
        assert result["exec"] == "blocked"

    def test_blocked_import_inside_sandbox(self, custom_mod):
        code = (
            "def convert(file_content):\n"
            "    try:\n"
            "        import subprocess\n"
            "        return {'import': 'succeeded'}\n"
            "    except ImportError:\n"
            "        return {'import': 'blocked'}\n"
        )
        result = custom_mod.execute_converter(code, "")
        assert result["import"] == "blocked"

    def test_env_restored_after_execution(self, custom_mod):
        original_path = os.environ.get("PATH", "")
        code = "def convert(file_content):\n    return {}\n"
        custom_mod.execute_converter(code, "")
        # PATH should be restored after execution
        assert os.environ.get("PATH", "") == original_path

    def test_returns_asm_wrapper(self, custom_mod):
        code = (
            "def convert(file_content):\n"
            "    return {\n"
            "        'success': True,\n"
            "        'asm_output': {'$asm.manifest': 'test'},\n"
            "        'field_mapping': []\n"
            "    }\n"
        )
        result = custom_mod.execute_converter(code, "data")
        assert result["success"] is True
        assert result["asm_output"]["$asm.manifest"] == "test"

    def test_converter_exception_propagates(self, custom_mod):
        code = (
            "def convert(file_content):\n"
            "    raise ValueError('converter error')\n"
        )
        with pytest.raises(ValueError, match="converter error"):
            custom_mod.execute_converter(code, "data")
