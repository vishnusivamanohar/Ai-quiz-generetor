from flask import Flask, render_template, request
import json
import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Initialize GenAI Client using GEMINI_KEY environment variable
api_key = os.getenv("GEMINI_KEY")
client = genai.Client(api_key=api_key)

# Pydantic schema to enforce exact JSON output format from Gemini
class QuizData(BaseModel):
    questions: list[list[str]] = Field(
        description="A list of questions. Each question is a list of exactly 4 strings: [question_text, option_1, option_2, option_3]"
    )
    answers: list[str] = Field(
        description="A list of correct answers. Each element must be a string '1', '2', or '3', representing the correct option index (1-based)."
    )

def question_generator(user_input, difficulty, num_questions):
    prompt = f"""
    You are an expert Quiz Generator. Generate a technical quiz on: {user_input}
    Difficulty level: {difficulty} (strictly tailor the questions to this difficulty level: easy questions should be basic, medium should be intermediate, and hard should be challenging/complex).

    STRICT RULES:
    1. Generate EXACTLY {num_questions} unique questions.
    2. Each question MUST have EXACTLY 3 options (e.g. 4 strings total in each list item: [question, option1, option2, option3]).
    3. Answers MUST be a list of strings: "1", "2", or "3" only.
    4. NEVER use "4", "0", "A", "B", or "C" in the answers list.
    5. Fact-check math and code: 2**3=8, 5/2=2.5.
    """
        
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=QuizData,
        )
    )
    
    # The output is guaranteed to follow the QuizData schema
    text = response.text.strip()
    data = json.loads(text)
    print("Generated quiz data:", data)
    return data["questions"], data["answers"]

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/generate_quiz", methods=["POST"])
def generate_quiz():
    topic = request.form.get("topic", "").strip()
    difficulty = request.form.get("difficulty", "medium")
    num_questions = request.form.get("num_questions", "10")
    timer_option = request.form.get("timer_option", "none")

    if not topic:
        return render_template("index.html", error="No topic provided! Please enter a topic.")
    
    try:
        num_questions = int(num_questions)
        if not (1 <= num_questions <= 20):
            num_questions = 10
    except ValueError:
        num_questions = 10

    try:
        questions, answers = question_generator(topic, difficulty, num_questions)
    except Exception as e:
        print(f"Error generating quiz: {e}")
        # Render index with error message instead of crashing
        return render_template("index.html", error=f"Failed to generate quiz: {str(e)}")

    return render_template("quiz.html", 
                           questions=questions, 
                           answers=answers, 
                           topic=topic, 
                           difficulty=difficulty, 
                           timer_option=timer_option)

if __name__ == "__main__":
    app.run(debug=True)
