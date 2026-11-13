
from flask import Flask, render_template, request
from database import create_table, save_request
from datetime import date

app = Flask(__name__)

# Create the database table when the application starts
create_table()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/awareness")
def awareness():
    return render_template("awareness.html")


@app.route("/classification")
def classification():
    return render_template("classification.html")


@app.route("/schedules")
def schedules():
    return render_template("schedules.html")


@app.route("/request", methods=["GET", "POST"])
def collection_request():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        waste_type = request.form.get("waste_type", "").strip()
        collection_date = request.form.get("date", "").strip()
        instructions = request.form.get("instructions", "").strip()

        # Validate required fields
        if not all([name, phone, address, waste_type, collection_date]):
            return "Please fill in all required fields.", 400

        # Validate contact number
        if not (phone.isdigit() and len(phone) == 10):
            return "Please enter a valid 10-digit contact number.", 400

        # Validate collection day according to waste type
        allowed_days = {
            "Wet Waste": [0, 2, 4],       # Monday, Wednesday, Friday
            "Dry Waste": [1, 5],          # Tuesday, Saturday
            "Hazardous Waste": [3]        # Thursday
        }

        # Validate date format
        try:
            selected_date = date.fromisoformat(collection_date)
        except ValueError:
            return "Invalid collection date.", 400

        # Prevent past dates
        if selected_date < date.today():
            return "Please select a future date.", 400

        # Validate waste type
        if waste_type not in allowed_days:
            return "Invalid waste type selected.", 400

        # Validate collection weekday
        if selected_date.weekday() not in allowed_days[waste_type]:
            return "Selected date does not match the waste collection schedule.", 400

        # Save request in SQLite database
        save_request(
            name,
            phone,
            address,
            waste_type,
            collection_date,
            instructions
        )

        return """
            <h2>Collection Request Submitted Successfully!</h2>
            <p>Your request has been saved in the application.</p>
            <p>This does not guarantee municipal pickup.</p>
            <a href="/">Return to Home</a>
        """

    return render_template("request.html")


if __name__ == "__main__":
    app.run(debug=True)
