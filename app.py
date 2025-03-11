import os
from flask import Flask, render_template, request
import google.generativeai as genai
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()
API_KEY = os.getenv('GEMINI_API_KEY')

# Debug: Check if API key is loading
print(f"API Key: {API_KEY}")

# Configure Google Gemini API
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        skills = request.form.get("skills")
        interests = request.form.get("interests")
        department = request.form.get("department")

        # Generate recommendations using Gemini API
        recommendations = get_course_recommendations(skills, interests, department)
        return render_template("results.html", recommendations=recommendations)
    
    return render_template("index.html")

def get_course_recommendations(skills, interests, department):
    prompt = f"""
    Suggest 5 to 7 online courses for a student in {department} with skills in {skills} and interests in {interests}.
    Format the result in this EXACT format:

    1. [Course Name](https://example.com)  
    2. [Course Name](https://example.com)  
    3. [Course Name](https://example.com)  

    Make sure to include valid, real course links from Coursera, Udemy, edX, and Swayam.
    Do not provide search suggestions — provide direct links only.
    """

    try:
        response = model.generate_content(prompt)
        print("RAW RESPONSE:", response.text)

        courses = []
        pattern = r"\[([^\]]+)\]\((https?://[^\)]+)\)"
        matches = re.findall(pattern, response.text)

        for match in matches:
            course = {"name": match[0], "link": match[1]}
            courses.append(course)

        # 🔥 Fallback: If no URLs found, generate platform search links
        if not courses:
            print("No direct links found — using fallback search...")
            fallback_courses = extract_course_names(response.text)
            courses = generate_fallback_links(fallback_courses)

        return courses[:7]  # Return top 5-7 courses
    except Exception as e:
        print(f"Error: {e}")
        return [{"name": "Failed to fetch courses", "link": "#"}]

# Fallback 1: Extract Course Names Using Regex
def extract_course_names(text):
    pattern = r"^\d+\.\s+(.+)$"
    matches = re.findall(pattern, text, re.MULTILINE)
    return matches

# Fallback 2: Generate Search Links
def generate_fallback_links(course_names):
    platforms = {
        "Coursera": "https://www.coursera.org/search?query=",
        "Udemy": "https://www.udemy.com/courses/search/?q=",
        "edX": "https://www.edx.org/search?q=",
        "Swayam": "https://swayam.gov.in/search?query="
    }

    courses = []
    for course in course_names:
        # Pick a random platform link
        for platform, url in platforms.items():
            search_link = f"{url}{course.replace(' ', '+')}"
            courses.append({"name": f"{course} ({platform})", "link": search_link})
            break

    return courses

if __name__ == "__main__":
    app.run(debug=True)
