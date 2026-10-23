
from crewai import Agent


def build_document_extractor(llm, document_reader_tool):
    return Agent(
        role="Customs Document Extraction Specialist",
        goal=(
            "Extract accurate shipment details from invoices and packing "
            "lists without guessing missing values."
        ),
        backstory=(
            "You are a careful trade-document analyst. Preserve the "
            "original quantities, units, currencies, dates and descriptions."
        ),
        llm=llm,
        tools=[document_reader_tool],
        allow_delegation=False,
        verbose=True,
    )
