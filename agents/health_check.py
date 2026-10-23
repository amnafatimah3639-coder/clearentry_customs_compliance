
import importlib
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

failures = []
api_key = os.getenv("GROQ_API_KEY", "").strip()
model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()


def check(name, fn):
    print(f"\nCHECK: {name}")
    try:
        message = fn()
        print(f"PASS: {message or 'OK'}")
        return True
    except Exception as exc:
        failures.append((name, f"{type(exc).__name__}: {exc}"))
        print(f"FAIL: {type(exc).__name__}: {exc}")
        return False


def check_files():
    required = [
        "app.py",
        "crew.py",
        "requirements.txt",
        "agents/__init__.py",
        "agents/document_extractor.py",
        "agents/cross_validator.py",
        "agents/regulation_researcher.py",
        "agents/compliance_analyst.py",
        "tools/__init__.py",
        "tools/document_tools.py",
        "health_check.py",
    ]
    missing = [f for f in required if not (ROOT / f).is_file()]

    if missing:
        raise FileNotFoundError("Missing files: " + ", ".join(missing))

    return f"Found all {len(required)} required files."


def check_dependencies():
    packages = [
        "streamlit",
        "crewai",
        "litellm",
        "groq",
        "pypdf",
        "docx",
        "pydantic",
        "requests",
    ]

    for package in packages:
        importlib.import_module(package)

    return "All required package imports succeeded."


def check_project_imports():
    import crew
    from agents.document_extractor import build_document_extractor
    from agents.cross_validator import build_cross_validator
    from agents.regulation_researcher import build_regulation_researcher
    from agents.compliance_analyst import build_compliance_analyst

    return "Crew and all four agent modules imported successfully."


def check_tools():
    from tools.document_tools import (
        DocumentReaderTool,
        CrossDocumentCompareTool,
        RegulationSearchTool,
        ReportStructureTool,
    )

    DocumentReaderTool()
    CrossDocumentCompareTool()
    ReportStructureTool()

    rag = RegulationSearchTool(
        source_names=["sample_rules.txt"],
        source_texts=[
            "Commercial invoices should include a declared value and quantity."
        ],
    )

    result = rag._run(query="invoice declared value quantity")

    if "sample_rules.txt" not in result:
        raise AssertionError("RAG did not return the source filename.")

    return "All four custom tools initialize and RAG returns a source."


def check_document_reader():
    from tools.document_tools import read_document

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        encoding="utf-8",
        delete=False,
    ) as handle:
        handle.write("Invoice reference: TEST-001\nQuantity: 10 units")
        filename = handle.name

    try:
        text = read_document(filename)

        if "TEST-001" not in text:
            raise AssertionError("Extracted text did not match the sample.")

        return "Sample TXT document was read successfully."
    finally:
        Path(filename).unlink(missing_ok=True)


def check_groq():
    from groq import Groq

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Add it to Streamlit Secrets "
            "or the environment before testing live access."
        )

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: CLEARENTRY_OK",
            }
        ],
        max_completion_tokens=60,
    )

    answer = response.choices[0].message.content or ""

    if not answer.strip():
        raise RuntimeError("Groq returned an empty response.")

    return f"Groq returned a response using configured model {model}."


def main():
    print("=" * 58)
    print("ClearEntry Health Check")
    print("=" * 58)

    check("Project files", check_files)
    check("Dependencies", check_dependencies)
    check("Agent and crew imports", check_project_imports)
    check("Custom tools and RAG", check_tools)
    check("Document extraction", check_document_reader)
    check("Live Groq API", check_groq)

    print("\n" + "=" * 58)
    if failures:
        print(f"RESULT: FAILED ({len(failures)} check(s))")
        for name, error in failures:
            print(f"- {name}: {error}")
        sys.exit(1)

    print("RESULT: ALL CHECKS PASSED")
    print("Note: This does not test a complete four-agent review.")
    sys.exit(0)


if __name__ == "__main__":
    main()
