# Crane Test

Local Streamlit smoke-test UI for the TRT60 Parser PoC. It does not write to
the database, upload to Supabase Storage, or grant lifting approval.

```powershell
python -m pip install -r backend/requirements-crane-test.txt
$env:PYTHONPATH='backend'
streamlit run backend/scripts/crane_test.py
```

Use the Golden-validated TRT60 reference PDF. The page shows parser metadata,
Golden/Critical result, parsed Configuration, an exact chart-cell selector, and
the Main Boom preliminary capacity result. Rigging can be entered either as a
total weight or as 1-4 sling legs with a per-leg weight; the latter is totalled
before the capacity calculation. Geometry intentionally remains
`NOT_IMPLEMENTED`: the TRT60 range graph is visual source evidence, not yet a
Golden-validated numerical geometry dataset.
