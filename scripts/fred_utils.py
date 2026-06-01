"""Shared FRED API helpers used by the data fetchers.

This module centralizes the FRED observations boilerplate that was previously
duplicated across the individual fetch scripts: URL construction, the
`User-Agent` header, dropping the `"."` missing-value sentinel, and float
conversion. It is an *internal* utility module — importing it does not introduce
any external runtime dependency, build step, or framework.
"""

import json
import os
import sys
import time
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

FRED_OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
USER_AGENT = "joemirza-site/1.0"

# Retry FRED on rate-limiting (429) and transient server errors with exponential
# backoff. FRED rate-limits bursts (the yield-curve fetch alone pulls 11 series),
# so a single 429 should not abort the whole run.
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
DEFAULT_MAX_RETRIES = 4
DEFAULT_BACKOFF = 2.0  # seconds; doubled each attempt: 2, 4, 8, 16


def get_api_key():
    """Return the FRED API key from the environment (empty string if unset)."""
    return os.environ.get("FRED_API_KEY", "")


def fetch_series(series_id, limit=None, *, api_key=None, sort_order="desc",
                 extra_params=None, required=True, timeout=30,
                 max_retries=DEFAULT_MAX_RETRIES, backoff=DEFAULT_BACKOFF):
    """Fetch observations for a FRED series.

    Returns a list of ``{"date": str, "value": float}`` dicts, with the ``"."``
    missing-value sentinel dropped, sorted oldest-first.

    Rate-limiting / transient errors: a 429 or 5xx response (or a transient
    network error) is retried up to ``max_retries`` times with exponential
    backoff, honoring a ``Retry-After`` header when present. On success the
    output is identical to a single successful call — retrying only changes the
    failure-under-load path.

    Key / failure handling (after retries are exhausted):
    - If the API key is missing or the request still fails and ``required`` is
      True (the default), print an error to stderr and ``sys.exit(1)`` — the
      behavior expected of FRED-primary fetchers.
    - If ``required`` is False, print a warning and return ``[]`` so callers for
      which FRED is a secondary/optional source (e.g. the S&P 500 P/E price
      extension) can degrade gracefully without exiting.

    ``sort_order`` is sent to FRED unless set to None (omitted). ``extra_params``
    is merged into the query string for callers needing frequency/aggregation
    options.
    """
    key = api_key if api_key is not None else get_api_key()
    if not key:
        if required:
            print("ERROR: FRED_API_KEY environment variable not set", file=sys.stderr)
            sys.exit(1)
        print(f"WARNING: FRED_API_KEY not set — skipping FRED fetch for {series_id}.",
              file=sys.stderr)
        return []

    params = {
        "series_id": series_id,
        "api_key": key,
        "file_type": "json",
    }
    if sort_order is not None:
        params["sort_order"] = sort_order
    if limit is not None:
        params["limit"] = limit
    if extra_params:
        params.update(extra_params)

    url = FRED_OBSERVATIONS_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items())
    req = Request(url, headers={"User-Agent": USER_AGENT})

    raw = _fetch_with_retry(req, series_id, timeout, required, max_retries, backoff)
    if raw is None:  # only reached when required=False and retries exhausted
        return []

    observations = []
    for obs in raw.get("observations", []):
        if obs["value"] != ".":
            observations.append({"date": obs["date"], "value": float(obs["value"])})

    observations.sort(key=lambda x: x["date"])
    return observations


def _fetch_with_retry(req, series_id, timeout, required, max_retries, backoff):
    """Perform the HTTP GET with bounded exponential-backoff retry.

    Returns the parsed JSON dict on success. On exhausted retries: ``sys.exit(1)``
    if ``required`` else ``None``.
    """
    attempt = 0
    while True:
        try:
            with urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except HTTPError as e:
            retryable = e.code in RETRYABLE_STATUS
            reason = f"HTTP {e.code}"
            retry_after = e.headers.get("Retry-After") if e.headers else None
        except URLError as e:
            retryable = True  # transient network error
            reason = str(e.reason)
            retry_after = None

        if retryable and attempt < max_retries:
            try:
                wait = float(retry_after) if retry_after else backoff * (2 ** attempt)
            except (TypeError, ValueError):
                wait = backoff * (2 ** attempt)
            print(f"  FRED {series_id}: {reason}, retrying in {wait:.0f}s "
                  f"(attempt {attempt + 1}/{max_retries})", file=sys.stderr)
            time.sleep(wait)
            attempt += 1
            continue

        # Non-retryable, or out of retries.
        if required:
            print(f"ERROR: Failed to fetch {series_id} from FRED: {reason}", file=sys.stderr)
            sys.exit(1)
        print(f"WARNING: FRED fetch failed for {series_id}: {reason}", file=sys.stderr)
        return None
