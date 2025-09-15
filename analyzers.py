import os
from dotenv import load_dotenv
from google import genai
from google.genai.types import Tool, GenerateContentConfig, ThinkingConfig, GoogleSearch, UrlContext, Part
import requests
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

# Initialize Gemini client
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)
model_name = "gemini-2.5-flash"

def analyze_text(text):
    try:
        # define url context and grounding tools
        tools = [
            Tool(url_context=UrlContext()),
            Tool(google_search=GoogleSearch())
        ]

        # call the model
        response = client.models.generate_content(
            model=model_name,
            contents=text,
            config=GenerateContentConfig(
                thinking_config=ThinkingConfig(thinking_budget=0),
                tools=tools
            )
        )

        # get the generated text from all parts
        explanation = ""
        if hasattr(response, "candidates") and response.candidates:
            for part in response.candidates[0].content.parts:
                explanation += part.text + "\n"
            
            # Add URL context if available
            if hasattr(response.candidates[0], 'url_context_metadata'):
                url_context = response.candidates[0].url_context_metadata
                explanation += "\n\n**URL Context:**\n"
                if isinstance(url_context, list):
                    for url in url_context:
                        explanation += f"- {url}\n"
                else:
                    explanation += f"- {str(url_context)}\n"
        else:
            explanation = response.text if hasattr(response, "text") else str(response)

        # check for grounding metadata
        gm = None
        if hasattr(response, "candidates"):
            # may vary depending on SDK version
            gm = response.candidates[0].grounding_metadata if hasattr(response.candidates[0], "grounding_metadata") else None

        # build verdict: e.g. if explanation has “fake” etc
        verdict = "Suspicious" if "fake" in explanation.lower() else "Credible"

        # you can also adjust verdict based on whether grounding metadata is present (no grounding → less confidence)
        if gm is None:
            explanation = explanation + "\n\n(Note: No external sources found.)"
        else:
            # collect source links from grounding_chunks
            chunks = gm.grounding_chunks
            # e.g. build list of URLs and titles
            sources = []
            for c in chunks:
                # c.web.uri, c.web.title etc
                uri = c.web.uri
                title = getattr(c.web, "title", uri)
                sources.append(f"- **{title}** ([🔗]({uri}))\n")
            explanation = explanation + "\n\n**Sources:**\n" + "\n".join(sources)

        return verdict, explanation

    except Exception as e:
        explanation = f"Error: {e}"
        verdict = "Error"
        return verdict, explanation

def analyze_url(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text_content = soup.get_text(separator=" ", strip=True)
        cleaned_text = " ".join(text_content.split()[:1000])

        if not cleaned_text:
            return "Error", "No readable content found on the page."

        return analyze_text(cleaned_text)

    except requests.exceptions.RequestException as e:
        return "Error", f"Failed to fetch URL: {e}"
    except Exception as e:
        return "Error", f"Error processing URL: {e}"
       
def analyze_image(image):
    try:
        # Save the uploaded image to memory (Flask provides a FileStorage object)
        image_bytes = image.read()

        # Call Gemini with both image and instruction
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                Part.from_bytes(data=image_bytes, mime_type=image.content_type),
                Part.from_text(text="Analyze this image and tell me if it looks credible or fake. Explain your reasoning behind the verdict but in brief.")
            ],
            config=GenerateContentConfig(
                thinking_config=ThinkingConfig(thinking_budget=0),
                tools=[Tool(google_search=GoogleSearch())]  # optional: let it ground claims
            )
        )

        explanation = response.text if hasattr(response, "text") else str(response)
        verdict = "Suspicious" if "fake" in explanation.split(".", 1)[0].lower() else "Credible"

    except Exception as e:
        explanation = f"Error: {e}"
        verdict = "Error"

    return verdict, explanation
