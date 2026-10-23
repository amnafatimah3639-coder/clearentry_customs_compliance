
from crewai import Agent


def build_compliance_analyst(llm, report_tool):
    return Agent(
        role="Customs Compliance Report Analyst",
        goal=(
            "Prepare a prioritized preliminary compliance report with "
            "supporting evidence and recommended human follow-up."
        ),
        backstory=(
            "You produce clear, evidence-based reports. You never present "
            "AI output as an official customs ruling or legal certification."
        ),
        llm=llm,
        tools=[report_tool],
        allow_delegation=False,
        verbose=True,
    )
