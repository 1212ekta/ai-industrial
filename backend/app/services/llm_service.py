import json
from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def extract_entities(text: str) -> dict:
    prompt = """
    Extract industrial entities from the following text.
    Return JSON format with these keys: "Equipment", "Failure", "Vendor", "Engineer", "Maintenance", "Inspection".
    Only include entities found in the text.
    Text: {text}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Using 3.5 turbo as fallback for 5.5 in MVP, depending on actual availability
            messages=[
                {"role": "system", "content": "You are an expert industrial knowledge extractor. Always output valid JSON."},
                {"role": "user", "content": prompt.format(text=text)}
            ],
            response_format={ "type": "json_object" }
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error extracting entities: {e}")
        return {}

def generate_rca(equipment: str, problem: str, graph_context: str, vector_context: str):
    prompt = f"""
    You are an AI Root Cause Analysis expert.
    Equipment: {equipment}
    Problem: {problem}
    
    Graph Context:
    {graph_context}
    
    Vector Context (Similar Documents):
    {vector_context}
    
    Generate a JSON response with the following structure:
    {{
        "likely_causes": [
            {{"cause": "Cause 1", "probability": 0.85}},
            {{"cause": "Cause 2", "probability": 0.15}}
        ],
        "recommendations": ["Rec 1", "Rec 2"]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a Root Cause Analysis expert. Always output valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error generating RCA: {e}")
        return {"likely_causes": [], "recommendations": []}
