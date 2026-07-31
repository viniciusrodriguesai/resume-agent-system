from __future__ import annotations


def enforce_optional_oidc(settings: object) -> None:
    """Ativa st.login somente quando RESUME_REQUIRE_LOGIN=true e o OIDC foi configurado."""
    if not getattr(settings, "require_login", False):
        return
    import streamlit as st

    user = getattr(st, "user", None)
    logged_in = bool(user and getattr(user, "is_logged_in", False))
    if logged_in:
        if st.sidebar.button("Sair"):
            st.logout()
        return
    st.warning("Esta instalação exige autenticação OIDC.")
    if not hasattr(st, "login"):
        st.error("A versão instalada do Streamlit não oferece st.login.")
        st.stop()
    if st.button("Entrar"):
        st.login()
    st.stop()
