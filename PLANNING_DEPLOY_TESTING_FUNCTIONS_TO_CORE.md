# Deployment Plan: Promote Testing CSV Exporter into Core Module

## Objective
Transfer the reusable CSV export functionality from the test suite into the production `core` package so that runtime deployments (Cloud Run) can rely on it without importing from `tests.*`. Ensure all required template assets are packaged with the deployment and that the test suite continues to function without duplicating logic.

## Scope & Deliverables
- New production module `core/csv_exporter.py` with the current functionality from `tests/core/csv_exporter.py`.
- Template assets relocated to `core/templates/` and bundled into deployment artefacts.
- Updated imports across the API and tests to reference `core.csv_exporter`.
- `.dockerignore` adjustments so templates are not excluded from Cloud Run builds.
- Optional compatibility shim in `tests/core/csv_exporter.py` that re-exports the production class (or removal of the duplicate file).

## Detailed Work Items

### 1. Create Production CSV Exporter Module
- Copy implementation from `tests/core/csv_exporter.py` into a new file `core/csv_exporter.py`.
- Sanitize the module for production use:
  - Remove CLI/test harness (`if __name__ == "__main__"` block) and ad-hoc logging configuration.
  - Replace the default `template_path` with a relative path, e.g. `Path(__file__).parent / "templates" / "FS_Input_Template_Fields.csv"`.
  - Review helper methods to ensure no assumptions about test directories remain.
- Update `core/__init__.py` to export `CSVExporter` alongside the existing core classes.

### 2. Relocate Template Assets
- Create `core/templates/` (if not already present).
- Move the canonical template `FS_Input_Template_Fields.csv` from `tests/fixtures/templates/` to `core/templates/`.
- Assess whether the variant templates (`FS_Input_Template_Fields_AFS2024.csv`, etc.) are required at runtime; move any that are used by the API or validation helpers.
- Update the exporter’s code to load from the new directory and ensure any other modules reference the correct paths.

### 3. Adjust Packaging & Ignore Rules
- `.dockerignore` currently excludes `tests/` and all `*.csv` files. Add explicit exceptions so the new templates are bundled:
  - `!core/templates/`
  - `!core/templates/*.csv`
- Confirm no other ignore rules (e.g. `.gitignore`, build scripts) inadvertently remove the templates.

### 4. Update Imports Throughout the Codebase
- Replace `from tests.core.csv_exporter import CSVExporter` with `from core.csv_exporter import CSVExporter` in:
  - `api_app.py`
  - `tests/run_extraction_test.py`
  - `tests/test_api_enhanced.py`
  - `tests/export_financial_data_to_csv.py`
  - `tests/test_parallel_performance.py`
  - Any additional modules/scripts referencing the old path.
- For the test suite, either:
  - Remove `tests/core/csv_exporter.py` and rely on the production module, or
  - Replace its contents with `from core.csv_exporter import CSVExporter` to act as a shim.

### 5. Update Test & Fixture References
- Audit tests or utilities that assume templates live in `tests/fixtures/templates/`; update those paths or provide helper functions to resolve the new location.
- Ensure comparison scripts or validation tools that load expected CSVs are aware of the relocated files (consider copying expected sample outputs if they are still needed under `tests/fixtures`).

### 6. Verification Checklist
- **Static import check**  
  - `python -m compileall core/csv_exporter.py` to confirm the new module imports without runtime dependencies on `tests.*`.
- **Targeted pytest pass** *(run with the appropriate API key/environment variables)*  
  - `pytest tests/test_api_enhanced.py -k export` – validates the `/extract` endpoint still emits base64 template CSVs.  
  - `pytest tests/analyze_field_extraction_accuracy.py` – ensures analytics scripts resolve `core/templates/...` correctly.  
  - `pytest tests/compare_results_vs_expected.py` – verifies comparisons against the relocated templates succeed.  
  - Optionally `pytest tests/test_parallel_performance.py` (or the relevant subset) if you want an end‑to‑end CSV generation check.
- **Manual API smoke test**
  1. Launch the service locally (`uvicorn api_app:app --reload` or equivalent).  
  2. `curl -F "file=@tests/fixtures/light/AFS2024 - statement extracted.pdf" -F export_csv=true http://localhost:8000/extract`.  
  3. Decode the returned `template_csv` payload and confirm the header set matches `core/templates/FS_Input_Template_Fields.csv`.
- **Post-move data spot check**  
  - Open at least one template in `core/templates/` to ensure the CSV content transferred intact (91-row baseline file, plus variants).  
  - Run `python tests/export_financial_data_to_csv.py --file tests/fixtures/light/AFS2024 - statement extracted.pdf` and inspect the generated CSV.
- **Cloud Run / CI validation**
  - Redeploy the container. Confirm the revision starts successfully (no `ModuleNotFoundError` for `tests.core.csv_exporter`).  
  - Review Cloud Run logs for successful health checks and verify an `/extract` invocation in the deployed environment.  
  - Download and inspect a CSV generated in production; headers must still align with `FS_Input_Template_Fields.csv`.

## Risks & Mitigations
- **Missing Templates in Deployment**: Mitigate by double-checking `.dockerignore` changes and performing a local `docker build` or `gcloud builds submit --no-cache` to confirm assets are packaged.
- **Path Resolution Errors**: Use `Path(__file__).resolve()` based paths with `Pathlib` to avoid ambiguity.
- **Test Failures After Path Updates**: Maintain or add shims in the test suite to prevent widespread changes and run the full test suite before merging.
- **Duplication or Drift**: Ensure the test suite imports the production module to avoid diverging implementations.

## Timeline Estimate
- Module migration & template relocation: **~1–2 hours**
- Import updates & test adjustments: **~1 hour**
- Verification (local + Cloud Run redeploy): **~1 hour**
- Contingency for fix-ups: **~30 minutes**

**Total Estimated Effort:** Approximately **3–4 hours**, depending on verification depth and deployment cadence.
