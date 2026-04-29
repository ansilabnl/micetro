# -*- coding: utf-8 -*-
#
# Copyright: (c) 2020-2026, Men&Mice, Ton Kersten
# GNU General Public License v3.0
# see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt
"""Utils for all Men&Mice modules.

This module implements a robust API helper for the Men&Mice Micetro API.
Changes made:
- Fixed retry logic and moved return outside retry loop
- Only mark changed for mutating HTTP methods
- Use stdlib json and urllib for compatibility
- Allow toggling of certificate validation via mm_provider["mm_validate_certs"]
- More defensive HTTP error handling
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import time
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus

# Import AnsibleError locally inside functions to avoid import-time issues in ansible-test

from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.urls import open_url, SSLValidationError


# The API sometimes has another concept of true and false than Python
# does, so 0 is true and 1 is false.
TRUEFALSE = {
    True: 0,
    False: 1,
}


MUTATING_METHODS = {"POST", "PUT", "DELETE", "PATCH"}


def _build_api_url(mm_url, path):
    """Build a sane API URL from base and relative path without double slashes."""
    return "%s/mmws/api/%s" % (mm_url.rstrip("/"), path.lstrip("/"))


def doapi(url, method, mm_provider, databody):
    """Run an API call.

    Parameters:
        - url          -> Relative URL for the API entry point (may include query parts)
        - method       -> The API method (GET, POST, DELETE,...)
        - mm_provider  -> Dict with keys: mm_url, mm_user, mm_password, optional mm_validate_certs
        - databody     -> Data needed for the API to perform the task (dict or None)

    Returns:
        - A dict with keys like 'message', 'changed', 'warnings' etc.

    Retries on connection errors up to `maxtries` with a small backoff.
    """
    headers = {"Content-Type": "application/json"}
    apiurl = _build_api_url(mm_provider["mm_url"], url)
    result = {"changed": False}

    maxtries = 5
    backoff = 0.25

    # validate_certs default to True unless explicitly set False in mm_provider
    validate_certs = mm_provider.get("mm_validate_certs", True)

    last_exception = None

    for attempt in range(1, maxtries + 1):
        try:
            # Only send data for non-GET methods and when databody is provided
            data = None
            if databody is not None and method.upper() != "GET":
                data = json.dumps(databody, ensure_ascii=False).encode("utf8")

            resp = open_url(
                apiurl,
                method=method,
                force_basic_auth=True,
                url_username=mm_provider.get("mm_user"),
                url_password=mm_provider.get("mm_password"),
                data=data,
                validate_certs=validate_certs,
                headers=headers,
            )

            response = resp.read()
            if isinstance(response, bytes):
                try:
                    response = response.decode("utf8")
                except Exception:
                    # fallback to native representation
                    response = to_native(response)

            # Parse response based on status code
            code = getattr(resp, "code", None)
            if code == 200:
                try:
                    result["message"] = json.loads(response)
                except Exception:
                    result["message"] = response
            elif code == 201:
                try:
                    result["message"] = json.loads(response)
                except Exception:
                    result["message"] = response or ""
            else:
                # Could be 204 No Content or other informational codes
                reason = getattr(resp, "reason", None)
                result["message"] = reason or response or ""

            # Only mark changed for mutating methods
            if method and method.upper() in MUTATING_METHODS:
                result["changed"] = True

            # Normal exit from retry loop
            last_exception = None
            break

        except HTTPError as err:
            # HTTPError may contain a body with JSON error details
            try:
                body = err.read()
                if isinstance(body, bytes):
                    body = body.decode("utf8")
                errbody = json.loads(body)
                err_msg = errbody.get("error", {})
                result["warnings"] = "%s: %s (%s)" % (
                    getattr(err, "msg", "HTTPError"),
                    err_msg.get("message", body),
                    err_msg.get("code", ""),
                )
            except Exception:
                # If we can't parse the body, return the HTTP error message
                result["warnings"] = "%s: %s" % (
                    getattr(err, "msg", "HTTPError"),
                    to_native(err)
                )

            # Do not retry on HTTP errors (they are application-level)
            last_exception = None
            break

        except URLError as err:
            last_exception = err
            # URLError is often fatal for URL resolution; do not retry
            raise RuntimeError("Failed lookup url for %s : %s" % (apiurl, to_native(err)))

        except SSLValidationError as err:
            raise RuntimeError(
                "Error validating the server's certificate for %s: %s"
                % (apiurl, to_native(err))
            )

        except ConnectionError as err:
            last_exception = err
            if attempt == maxtries:
                raise RuntimeError("Error connecting to %s: %s" % (apiurl, to_native(err)))
            # Backoff and retry
            time.sleep(backoff)
            backoff *= 2
            continue

    # If we exhausted retries and still have an exception attached, raise
    if last_exception is not None:
        raise RuntimeError("Failed to contact %s: %s" % (apiurl, to_native(last_exception)))

    # Normalize 'No Content' message
    if result.get("message", "") == "No Content":
        result["message"] = ""

    return result


def getrefs(objtype, mm_provider):
    """Get all objects of a certain type."""
    return doapi(objtype, "GET", mm_provider, None)


def get_single_refs(objname, mm_provider):
    """Get all information about a single object."""
    resp = doapi(objname, "GET", mm_provider, None)
    if resp.get("message"):
        return resp["message"].get("result", resp["message"])

    if resp.get("warnings"):
        resp["invalid"] = True
        return resp

    return {"invalid": True, "warnings": "Unknown error"}


def get_dhcp_scopes(mm_provider, ipaddress):
    """Given an IP Address, find the DHCP scopes."""
    # Ensure ipaddress is safely quoted when inserted into query strings
    url = "Ranges?filter=%s" % quote_plus(ipaddress)

    resp = doapi(url, "GET", mm_provider, None)

    scopes = []
    if resp and resp.get("message"):
        for dhcpranges in resp["message"].get("result", {}).get("ranges", []):
            for scope in dhcpranges.get("dhcpScopes", []):
                scopes.append(scope.get("ref"))

    return scopes
