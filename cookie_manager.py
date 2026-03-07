"""
]cookie helper for Streamlit.

Usage:
    from cookie_manager import get_cookie, set_cookie, delete_cookie, load_cookies

    # Call once at the top of your app — reads all cookies into session_state
    load_cookies()

    # Then read / write / delete as needed
    uid = get_cookie("nero_user_id")
    set_cookie("nero_user_id", "abc123", days=30)
    delete_cookie("nero_user_id")
"""

import streamlit as st
import streamlit.components.v1 as components
import urllib.parse


# ── Internal helpers ───────────────────────────────────────────────────────────

def _parse_cookie_string(raw: str) -> dict:
    result = {}
    for part in raw.split(";"):
        part = part.strip()
        if "=" in part:
            k, _, v = part.partition("=")
            try:
                result[k.strip()] = urllib.parse.unquote(v.strip())
            except Exception:
                result[k.strip()] = v.strip()
    return result


# ── Public API ─────────────────────────────────────────────────────────────────

def load_cookies():
    """
    Render a hidden component that reads document.cookie and stores it in
    st.query_params['_nero_cookies'] so Python can parse it.

    Call this ONCE near the top of main.py, before any cookie reads.
    On the very first load the query param won't exist yet — the component
    writes it and triggers a rerun, after which it's available.
    """
    raw = st.query_params.get("_nero_cookies", None)

    if raw is None:
        components.html("""
            <script>
            const raw  = encodeURIComponent(document.cookie);
            const url  = new URL(window.parent.location.href);
            url.searchParams.set('_nero_cookies', raw);
            window.parent.history.replaceState({}, '', url.toString());

            // Poke Streamlit into a rerun by simulating an input event
            // on the hidden query-param watcher it uses internally
            window.parent.postMessage({type: 'streamlit:forceRerun'}, '*');
            </script>
        """, height=0)
        st.stop()

    # Decode and cache in session_state so we don't re-parse every call
    if "_nero_cookie_dict" not in st.session_state:
        st.session_state["_nero_cookie_dict"] = _parse_cookie_string(
            urllib.parse.unquote(raw)
        )


def get_cookie(name: str, default: str = "") -> str:
    """Return the value of cookie `name`, or `default` if not set."""
    return st.session_state.get("_nero_cookie_dict", {}).get(name, default)


def set_cookie(name: str, value: str, days: int = 30):
    """
    Write a persistent cookie. Renders a hidden JS snippet.
    The new value is also written into the in-memory cache immediately
    so subsequent get_cookie() calls in the same run see it.
    """
    safe_val = urllib.parse.quote(str(value), safe="")
    components.html(f"""
        <script>
        (function() {{
            var d = new Date();
            d.setTime(d.getTime() + {days} * 86400000);
            document.cookie = "{name}=" + "{safe_val}"
                + ";expires=" + d.toUTCString()
                + ";path=/;SameSite=Strict";
        }})();
        </script>
    """, height=0)

    # Update in-memory cache
    if "_nero_cookie_dict" not in st.session_state:
        st.session_state["_nero_cookie_dict"] = {}
    st.session_state["_nero_cookie_dict"][name] = str(value)

    # Keep query param in sync so the value survives a rerun within same session
    current = st.session_state["_nero_cookie_dict"]
    raw_pairs = ";".join(f"{k}={urllib.parse.quote(v, safe='')}" for k, v in current.items())
    st.query_params["_nero_cookies"] = urllib.parse.quote(raw_pairs, safe="")


def delete_cookie(name: str):
    """Expire a cookie immediately."""
    components.html(f"""
        <script>
        document.cookie = "{name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;SameSite=Strict";
        </script>
    """, height=0)

    # Remove from in-memory cache
    if "_nero_cookie_dict" in st.session_state:
        st.session_state["_nero_cookie_dict"].pop(name, None)