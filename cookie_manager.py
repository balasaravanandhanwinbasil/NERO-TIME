"""
cookie_manager.py
Persistent login for Streamlit using st.query_params as the cookie jar.

HOW IT WORKS:
- On login:  set_cookie() writes values into st.query_params so they appear
             in the URL (e.g. ?nero_user_id=...&nero_token=...).
             The URL persists across tab closes IF the browser restores the
             last-visited URL (which all major browsers do by default).
- On load:   load_cookies() simply reads st.query_params — no JS, no st.stop(),
             no black screen.
- On logout: delete_cookie() removes the keys from st.query_params, cleaning
             the URL.

SECURITY NOTE:
  The token value is a 48-byte random secret validated against Firebase.
  Exposing it in the URL is acceptable for a personal productivity app, but
  if you need higher security, consider a proper backend session endpoint.
"""

import streamlit as st


def load_cookies():
    """
    Read persisted values from st.query_params into st.session_state cache.
    Call once near the top of main.py — safe on every rerun, never blocks.
    """
    if "_nero_cookie_dict" not in st.session_state:
        st.session_state["_nero_cookie_dict"] = {}

    params = st.query_params
    # Copy any nero_ prefixed params into our in-memory dict
    for key in list(params.keys()):
        if key.startswith("nero_"):
            st.session_state["_nero_cookie_dict"][key] = params[key]


def get_cookie(name: str, default: str = "") -> str:
    """Return the value of a persisted cookie, or `default` if not set."""
    return st.session_state.get("_nero_cookie_dict", {}).get(name, default)


def set_cookie(name: str, value: str, days: int = 30):
    """
    Persist a value by writing it into both st.query_params and the
    in-memory cache. The query_params write keeps it in the URL so it
    survives a tab close / browser restart.
    """
    if "_nero_cookie_dict" not in st.session_state:
        st.session_state["_nero_cookie_dict"] = {}

    st.session_state["_nero_cookie_dict"][name] = str(value)
    st.query_params[name] = str(value)


def delete_cookie(name: str):
    """Remove a persisted value from both the URL and the in-memory cache."""
    if "_nero_cookie_dict" in st.session_state:
        st.session_state["_nero_cookie_dict"].pop(name, None)

    try:
        # st.query_params raises KeyError if key doesn't exist
        params = dict(st.query_params)
        if name in params:
            del params[name]
            st.query_params.clear()
            for k, v in params.items():
                st.query_params[k] = v
    except Exception:
        pass