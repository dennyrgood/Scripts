# DMS — Scripts, Config, and External Dependencies

This document lists the direct and indirect scripts invoked by the `dms` entrypoint (via `run_dms_script` or the menu), the configuration/data files referenced, external executables and services used, and additional notes.

## Direct calls made by `dms`
(Scripts invoked via `run_dms_script` or the menu)

- `dms_menu.py`
- `dms_util/dms_scan.py`
- `dms_util/dms_image_to_text.py`
- `dms_util/dms_summarize.py`
- `dms_util/dms_review.py`
- `dms_util/dms_apply.py`
- `dms_util/dms_cleanup.py`
- `dms_util/dms_render.py`
- `dms_util/dms_init.py`
- `dms_util/dms_status.py`
- `dms_util/dms_delete_entry.py`

## Indirect calls (invoked by the above scripts)

- `dms_util/dms_render.py`  
  (also invoked by `dms_apply.py`, `dms_init.py`, and `dms_cleanup.py`)
- `tools_pdf_to_md_textonly.py`  
  (invoked by `dms_util/dms_image_to_text.py`)

## Configuration / data files used
(Referenced by `dms` scripts; not executable)

- `dms_config.json`
- `.dms_state.json` (e.g., `Doc/.dms_state.json`)
- `.dms_scan.json` (e.g., `Doc/.dms_scan.json`)
- `.dms_pending_summaries.json` (e.g., `Doc/.dms_pending_summaries.json`)
- `.dms_pending_approved.json` (e.g., `Doc/.dms_pending_approved.json`)

## External executables / services invoked

- `tesseract` — CLI OCR (used by `dms_util/dms_image_to_text.py`)
- `python3` / `sys.executable` — used to run external Python tools (e.g., `tools_pdf_to_md_textonly.py`)
- Ollama HTTP API (ollama service) — used by `dms_util/dms_summarize.py`
- `git` — checked/used by `dms` and `dms_menu.py`
- `which` — used in `dms_menu.py` checks

## Notes

- Some repository utilities exist but are not invoked by the `dms` wrapper in normal operation. Examples:
  - `dms_util/dms_bootstrap.py`
  - `dms_util/dms_migrate_to_json.py`
  - `dms_util/dms_apply_test.py`
- These utilities were intentionally excluded from the lists above because they are not called (directly or indirectly) by the `dms` entrypoint. If you want them included, they can be added to this document.

```