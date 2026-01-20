from openai import OpenAI
import json

def match_company_with_profile(company_info, user_profile_text, api_key):
    """
    Uses OpenAI GPT to match a company with a user profile.
    """
    if not api_key:
        return {"match_score": 0, "reasoning": "API Key missing"}

    client = OpenAI(api_key=api_key)

    prompt = f"""
    You are a career matching assistant. 
    Compare the following User Profile with the Company Information.
    
    User Profile:
    {user_profile_text}
    
    Company Information:
    {company_info}
    
    Provide a JSON response with:
    1. "match_score": A number between 0 and 100 representing the fit.
    2. "reasoning": A concise explanation (max 2 sentences) of why this is a good or bad match.
    
    Return ONLY JSON.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        return {"match_score": 0, "reasoning": f"Error: {str(e)}"}
