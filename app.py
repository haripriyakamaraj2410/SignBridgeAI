"""
app.py
------
SignBridge AI — thin Flask routing layer.
All AI logic lives in ai_service.py, all storage in database.py.
Run with: python app.py
"""
from flask import Flask, render_template, request, jsonify

import ai_service
import database

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html", active="home")


@app.route("/classroom")
def classroom():
    return render_template("classroom.html", active="classroom")


@app.route("/sign-converter")
def sign_converter():
    return render_template("sign_converter.html", active="converter")


@app.route("/simplifier")
def simplifier():
    return render_template("simplifier.html", active="simplifier")


@app.route("/learn")
def learn():
    return render_template("learn.html", active="learn",
                            categories=ai_service.get_categories(),
                            signs_by_category=ai_service.SIGN_CATEGORIES)


@app.route("/quiz")
def quiz():
    return render_template("quiz.html", active="quiz",
                            categories=ai_service.get_categories(),
                            signs_by_category=ai_service.SIGN_CATEGORIES)


@app.route("/communication")
def communication():
    return render_template("communication.html", active="communication")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", active="dashboard")


@app.route("/about")
def about():
    return render_template("about.html", active="about")


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
@app.route("/api/convert-signs", methods=["POST"])
def api_convert_signs():
    data = request.get_json(force=True) or {}
    text = (data.get("text") or "").strip()
    use_concepts = bool(data.get("use_concepts", False))
    if not text:
        return jsonify({"error": "empty text"}), 400
    sequence = ai_service.text_to_sign_sequence(text, use_concepts=use_concepts)
    return jsonify({"sequence": sequence})


@app.route("/api/simplify", methods=["POST"])
def api_simplify():
    data = request.get_json(force=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "empty text"}), 400
    result = ai_service.simplify_text(text)
    return jsonify(result)


@app.route("/api/quiz-result", methods=["POST"])
def api_quiz_result():
    data = request.get_json(force=True) or {}
    student = (data.get("student") or "Guest").strip() or "Guest"
    category = data.get("category", "general")
    quiz_type = data.get("quiz_type", "multiple_choice")
    sign_word = data.get("sign_word", "")
    is_correct = bool(data.get("is_correct", False))
    if not sign_word:
        return jsonify({"error": "sign_word required"}), 400
    database.record_quiz_result(student, category, quiz_type, sign_word, is_correct)
    return jsonify({"status": "ok"})


@app.route("/api/progress", methods=["GET"])
def api_progress():
    student = request.args.get("student", "Guest").strip() or "Guest"
    progress = database.get_progress(student)
    if not progress["recommended_practice"]:
        # nothing weak yet -- recommend a few signs the student hasn't tried
        untried = [w for w in ai_service.get_all_sign_words() if w not in progress["signs_learned"]]
        progress["recommended_practice"] = untried[:5]
    return jsonify(progress)


@app.route("/api/message", methods=["POST"])
def api_message():
    data = request.get_json(force=True) or {}
    sender = data.get("sender", "student")
    phrase = (data.get("phrase") or "").strip()
    if not phrase:
        return jsonify({"error": "empty phrase"}), 400
    database.add_message(sender, phrase)
    return jsonify({"status": "ok"})


@app.route("/api/messages", methods=["GET"])
def api_messages():
    return jsonify(database.get_recent_messages())


if __name__ == "__main__":
    database.init_db()
    app.run(debug=True, port=5000)
