from flask import Flask, render_template,request
import json
from google import genai

app = Flask(__name__)
client = genai.Client(api_key="your gemini api key")


def question_generator(user_input):
    prompt = f"""
    You are an expert Quiz Generator. Generate a technical quiz on: {user_input}

    STRICT RULES:
    1. Generate EXACTLY 10 unique questions.
    2. Each question MUST have EXACTLY 3 options.
    3. Answers MUST be a list of strings: "1", "2", or "3" only.
    4. NEVER use "4", "0", "A", "B", or "C" in the answers list.
    5. Fact-check math and code: 2**3=8, 5/2=2.5.
    6. Return ONLY raw JSON. No markdown backticks.

    FORMAT:
    {{
      "questions": [
        ["What is the output of 2**3?", "6", "8", "9"],
        ["Which keyword defines a function?", "def", "func", "define"]
      ],
      "answers": ["2", "1"]
    }}
    """
       
    response = client.models.generate_content(
        model="models/gemini-2.5-flash", 
        contents=prompt
    )
    text = response.text.strip().replace("```json", "").replace("```", "")
    data = json.loads(text)
    return data["questions"], data["answers"]



@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("index.html")

@app.route("/generate_quiz", methods=["GET", "POST"])
def generate_quiz():
    # Adding a default empty string '' if "topic" isn't found
    topic = request.form.get("topic", "") 
    if not topic:
        return "No topic provided! Please go back and enter a topic."
    questions, answers = question_generator(topic)
    return render_template("quiz.html", questions=questions, answers=answers)

if __name__ == "__main__":
    app.run(debug=True)
