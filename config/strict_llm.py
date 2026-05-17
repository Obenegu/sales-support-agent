from config.settings import client
from google.genai import types


def call_llm_strict(prompt: str) -> dict:
    """Call the LLM with strict constraints to avoid hallucinations."""

    config = types.GenerateContentConfig(
            # tools=[tools],
            temperature=0.2,  # No randomness
            max_output_tokens=2024,
            response_mime_type="application/json" # forces clean JSON output
        )

    contents = types.Content(role="user", parts=[
        types.Part(text=prompt)
    ])


    response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[contents],
                    config=config
                )
    
    # return response.candidates[0].content.parts[0].text

    if not response or not getattr(response, "candidates", None):
        return "I don’t have information about that."

    candidate = response.candidates[0]
    if not candidate or not getattr(candidate, "content", None):
        return "I don’t have information about that."

    parts = getattr(candidate.content, "parts", None)
    if not parts or len(parts) == 0 or not getattr(parts[0], "text", None):
        return "I don’t have information about that."

    return parts[0].text
