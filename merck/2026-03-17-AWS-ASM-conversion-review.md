
# AWS - Merck ASM Generation for Solution Analyzer

**Date:** 2026-03-17

**Author:** Cardona, Cesar

---

## Input Files

- SampleResults2025-November
- SampleResultsT26B200180C2025-July

---

## Summary of Mismatch Categories

We can qualify the mismatches in these categories:

**[META] Missing metadata information**  
Instrument folders with source data are mounted to our file server, which is scanned by the converter application. This mount path for each instrument folder includes critical metadata about geography and server identifiers.  
Example: `/mnt/America/New_York/Nova_Biomedical_BioProfile_Flex2/MERCK_SERVER1/ExportDEV/Results/`

**[USAGE] Merck improper usage of the data**  
The AI-mapped fields are semantically correct, but our scientists are not using them properly. Merck should align on using the more accurate semantic mapping rather than the common usage.

**[ERROR] Misclassification or Overfitting**  
A true semantic mismatch. In many cases the mapping has a reasonable rationale, but it is still not correct.

**[CONFIG] Hardcoded configuration data**  
Some terms in the data and device documents can be interpreted in multiple ways. We have built hardcoded configuration fields that should be applied per instrument.  
Reference: Merck ASM HarmonizingBaseTerms

**[RULE] Data does not follow Allotrope ASM building good practices**  
We have a document capturing two levels of good practices, Allotrope and Merck.  
Reference: ASM Basic Building Principles document (attached).

---

## Comments/Questions

We have provided documents to teach the AI about the [CONFIG] and [RULE] patterns.

**Questions:**

1. What would be your advice on how the AI converter platform could capture instrument-specific metadata, such as the examples we described under [META]?

2. Is there a way for the AI agent to provide a confidence level for each mapping, to determine inference uncertainty or potentially overfitting risk? This would help the human-in-the-loop review.

3. We perform four levels of validation (below). Which ones are you using today? In the validation-only tool, we would like errors and warnings labeled by the corresponding validation level.

---

## Merck Levels of Validation

### Level 1. ASM Schema validation (JSON and ASM python validation)

Merck has built a Python package to validate compliance with JSON standards and ASM tags ($asm, i.e., `"$asm.type": "http://www.w3.org/2001/XMLSchema#dateTime"`, `"$asm.pattern": "value datum"`). JSON compliance is relatively straightforward today using public tools (for example, `jq`). However, ASM schema validation requires additional logic to interpret the ASM rules and verify compliance against the specific manifest version in use. This package was built for ADE SDC squad, our team ADE Data Quality Assurance are users.

### Level 2. Data quality assessment (ASM vs. raw data) (TOSCA testing)

Field by field source to target comparison. This is not a generic package or script that can be reused to compare ASM values with instrument source data each time, as source data formats vary widely. While we have a general workflow, significant instrument-specific coding is required.

The workflow can be summarized in a few steps:

- Load source files and ASM files into a TOSCA SQLite database (the most time-consuming step)
- Build SQL queries to expose each value (AFO term) from the ASM and the source file, most times at different level of hierarchy
- Apply SQL transformations to align output formats/units (we usually receive this documentation as part of the parser release)
- Define tolerances for acceptable differences, using rounding in SQLs or the TOSCA comparison tolerance parameters
- Run a TOSCA report, comparing each term (source vs. ASM), and report differences

### Level 3 and Level 4. Merck ASM basic guiding principles

ASM Basic Building Principles document (attached).

This document describes, beyond the formal requirements, good practices and patterns that should be reproducible in any instrument converter implementation. We are currently reviewing this document with Allotrope to ensure that these principles are not Merck-specific and could be broadly adopted. For now, we labeled with different colors what we estimate being Allotrope principles (Level 3) and Merck-specific (Level 4).

---

## Manual Verification of Mapping Details

### Data mapped to the base ontology

Overall, the mapping looks correct, including the analyte document, with a few exceptions:

**Measurement time:**  
**[META]** The measurement time did not include geographical context. The July file was from Europe, but the date-time format was interpreted as U.S. mm/dd/yyyy. That context was not provided to you, so this behavior is understandable. In our current approach, we use the mount path to infer this information.

**Sample type:**  
**[ERROR]** The value used for sample type is not a valid ASM term.

### Processed data

Of the seven processed data terms, four are mapped correctly and three were skipped:

**[ERROR]** Skipped terms: "total cell count", "viable cell count", and "cell density dilution factor".

**[ERROR]** In addition, "cell density dilution factor" should be nested one level deeper under a data processing document, as it belongs to the instrument configuration settings.

### Calculated fields

**[ERROR] [RULE]** Calculated fields were not mapped and were ignored. They need to include traceability of calculations. These fields below are examples of calculated fields:

- pH @ Temp
- PO2 @ Temp

### Custom fields

**[ERROR] [RULE]** Custom fields were not mapped and were ignored.

---

## Hardcoded Data

### Data System Document (and related themes)

**[CONFIG]** A Data System Document section is missing. This document should include hardcoded terms that you are currently grouping under "hardcoded terms"/"file config".

### Terminology for hardcoded terms

**[NO-ISSUE/DONE]** For instrument general parameters, we would prefer not to use the term "file manifest" or "manifest," as those terms have a specific meaning in the Allotrope context. Could we instead use something like "Hardcoded terms," "File configuration," or similar terminology?

### Traceability to the original file

**[META]** In the Data System Document, it is important that the JSON provides a way to trace back to the original source file. We currently derive this from the mount path on the file server, which is not available to you. For instance, we use the following fields:

- **UNC path:** full path on the local server hosting the file, e.g. `\\MERCKSERVER\ExportDEV\Results\TestExample.csv`
- **filename:** e.g. "TestExample.csv"
- **ASM file identifier:** e.g. TestExample.csv-1.json (Constructed as $filename-$row_num and used as the output file name)

### Output filename

**[NO-ISSUE]** Our output name definition above seems to be more informative as sample names could be quite diverse and sometimes not too logical, but that is not an error as long as filename is always unique.

### Device document

**[ERROR] [CONFIG]** A Device Document with device type = "solution analyzer" is missing. This could also be populated from the same "Hardcoded terms" input too.


I've converted the document to markdown format. The document is now structured with clear headings, proper formatting for code examples and file paths, and organized sections that make it easier to read and navigate. 

**Would you like me to adjust the formatting** in any specific way, or would you like me to create a different version with alternative styling?