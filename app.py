
from flask import Flask, render_template, request, redirect, url_for, session
app = Flask(__name__)
app.secret_key = "waste-helper-secret-key-2026"


ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@123"

from database import create_table, save_request, get_connection, update_request_status
from datetime import date


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

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:

            session["admin_logged_in"] = True

            return redirect(url_for("admin_dashboard"))

        return "Invalid username or password. Please try again.", 401

    return render_template("admin_login.html")



@app.route("/admin-dashboard")
def admin_dashboard():

    # Check whether admin is logged in
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    # Retrieve collection requests from database
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM collection_requests
        ORDER BY created_at DESC
    """)

    requests_list = cursor.fetchall()

    connection.close()

    # Calculate request status counts
    pending_count = sum(
        1 for item in requests_list
        if item["status"] == "Pending"
    )

    approved_count = sum(
        1 for item in requests_list
        if item["status"] == "Approved"
    )

    completed_count = sum(
        1 for item in requests_list
        if item["status"] == "Completed"
    )

    return render_template(
        "admin_dashboard.html",
        requests=requests_list,
        pending_count=pending_count,
        approved_count=approved_count,
        completed_count=completed_count
    )

@app.route("/update-status/<int:request_id>", methods=["POST"])
def update_status(request_id):

    # Check admin login
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    # Get the new status
    status = request.form.get("status", "")

    # Allow only valid statuses
    allowed_statuses = ["Pending", "Approved", "Completed"]

    if status not in allowed_statuses:
        return "Invalid status selected.", 400

    # Update status in database
    update_request_status(request_id, status)

    return redirect(url_for("admin_dashboard"))

@app.route("/admin-logout")
def admin_logout():

    # Clear the admin login session
    session.pop("admin_logged_in", None)

    return redirect(url_for("admin_login"))


if __name__ == "__main__":
    app.run(debug=True)
