I have been assuming that the converters only convert to ASM format, the actual values are not converted. Is this not the case? Or are there some instances that the standard calls for changing the source values to standard values in which case the source and tartet wouldn't match?


Context
That's the right assumption for most fields — the converter reformats the structure (CSV → ASM JSON), not the values. A pH of 7.183 in the CSV should be 7.183 in the ASM.

But there are a few cases where the Allotrope standard or the customer's own design principles call for value changes:

1. Unit normalization
The Allotrope schema specifies valid units. If an instrument outputs temperature as 36.5 °C but the schema expects degC, the value stays the same but the unit label changes. Our field_mapping already handles this — we compare the numeric value, not the unit string.

2. Timestamp formatting
Source: 11/1/2025 4:46:26 AM → ASM: 2025-11-01T04:46:26.000+00:00. The value is the same moment in time, just reformatted. We don't include timestamps in field_mapping for this reason — they're structural.

3. Chemistry Dilution Ratio
This is one we actually do transform today. Source: 1:2 (string) → ASM: 0.5 (float). The ratio is converted to a decimal. This is the one case in our Nova FLEX2 converter where source_value ≠ asm_value. And looking at the customer's own ASM output, they do the same thing — their file has 0.5 for a 1:2 ratio.

4. Manufacturer/model naming
Source CSV has no manufacturer field. The converter hardcodes "nova biomedical" in lowercase per Merck's design principles. This isn't a value conversion — it's metadata injection from the instrument config.

5. Potential future case: Merck's processed data
Their design principles mention "transformations applied to raw data" going into processed data aggregate document. If an instrument outputs a raw signal and the converter computes a concentration from it, that would be a true value transformation. But for Nova FLEX2, the instrument itself does the computation — the CSV already contains the final values.

So to directly answer your question: your assumption is correct for the vast majority of fields. The converter changes the format, not the values. The only real exception in our current converter is the dilution ratio (1:2 → 0.5), and even that is debatable since it's a representation change, not a data change.

The exact-match comparison in our Data Integrity Verification is the right approach. If a future instrument requires actual value conversions, we can handle it then — but I wouldn't add complexity for a case that doesn't exist yet.


