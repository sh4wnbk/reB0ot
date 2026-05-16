# Bob Task — Better API Error Handling

**Date:** May 16, 2026  
**Task:** Add comprehensive error handling for API calls in reboot.py

## Objective
Wrap the `requests.post` call in `generate_restoration_string()` with a try/except block that catches `requests.exceptions.HTTPError` and provides clear, actionable error messages for common API failures.

## Changes Made

### File: `reboot.py`

**Location:** Lines 198-215 (in `generate_restoration_string()` function)

**Before:**
```python
resp = requests.post(
    f"{WATSONX_URL}/ml/v1/text/generation?version=2023-05-29",
    json=payload,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
)
resp.raise_for_status()
```

**After:**
```python
try:
    resp = requests.post(
        f"{WATSONX_URL}/ml/v1/text/generation?version=2023-05-29",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    resp.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 403:
        raise SystemExit("Error: API access denied (403). Check your WATSONX_API_KEY and PROJECT_ID.")
    elif e.response.status_code == 429:
        raise SystemExit("Error: Rate limit hit (429). Wait a moment and try again.")
    else:
        raise SystemExit(f"Error: API call failed ({e.response.status_code}): {e}")
```

## Benefits

1. **403 Forbidden:** Clear message indicating credential issues with specific environment variables to check
2. **429 Rate Limit:** Helpful message suggesting the user wait before retrying
3. **Other HTTP Errors:** Generic fallback with status code and error details
4. **Clean Exit:** Uses `SystemExit` to exit gracefully with informative messages instead of raw stack traces

## Testing Recommendations

- Test with invalid API key (should trigger 403)
- Test with excessive requests (should trigger 429)
- Test with other error conditions (network issues, invalid project ID, etc.)

## Status
✅ **Complete** — Error handling implemented and ready for testing