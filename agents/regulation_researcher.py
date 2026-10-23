
from crewai import Agent


def build_regulation_researcher(llm, regulation_tool):
    return Agent(
        role="Customs Regulation Research Specialist",
        goal=(
            "Retrieve relevant regulatory passages from the supplied "
            "library and identify potential compliance concerns."
        ),
        backstory=(
            "You are a cautious researcher. Never invent legal citations "
            "or claim that supplied documents represent all current laws."
        ),
        llm=llm,
        tools=[regulation_tool],
        allow_delegation=False,
        verbose=True,
    )
