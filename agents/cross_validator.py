
from crewai import Agent


def build_cross_validator(llm, compare_tool):
    return Agent(
        role="Cross-Document Audit Specialist",
        goal=(
            "Identify potential mismatches between the invoice and packing "
            "list, supported by evidence from both documents."
        ),
        backstory=(
            "You compare shipment records carefully. You distinguish "
            "confirmed differences from missing or ambiguous information."
        ),
        llm=llm,
        tools=[compare_tool],
        allow_delegation=False,
        verbose=True,
    )
