"""Streamlit UI with source checkboxes and chat interface."""

import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000"


def fetch_sources():
    """Fetch available sources from the backend."""
    try:
        resp = requests.get(f"{API_BASE_URL}/api/sources", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return []


def query_backend(question: str, sources: list[str]):
    """Send a query to the backend RAG pipeline."""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/query",
            json={"question": question, "sources": sources if sources else None},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        return {"answer": f"Error communicating with backend: {e}", "citations": []}


def scrape_source(source_name: str):
    """Trigger scraping for a source."""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/admin/scrape",
            json={"source": source_name},
            timeout=300,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def get_store_stats():
    """Get vector store statistics."""
    try:
        resp = requests.get(f"{API_BASE_URL}/api/admin/store/stats", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None


def get_llm_status():
    """Get LLM connectivity status."""
    try:
        resp = requests.get(f"{API_BASE_URL}/api/admin/llm/status", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None


# --- Page Config ---
st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="📊",
    layout="wide",
)

st.title("AI Research Assistant")
st.caption("RAG-powered financial document Q&A")

# --- Initialize session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_sources" not in st.session_state:
    st.session_state.selected_sources = []

# --- Sidebar ---
with st.sidebar:
    st.header("Data Sources")

    sources = fetch_sources()

    if sources:
        # Select All / Deselect All
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Select All"):
                st.session_state.selected_sources = [s["name"] for s in sources]
                st.rerun()
        with col2:
            if st.button("Deselect All"):
                st.session_state.selected_sources = []
                st.rerun()

        # Source checkboxes
        selected = []
        for source in sources:
            checked = source["name"] in st.session_state.selected_sources
            if st.checkbox(
                source["display_name"],
                value=checked,
                key=f"src_{source['name']}",
            ):
                selected.append(source["name"])
        st.session_state.selected_sources = selected

        st.divider()

        # Scrape controls
        st.subheader("Refresh Sources")
        for source in sources:
            if st.button(f"Scrape {source['display_name']}", key=f"scrape_{source['name']}"):
                with st.spinner(f"Scraping {source['display_name']}..."):
                    result = scrape_source(source["name"])
                    if "error" in result:
                        st.error(f"Error: {result['error']}")
                    else:
                        st.success(
                            f"Found {result['documents_found']} docs, "
                            f"ingested {result['documents_ingested']}"
                        )
                        if result.get("errors"):
                            for err in result["errors"]:
                                st.warning(err)
    else:
        st.warning("No sources available. Is the backend running?")

    st.divider()

    # Settings expander
    with st.expander("Settings & Stats"):
        stats = get_store_stats()
        if stats:
            st.metric("Total Chunks", stats["total_chunks"])
            st.metric("Total Documents", stats["total_documents"])
            if stats.get("sources"):
                st.write("**Indexed Sources:**")
                for s in stats["sources"]:
                    st.write(f"- {s}")
        else:
            st.info("Could not fetch store stats.")

        st.divider()

        llm = get_llm_status()
        if llm:
            status_icon = "Connected" if llm["reachable"] else "Disconnected"
            st.write(f"**LLM Status:** {status_icon}")
            st.write(f"**Provider:** {llm['provider']}")
            st.write(f"**Model:** {llm['model']}")
            if llm.get("error"):
                st.error(llm["error"])
        else:
            st.info("Could not fetch LLM status.")

# --- Chat Interface ---
# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("citations"):
            with st.expander("View Citations"):
                for citation in message["citations"]:
                    st.markdown(f"**{citation['source_name']}**")
                    if citation.get("source_url"):
                        st.markdown(f"[Link]({citation['source_url']})")
                    if citation.get("date"):
                        st.markdown(f"*Date: {citation['date']}*")
                    st.markdown(f"> {citation['text_snippet']}")
                    st.divider()

# Chat input
if prompt := st.chat_input("Ask a question about your financial documents..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = query_backend(prompt, st.session_state.selected_sources)

        st.markdown(result["answer"])

        citations = result.get("citations", [])
        if citations:
            with st.expander("View Citations"):
                for citation in citations:
                    st.markdown(f"**{citation['source_name']}**")
                    if citation.get("source_url"):
                        st.markdown(f"[Link]({citation['source_url']})")
                    if citation.get("date"):
                        st.markdown(f"*Date: {citation['date']}*")
                    st.markdown(f"> {citation['text_snippet']}")
                    st.divider()

    # Save assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "citations": citations,
    })
