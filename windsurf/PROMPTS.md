# Windsurf Prompts for fredapi

> This file contains ready-to-use prompts for [Windsurf](https://windsurf.com), Cognition's AI-powered IDE. Open this repo in Windsurf, pick a prompt below, and paste it into Cascade. Each prompt includes context on what problem it solves and what Windsurf will do.
>
> Prompts are ordered from simple → complex so you can start easy and build confidence.

---

## Prompt 1 — Understand the Library and Find Your Way Around (Beginner)
**What this solves:** fredapi is the most popular Python client for FRED (Federal Reserve Economic Data) with 19M downloads, but the codebase has minimal documentation. You need to understand how it works to use it effectively or contribute to it.

**What Windsurf will do:** Give you a guided tour of the codebase, explain the class hierarchy, and show you exactly how API calls flow from your Python code to FRED and back.

**Paste this into Cascade:**
```
I'm new to this codebase. Give me a complete walkthrough:

1. What does fredapi do and who uses it? (based on the README and code)
2. Walk me through fredapi/fred.py — what's the Fred class, what are all its public methods, and what does each one return?
3. How does authentication work? Trace what happens when a user creates Fred(api_key="...")
4. Pick the get_series() method and trace it end-to-end: from the Python call → URL construction → HTTP request → XML parsing → pandas Series creation
5. What are the main dependencies (pandas, lxml) and how are they used?
6. Are there any tests? Where are they, and what do they cover?
7. What would I need to know to fix a bug in this library?

Format the output as a developer onboarding guide I could share with my team.
```

---

## Prompt 2 — Fix a Real Bug: XML Parsing Crash (Intermediate)
**What this solves:** Issue #74 — users report "Exception when trying loop over children of lxml.ElementTree." The library crashes on newer versions of lxml because it uses the deprecated `getchildren()` method which was removed. This affects anyone installing fredapi fresh today.

**What Windsurf will do:** Find every instance of the deprecated API, explain why it breaks, fix it with the modern equivalent, and verify the fix doesn't break anything.

**Paste this into Cascade:**
```
There's a reported bug (Issue #74): the library crashes with "AttributeError: 'xml.etree.ElementTree.Element' object has no attribute 'getchildren'" on newer lxml versions.

1. Search the entire codebase for uses of `getchildren()` — this method was deprecated in lxml 4.x and removed in later versions
2. For each occurrence, show me the current code and explain what it's doing
3. Replace each `getchildren()` call with the modern equivalent: `list(element)` for getting child elements, or direct iteration with `for child in element:`
4. Check for any other deprecated lxml/xml.etree APIs while you're at it
5. Write a test that verifies the XML parsing works correctly with a sample FRED API response
6. Make sure the existing tests still pass

Show me a before/after diff for each change.
```

---

## Prompt 3 — Add a New Feature: Batch Series Download (Advanced)
**What this solves:** Issue #42 (most-requested feature) — users want to download multiple FRED series at once and get them as a single DataFrame. Currently you have to call `get_series()` in a loop, which is slow and tedious. Economists routinely work with 10-50 series at a time (GDP, CPI, unemployment, interest rates, etc.).

**What Windsurf will do:** Design and implement a new public method with parallel fetching, proper error handling for partial failures, and a clean DataFrame output.

**Paste this into Cascade:**
```
I want to add a get_multiple_series() method to the Fred class. This is the most-requested feature (#42). Here's what I need:

1. Method signature: `get_multiple_series(series_ids: list, observation_start=None, observation_end=None, num_workers=4) -> pd.DataFrame`
2. It should fetch all series in parallel using concurrent.futures.ThreadPoolExecutor
3. Return a DataFrame where each column is a series (column names = series IDs), index is the date
4. Handle partial failures gracefully: if 3 out of 5 series succeed, return those 3 with a warning about the 2 that failed (don't crash the whole call)
5. Handle series with different frequencies (e.g., monthly CPI + quarterly GDP): align to the most common frequency, or let the user choose
6. Add a docstring with a usage example:
   ```python
   fred = Fred(api_key='your_key')
   df = fred.get_multiple_series(['GDP', 'CPIAUCSL', 'UNRATE', 'FEDFUNDS'])
   df.plot(subplots=True, figsize=(12, 8))
   ```
7. Add unit tests with mocked API responses
8. Update the README with this new feature

This should feel like a natural extension of the existing API — follow the same patterns and conventions used by get_series().
```

---

## Prompt 4 — Modernize the Entire Test Suite (Expert)
**What this solves:** The library has 19M downloads but minimal test coverage. The CI badge is currently **failing**. For a library that economists, data scientists, and financial analysts depend on for accessing Federal Reserve data, this is a reliability risk. You need a comprehensive test suite that runs without a FRED API key.

**What Windsurf will do:** Build a complete mock-based test framework from scratch, covering every public method, edge case, and error path.

**Paste this into Cascade:**
```
This library has 19M PyPI downloads but almost no tests, and the CI is failing. I need a production-quality test suite. Build it from the ground up:

1. Create tests/conftest.py with:
   - A fixture that creates a Fred instance with a fake API key
   - A fixture factory for mock HTTP responses that return realistic FRED XML (look at the actual FRED API response format)
   - Sample response data for: GDP series observations, CPI series info, search results, category listings

2. Create tests/test_fred.py testing every public method:
   - get_series(): normal case, empty series, series with NaN/"." values, date filtering with observation_start/end
   - get_series_info(): metadata parsing, handle missing optional fields
   - get_series_all_releases(): multi-vintage data, pagination
   - search(): keyword matching, limit/offset, empty results
   - search_by_release(), search_by_category(): id-based lookups
   - get_series_categories(), get_series_tags(): relationship queries

3. Create tests/test_errors.py testing failure modes:
   - Invalid API key → clear error message
   - Invalid series ID → "Series not found" error
   - Network timeout → appropriate exception
   - Rate limit (HTTP 429) → appropriate exception
   - Malformed XML response → doesn't crash, raises meaningful error

4. Add pytest config (in pyproject.toml or pytest.ini) with coverage settings
5. All tests must pass with `pytest` using only mocks — no real API calls

Run the tests and show me the coverage report. Target >85% on fredapi/fred.py.
```

---
