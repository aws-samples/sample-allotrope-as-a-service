Yes, absolutely! ATaaS uses Bedrock Claude 3.5 Sonnet for:

File Analysis - analyze_file_with_claude() - AI identifies format, instrument type, vendor

ASM Conversion - convert_to_asm_with_claude() - AI converts data to ASM format

Converter Code Generation - generate_converter_with_claude() - AI generates Python converter code

The issue is: ATaaS times out on complex files (Nova FLEX2, EndoScan-V, Wyatt ASTRA) due to the API Gateway 30-second hard limit.