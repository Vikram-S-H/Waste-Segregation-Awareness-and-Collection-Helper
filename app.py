
from flask import Flask, render_template

app = Flask(__name__)


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Waste Awareness page
@app.route("/awareness")
def awareness():
    return render_template("awareness.html")


@app.route("/classification")
def classification():
    return render_template("classification.html")


if __name__ == "__main__":
    app.run(debug=True)
