"""Mock LLM used by the deployment lab when no real provider key is set."""
import random
import time


MOCK_RESPONSES = {
    "default": [
        "This is a mock AI agent response. In production this would come from an LLM provider.",
        "The agent is running correctly and received your question.",
        "Your cloud-ready AI agent handled the request successfully.",
    ],
    "docker": [
        "Docker packages the app and its dependencies so it can run consistently across environments."
    ],
    "deploy": [
        "Deployment moves code from your machine to a cloud service with a public URL."
    ],
    "health": [
        "The agent is healthy. Liveness and readiness checks are available."
    ],
}


def ask(question: str, delay: float = 0.05) -> str:
    time.sleep(delay + random.uniform(0, 0.02))
    question_lower = question.lower()
    for keyword, responses in MOCK_RESPONSES.items():
        if keyword in question_lower:
            return random.choice(responses)
    return random.choice(MOCK_RESPONSES["default"])
