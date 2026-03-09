Data Source Traceability Section (Lines 217-230)

"calculated data aggregate document": {
  "calculated data document": [
    {
      "calculated data name": "temperature corrected pH",
      "calculated result": {"value": 7.189, "unit": "pH"}
    },
    {
      "calculated data name": "temperature corrected pO2",
      "calculated result": {"value": 91.7, "unit": "mmHg"}
    },
    {
      "calculated data name": "temperature corrected pCO2",
      "calculated result": {"value": 30.7, "unit": "mmHg"}
    },
    {
      "calculated data name": "bicarbonate",
      "calculated result": {"value": 11.8, "unit": "mmol/L"}
    }
  ],
  "data source aggregate document": {
    "data source document": [
      {
        "data source identifier": "3320f832-070e-40c1-be60-78d9a8d4eaaf",
        "data source feature": "pH measurement"
      },
      {
        "data source identifier": "6450950e-0542-45f4-96c1-5e722fd815a5",
        "data source feature": "gas measurement"
      }
    ]
  }
}

Key Points to Explain to Customer
1. What is it?
The data source aggregate document links calculated values back to their source measurements.

2. Why is it required?

FDA 21 CFR Part 11: Electronic records must have complete audit trail

EMA Annex 11: Data integrity requires traceability

Regulatory Compliance: Must prove which raw measurements were used in calculations

3. How does it work?

Calculated value: "temperature corrected pH" = 7.189

Source measurement: UUID 3320f832-070e-40c1-be60-78d9a8d4eaaf (the pH measurement from line 68)

This creates an auditable link: "This calculated value came from THIS specific measurement"

4. What's missing in customer's file?
Their file has the calculated data document but is missing the data source aggregate document, so there's no way to trace calculated values back to source measurements.

5. File size difference:

Customer: 4,681 bytes (no traceability)

AWS: 5,484 bytes (+803 bytes for traceability)

The extra 803 bytes provide regulatory compliance

This is the compliance issue AWS found and fixed automatically!