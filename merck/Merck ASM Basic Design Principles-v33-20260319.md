
# Merck ASM Basic Design Principles
## Composition of Matter

**Exported on 2026-03-19 03:29:49**

---

## Table of Contents

1. [Principles To Build ASM Files](#principles-to-build-asm-files)
2. [Table 1: Placement Logic in the ASM Summary](#table-1-placement-logic-in-the-asm-summary)
3. [Table 2: Best Practices for Calculated Data Linkage](#table-2-best-practices-for-calculated-data-linkage)

---

## Principles To Build ASM Files

These principles have been guided by multiple conversations with Allotrope. The text in purple reflects items we have not heard explicitly from Allotrope; while it may still align with their thinking, we should treat it as Merck specific until additional alignment discussions occur.

### Instrument Hardcoded Terms
The first step in mapping a new instrument is to populate the core attributes in Harmonizing Base Terms (HarmonizingBaseTerms.xlsx). These provide the baseline description of the instrument and define terms that remain constant across any ASM generated for that instrument. Most importantly, they also ensure consistent use of terms across instrument types and instrument families. An expert in the use of the instrument can help define these terms, and mappings from prior documents can be reused to learn and follow our established patterns.

### Data Hierarchical Structure
The hierarchical structure of the ASMs is guided by the core hierarchy schema and the instrument-specific schemas. The hierarchy schema defines the default nested structure of the ASM. An instrument schema can override any information defined in the hierarchy schema; however, elements that are not changed by the instrument schema remain inherited from the hierarchy schema, even if the manifest does not explicitly reference them. The December 2025 release of the hierarchy schema is available at: https://purl.allotrope.org/json-schemas/adm/core/REC/2025/12/hierarchy.schema

### ASM Terms and Values Formatting
ASM terms (the keys in the key-value pairs) are written in the same case as in the official schemas, typically lowercase, with acronyms as a possible exception. Words are separated by spaces, not hyphens or underscores. Calculated field terms should match existing AFO terms or, if none exist, use similar terminology; such terms may be considered for future additions to the ontology. Custom field terms are kept identical to the source, preserving their original case. At any level, values should match the case of the original source data, except for boolean terms, which should always be mapped to a JSON boolean regardless of source case. If a new value is introduced by hardcoding, it should be written in lowercase.

**Special cases:**
- **Manufacturer**: For specific terms that refer to the instrument manufacturer, the most common name is used and written in lowercase (for example, roche), rather than using one of multiple official variants.

### Base Measurement Term Placement
Placement of a term under the base measurement ontology vs. a processed data aggregate document depends on whether the value originates from the raw instrument measurement (base measurement) or is the result of a transformation applied to the raw data (processed data aggregate document), regardless of whether the transformation is user-defined or produced by the instrument. In all cases, terms must match an AFO-valid term used in the reference schema and use Allotrope-valid units. If a term is intended for a processed data aggregate document but is not an AFO term or is not present in the relevant schema, either (a) a request can be made to Allotrope to add the term, or (b) the term can be moved to the calculated data aggregate document, which has fewer restrictions. This should be decided on a case-by-case basis.

### Terms in Multiple Locations
If an ontological term could be placed in multiple locations in the ASM hierarchy, determine whether there is a different intended usage at different levels, as the hierarchy level may provide additional context. For example, device_type = 'solution analyzer' at the device system information level may describe a device capable of multiple instrument roles, whereas device_type in device_control_document at each measurement level may represent the specific role for that reading (for example, the same ASM could use device_type = 'cell counter' at this level). If there is never a difference between values at higher and lower levels of the hierarchy, only the higher-level term is required.

### Custom Fields
Custom fields (any fields created specifically by customers, end users, etc.) should always be transferred on a 1:1 basis (field name, field value, and field unit, if available) to a custom information aggregate document and should not be mapped to core schema fields. Even if the units are known but not present in the output file, they should not be added manually. Custom ASM converters should not be required for each ASM user or customer; this approach enables converters to be readily transferred and reused between customers. 

**Exception**: COTS custom fields. These are custom fields that the software vendor has chosen to deploy and use universally for all software installations and therefore are not unique to an individual end user or customer.

### Calculated Fields
Calculated values that cannot be added to the processed data aggregate document should be added to the calculated data aggregate document and treated similarly to the 1:1 custom information aggregate document transfer, with the exception that units are required and should follow an ontology. If units are not in the Allotrope ontology, a request should be made for them to be added, and the schema can be forked so validation can pass while the request is processed. If units are not available, the term should instead be placed in the custom information aggregate document.

### Best Practices for Linking Calculated Data to Measurements
When adding calculated data to ASMs, calculated values should be traceable back to the measurements used to derive them. The following patterns are recommended:

- **Calculated values from a single measurement**: If the calculated value is derived from only one measurement, the calculated data document should be a child of that measurement, including a linkage to the specific terms involved in the calculation.

- **Calculated values from all measurements**: If the calculated value is derived from all measurements within a measurement aggregate document, the calculated data document should be a child of the measurement aggregate document. This is not likely the most common case, and a processed data aggregate document may be more appropriate for such global calculations.

- **Calculated values from some, but not all, measurements**: If the calculated value is derived from more than one, but not all, measurements, the calculated data document should be a child of the measurement aggregate document, and the specific measurement IDs involved in the calculation should be explicitly indicated.

To capture the linkage, each calculated data document (and each calculated value) can include an optional data source aggregate document. This document lists the identifiers and field names of the data sources used in the calculation and can reference measured, processed, or calculated data. This ensures clear provenance for each calculated value and aligns with how the core schemas are intended to represent data sources.

### Custom and Calculated Fields Identification
Some calculated fields are already part of the instrument schema, but not all. When calculated terms are not defined in the schema, expert knowledge is needed to determine which fields are calculated and which raw data measurements are used in the calculation; scientific instrument user manuals are often employed. Once that is determined, the calculated values placement rules described in bullets above can be used.

### Source File Formats

**Uniform export/report format (typically mono-table format)**: Any automated mapping process should map every term in the source data. If a source term match is not found to the destination schema, it should be captured as a calculated field or a custom field following patterns above. The human in the loop could decide to skip some unwanted mappings in final reviews.

**Complex, non-uniform export/report (mix of different section formats: free-form, one or many different table formats, header/footers, etc.)**: Additional pre-processing is needed to identify which parts of the complex formats are usable and to create an equivalent tabular representation for those elements. Once the data is transformed into a tabular format, the uniform-export rules above can be applied to the transformed source data.

### Statistic Datum Role
When an expert is able to determine it, any field with "quantity" value should have an associated enumerated "statistic datum role" that describes it e.g. "standard deviation role" or "coefficient of variation role".

### Array Ordering
Explicitly include an @index term to force array entries into a specific order. If the items in the list have a single discriminating date that denotes chronology, we should use that field. If it doesn't exist, we should index entries in the same order the data appears in the source data.

---

## Table 1: Placement Logic in the ASM Summary

| Category | Placement Logic | Requirements & Constraints |
|----------|----------------|---------------------------|
| **Raw Measurement** | Under the measurement document aggregate document. | Value must originate from raw instrument measurement. Terms must match AFO-valid terms and use Allotrope-valid units. |
| **Processed Data** | Within the processed data aggregate document. | Used for results of transformations applied to raw data, whether user-defined or instrument-produced. Requires AFO-valid terms and units. |
| **Calculated Data** | Within the calculated data aggregate document. | Used when a term is not in the processed data schema or requires fewer restrictions. Units are required and must follow an ontology. |
| **Custom Fields (User/Customer)** | Always transferred 1:1 to a custom information aggregate document. | Transfer field name, value, and unit (if available) as-is. Do not map to core schema fields or add units manually if missing from the source. |
| **COTS Custom Fields** | May be treated differently than 1:1 user custom fields. | Applies to vendor-specific fields deployed universally across all software installations. |

---

## Table 2: Best Practices for Calculated Data Linkage

To ensure clear provenance and structural conformance, calculated values should be traceable back to their source measurements.

| Calculation Scope | Recommended Hierarchy Placement | Linkage Method |
|-------------------|--------------------------------|----------------|
| **Single Measurement** | Child of the specific measurement document. | Include a linkage to the specific terms involved in the calculation. Can use a data source aggregate document to list identifiers and field names of sources. |
| **All Measurements*** within the measurement aggregate document<br>*not likely a common use case, global calculations may be more appropriate in a processed data aggregate document | Child of the measurement aggregate document. | Can use a data source aggregate document to list identifiers and field names of sources. |
| **Subset of Measurements** | Child of the measurement aggregate document. | Explicitly indicate the specific measurement IDs involved in the calculation. Can use a data source aggregate document to list identifiers and field names of sources. |


I've converted your document to Markdown format.  The document includes all the principles for building ASM files, with proper headings, formatting, and two summary tables at the end. The link to the Allotrope hierarchy schema has been preserved as a clickable link.

**Would you like me to adjust the formatting** or make any other changes to the document?