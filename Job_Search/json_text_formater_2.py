import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Import function
from text_extraction_1 import get_structured_resume

# Load .env
load_dotenv()

# =====================================
# GET STRUCTURED RESUME
# =====================================

structured_json = get_structured_resume()

# Convert to JSON string
resume_json = json.dumps(structured_json, indent=2)

# =====================================
# INITIALIZE LLM
# =====================================

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3
)

# =====================================
# PROMPT
# =====================================

prompt = f"""
You are an expert ATS Resume Optimizer.

You will receive resume data in JSON format.

Tasks:
1. Improve wording
2. Improve ATS optimization
3. Improve formatting
4. Keep facts unchanged
5. Make bullet points recruiter-friendly
6. Do not add fake experience

Resume JSON:
{resume_json}

Return:
A professional ATS-friendly resume in markdown format.
"""

# =====================================
# GENERATE RESPONSE
# =====================================

try:

    print("Sending resume to Groq...\n")

    response = llm.invoke(prompt)

    optimized_resume = response.content

    print("========== OPTIMIZED RESUME ==========\n")

    print(optimized_resume)

    # Save output
    with open("optimized_resume.md", "w", encoding="utf-8") as file:
        file.write(optimized_resume)

    print("\nOptimized resume saved successfully.")

except Exception as e:

    print(f"Error: {str(e)}")