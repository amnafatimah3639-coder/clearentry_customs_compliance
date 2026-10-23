
import os
import tempfile
from pathlib import Path

import requests
import streamlit as st

from crew import run_compliance_crew
from tools.document_tools import read_document


st.set_page_config(
    page_title="ClearEntry | Customs AI",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

    .stApp { background: #f4f7fb; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .block-container { max-width: 1300px; padding-top: 1.5rem; }
    .hero {
        background: linear-gradient(120deg, #111c3a, #174b69, #197e83);
        color: white; padding: 32px; border-radius: 22px;
        margin-bottom: 22px;
    }
    .hero h1 {
        font-family: 'Manrope', sans-serif; font-size: 2.4rem;
        font-weight: 800; margin: 4px 0 8px 0;
    }
    .hero p { color: #d9f1f4; margin-bottom: 0; }
    .eyebrow {
        color: #9de6df; font-size: .75rem;
        letter-spacing: 2px; font-weight: 700;
    }
    .panel {
        background: white; border: 1px solid #e2e8f0;
        border-radius: 17px; padding: 20px; margin-bottom: 14px;
    }
    .panel h3 { color: #14213d; margin-top: 0; }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #176b78, #258b91);
        color: white; border: 0; border-radius: 12px;
        min-height: 3rem; font-weight: 700;
    }
    [data-testid="stFileUploader"] {
        background: white; border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">AI-ASSISTED TRADE OPERATIONS</div>
        <h1>ClearEntry</h1>
        <p>Customs documentation review, evidence-based checks, and
        regulation-grounded findings in one workspace.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## Review settings")

    jurisdiction = st.text_input(
        "Customs jurisdiction",
        placeholder="e.g. Pakistan",
    )

    shipment_type = st.selectbox(
        "Shipment type",
        ["Import", "Export", "Transit", "Other"],
    )

    st.divider()
    st.markdown("### Your AI team")

    st.markdown(
        """
        **01 · Document Extractor**
        
        Extracts shipment fields.
        
        **02 · Cross-Document Auditor**
        
        Checks potential inconsistencies.
        
        **03 · Regulation Researcher**
        
        Retrieves relevant supplied rules.
        
        **04 · Compliance Analyst**
        
        Prepares the final report.
        """
    )

    st.caption(
        "AI findings are preliminary. Human verification is required."
    )

left, right = st.columns([1.05, 0.95], gap="large")

with left:
    st.markdown(
        """
        <div class="panel">
        <h3>01 · Shipment documents</h3>
        Upload the commercial invoice and packing list.
        Supported formats: PDF, DOCX, TXT.
        </div>
        """,
        unsafe_allow_html=True,
    )

    invoice = st.file_uploader(
        "Commercial invoice",
        type=["pdf", "docx", "txt"],
        key="invoice",
    )

    packing = st.file_uploader(
        "Packing list",
        type=["pdf", "docx", "txt"],
        key="packing",
    )

    st.markdown(
        """
        <div class="panel">
        <h3>02 · Regulation library</h3>
        Supply relevant official regulations, guidance, or tariff notes.
        </div>
        """,
        unsafe_allow_html=True,
    )

    regulation_files = st.file_uploader(
        "Regulations and guidance",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="regulations",
    )

with right:
    st.markdown(
        """
        <div class="panel">
        <h3>03 · What gets reviewed?</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        - Product descriptions and quantities
        - Currency, declared values and dates
        - Package counts and weights
        - HS-code references when present
        - Missing or ambiguous information
        - Potential issues supported by supplied regulations
        """
    )

    st.warning(
        "This prototype does not connect to a live customs database. "
        "Scanned PDFs need OCR before text can be extracted."
    )

    n8n_url = st.text_input(
        "Optional n8n production webhook",
        placeholder="https://your-n8n-host/webhook/...",
    )

    send_to_n8n = st.checkbox("Send report to n8n when finished")


def get_secret(name, default=""):
    """Read Streamlit Cloud secrets, then environment variables."""
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = os.getenv(name, default)

    return str(value or default).strip()


def save_upload(uploaded_file):
    suffix = Path(uploaded_file.name).suffix.lower()

    with tempfile.NamedTemporaryFile(
        suffix=suffix,
        delete=False,
    ) as handle:
        handle.write(uploaded_file.getvalue())
        return handle.name


st.divider()

if st.button(
    "Run compliance review",
    type="primary",
    use_container_width=True,
):
    if not invoice or not packing:
        st.error("Upload both the invoice and packing list.")
        st.stop()

    if not jurisdiction.strip():
        st.error("Enter the customs jurisdiction.")
        st.stop()

    if not regulation_files:
        st.error("Upload at least one regulation or guidance document.")
        st.stop()

    if send_to_n8n and not n8n_url:
        st.error("Enter the n8n webhook URL or disable the n8n option.")
        st.stop()

    api_key = get_secret("GROQ_API_KEY")
    model = get_secret("GROQ_MODEL", "openai/gpt-oss-120b")

    if not api_key:
        st.error(
            "GROQ_API_KEY is missing. Add it in Streamlit Cloud "
            "Settings → Secrets."
        )
        st.stop()

    os.environ["GROQ_API_KEY"] = api_key
    os.environ["GROQ_MODEL"] = model

    temporary_paths = []

    try:
        with st.spinner("Reading and validating uploaded files..."):
            invoice_path = save_upload(invoice)
            packing_path = save_upload(packing)
            temporary_paths.extend([invoice_path, packing_path])

            invoice_text = read_document(invoice_path)
            packing_text = read_document(packing_path)

            if not invoice_text.strip() or not packing_text.strip():
                raise ValueError(
                    "A shipment document has no selectable text. "
                    "Scanned PDFs require OCR."
                )

            regulation_texts = []

            for uploaded in regulation_files:
                text = uploaded.getvalue()

                suffix = Path(uploaded.name).suffix.lower()

                if suffix == ".txt":
                    extracted = text.decode("utf-8", errors="replace")
                else:
                    temp_path = save_upload(uploaded)
                    temporary_paths.append(temp_path)
                    extracted = read_document(temp_path)

                if extracted.strip():
                    regulation_texts.append(
                        {"name": uploaded.name, "text": extracted}
                    )

            if not regulation_texts:
                raise ValueError(
                    "No readable text was found in the regulation files."
                )

        st.markdown("## Live agent activity")
        active_agent = st.empty()
        progress_bar = st.progress(0)
        activity_message = st.empty()

        agent_names = [
            "Document Extractor",
            "Cross-Document Auditor",
            "Regulation Researcher",
            "Compliance Analyst",
        ]
        current_index = {"value": -1}

        def update_agent(name):
            if name in agent_names:
                current_index["value"] = agent_names.index(name)
                progress_bar.progress(
                    (current_index["value"] + 1) / len(agent_names)
                )

            active_agent.info(f"⚙️ Working now: **{name}**")
            activity_message.caption(
                "CrewAI is processing the current task. "
                "The label updates when agent steps are reported."
            )

        result = run_compliance_crew(
            invoice_path=invoice_path,
            packing_path=packing_path,
            jurisdiction=jurisdiction.strip(),
            shipment_type=shipment_type,
            regulation_texts=regulation_texts,
            status_callback=update_agent,
        )

        report = result["report"]
        st.session_state["last_report"] = report
        st.session_state["last_result"] = result

        progress_bar.progress(1.0)
        active_agent.success("Review workflow completed.")

        if send_to_n8n:
            response = requests.post(
                n8n_url,
                json={
                    "event": "customs_review_completed",
                    "jurisdiction": jurisdiction.strip(),
                    "shipment_type": shipment_type,
                    "invoice_filename": invoice.name,
                    "packing_list_filename": packing.name,
                    "regulation_filenames": [
                        file.name for file in regulation_files
                    ],
                    "report": report,
                },
                timeout=20,
            )
            response.raise_for_status()
            st.success("Report sent to n8n.")

    except Exception as exc:
        st.error("The review failed. Check the error details below.")
        st.exception(exc)

    finally:
        for path in temporary_paths:
            try:
                os.unlink(path)
            except OSError:
                pass


if "last_report" in st.session_state:
    st.divider()
    st.markdown("## Compliance review report")

    st.caption(
        "Preliminary AI review only. Verify findings against original "
        "documents and current, authoritative regulations."
    )

    st.markdown(st.session_state["last_report"])

    st.download_button(
        "Download report as Markdown",
        data=st.session_state["last_report"],
        file_name="customs_compliance_report.md",
        mime="text/markdown",
    )

    with st.expander("View individual agent outputs"):
        outputs = st.session_state["last_result"]

        for key in (
            "extraction",
            "cross_document_audit",
            "regulation_research",
        ):
            st.markdown(f"### {key.replace('_', ' ').title()}")
            st.write(outputs[key])
