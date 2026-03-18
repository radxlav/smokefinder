# CHANGELOG

## [2026-03-02] - Fixes and Improvements

### Fixed
- **Home.py**: Uncommented and simplified the home page code. Removed authentication requirement to allow app to run without secrets configured.
- **All page files**: Added secrets validation check at startup to prevent crashes when `secrets.toml` is missing. Pages now show helpful error message instead of crashing.

### Added
- **utils.py**: New utility module with `check_secrets()` function used by all pages to validate configuration before loading.
- **.streamlit/secrets.toml.template**: Template file showing required secrets format for:
  - DataForSEO API credentials (`email`, `password`)
  - Google Cloud service account (`gcp_service_account`)

### Changed
- **requirements.txt**: Updated package versions for Python 3.13 compatibility:
  - `streamlit>=1.38.0` (was pinned to 1.38.0)
  - `pandas>=2.1.0` (was pinned to 2.0.3 which doesn't work with Python 3.13)
  - `chromadb>=0.4.0` (was pinned to 0.3.29)
  - Removed `pysqlite3-binary` (not needed)
  - Removed duplicate `gsheetsdb`
  - Removed `datetime` (built-in module)

### Files Modified
1. `Home.py` - Uncommented, simplified
2. `requirements.txt` - Updated versions
3. `pages/Google.py` - Added secrets check
4. `pages/Yelp.py` - Added secrets check
5. `pages/Trustpilot.py` - Added secrets check
6. `pages/Tripadvisor.py` - Added secrets check
7. `pages/OnPage.py` - Added secrets check
8. `pages/Summary.py` - Added secrets check
9. `pages/Keywords For Site.py` - Added secrets check
10. `pages/Content Analysis.py` - Added secrets check
11. `pages/Domain Intersection.py` - Added secrets check
12. `pages/Competitors Domain.py` - Added secrets check
13. `pages/Google Trends.py` - Added secrets check

### New Files
1. `utils.py` - Utility functions for secrets validation
2. `.streamlit/secrets.toml.template` - Template for secrets configuration
3. `CHANGELOG.md` - This file
4. `venv/` - Virtual environment directory (not tracked in git)

### How to Configure Secrets
1. Copy `.streamlit/secrets.toml.template` to `.streamlit/secrets.toml`
2. Fill in your DataForSEO API credentials
3. Fill in your Google Cloud service account JSON
4. Restart the app
