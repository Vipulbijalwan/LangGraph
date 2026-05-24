import os
import re
import json
from pypdf import PdfReader


# ==========================================
# EXTRACT TEXT FROM PDF
# ==========================================

def extract_resume_text(pdf_path):

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")

    try:
        reader = PdfReader(pdf_path)

        extracted_text = []

        for page in reader.pages:

            try:
                text = page.extract_text(extraction_mode="layout")

            except TypeError:
                # Fallback for older pypdf versions
                text = page.extract_text()

            if text:
                extracted_text.append(text)

        return "\n".join(extracted_text)

    except Exception as e:
        raise Exception(f"PDF Reading Error: {str(e)}")


# ==========================================
# PARSE RESUME
# ==========================================

def parse_extracted_resume(raw_text):

    resume_data = {
        "contact_information": {
            "name": "",
            "location": "",
            "phone": "",
            "email": "",
            "links": []
        },
        "professional_summary": "",
        "technical_skills": {},
        "projects": [],
        "education": [],
        "achievements": []
    }

    if not raw_text:
        return resume_data

    # Clean lines
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

    if not lines:
        return resume_data

    # ======================================
    # CONTACT INFORMATION
    # ======================================

    resume_data["contact_information"]["name"] = lines[0]

    # Email
    email_match = re.search(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        raw_text
    )

    if email_match:
        resume_data["contact_information"]["email"] = email_match.group()

    # Phone
    phone_match = re.search(
        r"(?:\+91[\-\s]?)?[6-9]\d{9}",
        raw_text
    )

    if phone_match:
        resume_data["contact_information"]["phone"] = phone_match.group()

    # Links
    links = re.findall(
        r"(https?://[^\s]+|www\.[^\s]+|linkedin\.com/[^\s]+|github\.com/[^\s]+|leetcode\.com/[^\s]+)",
        raw_text
    )

    resume_data["contact_information"]["links"] = list(set(links))

    # Location
    for line in lines[:5]:

        if "Dehradun" in line:
            resume_data["contact_information"]["location"] = "Dehradun"

    # ======================================
    # SECTION PARSING
    # ======================================

    current_section = None
    project_buffer = None

    for line in lines:

        lower_line = line.lower()

        # Section Detection
        if "professional summary" in lower_line:
            current_section = "summary"
            continue

        elif "technical skills" in lower_line:
            current_section = "skills"
            continue

        elif "projects" in lower_line:
            current_section = "projects"
            continue

        elif "education" in lower_line:
            current_section = "education"
            continue

        elif "achievements" in lower_line:
            current_section = "achievements"
            continue

        # ======================================
        # SUMMARY
        # ======================================

        if current_section == "summary":

            resume_data["professional_summary"] += line + " "

        # ======================================
        # SKILLS
        # ======================================

        elif current_section == "skills":

            if ":" in line:

                category, skills = line.split(":", 1)

                resume_data["technical_skills"][category.strip()] = [
                    skill.strip()
                    for skill in skills.split(",")
                    if skill.strip()
                ]

        # ======================================
        # PROJECTS
        # ======================================

        elif current_section == "projects":

            # New Project
            if "|" in line and not line.startswith("•"):

                if project_buffer:
                    resume_data["projects"].append(project_buffer)

                parts = line.split("|")

                title = parts[0].strip()

                tech_stack = []

                if len(parts) > 1:

                    tech_stack = [
                        tech.strip()
                        for tech in parts[1].split(",")
                        if tech.strip() and tech.upper() != "LINK"
                    ]

                project_buffer = {
                    "title": title,
                    "tech_stack": tech_stack,
                    "description": []
                }

            # Bullet Points
            elif line.startswith("•") and project_buffer:

                bullet = line.replace("•", "").strip()

                bullet = re.sub(r"\s+-\s+", "-", bullet)

                project_buffer["description"].append(bullet)

        # ======================================
        # EDUCATION
        # ======================================

        elif current_section == "education":

            if (
                "b.tech" in lower_line
                or "bachelor" in lower_line
                or "diploma" in lower_line
            ):

                resume_data["education"].append({
                    "degree": line,
                    "institution_details": ""
                })

            elif resume_data["education"]:

                previous_text = (
                    resume_data["education"][-1]["institution_details"]
                )

                resume_data["education"][-1]["institution_details"] = (
                    previous_text + " " + line
                ).strip()

        # ======================================
        # ACHIEVEMENTS
        # ======================================

        elif current_section == "achievements":

            if line.startswith("•"):

                achievement = line.replace("•", "").strip()

                resume_data["achievements"].append(achievement)

    # Add Final Project
    if project_buffer:
        resume_data["projects"].append(project_buffer)

    # Cleanup
    resume_data["professional_summary"] = (
        resume_data["professional_summary"].strip()
    )

    return resume_data


# ==========================================
# MAIN FUNCTION
# ==========================================

def get_structured_resume():

    resume_pdf = (
        r"C:\Users\user\Desktop\LangGraph\campux\Job_Search\Vipul Resume.pdf"
    )

    raw_text = extract_resume_text(resume_pdf)

    structured_json = parse_extracted_resume(raw_text)

    return structured_json


# ==========================================
# MAIN EXECUTION
# ==========================================

if __name__ == "__main__":

    structured_json = get_structured_resume()

    clean_json = json.dumps(structured_json, indent=4)

    print("========== EXTRACTED RESUME JSON ==========\n")

    print(clean_json)

    with open("resume_output.json", "w", encoding="utf-8") as file:
        file.write(clean_json)

    print("\nJSON saved as resume_output.json")