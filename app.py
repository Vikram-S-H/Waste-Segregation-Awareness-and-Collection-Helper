
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
from config import SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD

app.secret_key = SECRET_KEY
from database import (
    create_table,
    create_users_table,
    register_user,
    get_user_by_username,
    get_user_by_id,
    save_request,
    get_connection,
    update_request_status
)
from datetime import date


# Create the database table when the application starts
create_table()

create_users_table()


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

    # Check whether the user is logged in
    if not session.get("user_id"):
        return redirect(url_for("user_login"))

    # Retrieve registered user details
    user = get_user_by_id(session["user_id"])

    if not user:
        session.pop("user_id", None)
        session.pop("user_name", None)
        return redirect(url_for("user_login"))

    if request.method == "POST":

        waste_type = request.form.get("waste_type", "").strip()
        collection_date = request.form.get("date", "").strip()
        instructions = request.form.get("instructions", "").strip()

        # Validate required fields
        if not waste_type or not collection_date:
            return "Please fill in all required fields.", 400

        # Validate collection days
        allowed_days = {
            "Wet Waste": [0, 2, 4],
            "Dry Waste": [1, 5],
            "Hazardous Waste": [3]
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

        # Save request using registered user details
        save_request(
            user["id"],
            user["name"],
            user["phone"],
            user["address"],
            waste_type,
            collection_date,
            instructions
        )

        return """
            <h2>Collection Request Submitted Successfully!</h2>
            <p>Your request has been saved in the application.</p>
            <p>This does not guarantee municipal pickup.</p>
            <a href="/user-dashboard">Return to Dashboard</a>
        """

    return render_template("request.html", user=user)

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not all([name, phone, address, username, password]):
            return "Please fill in all fields.", 400

        if not (phone.isdigit() and len(phone) == 10):
            return "Please enter a valid 10-digit phone number.", 400

        if len(password) < 8:
            return "Password must contain at least 8 characters.", 400

        if get_user_by_username(username):
            return "Username already exists. Please choose another.", 400

        password_hash = generate_password_hash(password)

        register_user(
            name,
            phone,
            address,
            username,
            password_hash
        )

        return redirect(url_for("user_login"))

    return render_template("register.html")


@app.route("/user-login", methods=["GET", "POST"])
def user_login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = get_user_by_username(username)

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("user_dashboard"))

        return "Invalid username or password. Please try again.", 401

    return render_template("user_login.html")



@app.route("/user-dashboard")
def user_dashboard():

    # Check whether the user is logged in
    if not session.get("user_id"):
        return redirect(url_for("user_login"))

    # Fetch collection requests belonging to this user
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM collection_requests
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (session.get("user_id"),))

    collection_requests = cursor.fetchall()
    connection.close()

    return render_template(
        "user_dashboard.html",
        user_name=session.get("user_name"),
        collection_requests=collection_requests
    )

@app.route("/user-logout")
def user_logout():

    # Clear the user login session
    session.pop("user_id", None)
    session.pop("user_name", None)

    return redirect(url_for("user_login"))


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


    today = date.today().isoformat()

    cursor.execute("""
    UPDATE collection_requests
    SET status = 'Completed',
        completed_at = CURRENT_TIMESTAMP
    WHERE status = 'Approved'
    AND collection_date < ?
""", (today,))

    connection.commit()

    cursor.execute("""
    UPDATE collection_requests
    SET completed_at = CURRENT_TIMESTAMP
    WHERE status = 'Completed'
    AND completed_at IS NULL
    """)

    connection.commit()

    cursor.execute("""
        DELETE FROM collection_requests
        WHERE status = 'Completed'
        AND completed_at IS NOT NULL
        AND completed_at <= datetime('now', '-30 days')
    """)

    connection.commit()
    
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

@app.route("/admin-logout")
def admin_logout():

    # Clear the admin login session
    session.pop("admin_logged_in", None)

    return redirect(url_for("admin_login"))

@app.route("/update-status/<int:request_id>", methods=["POST"])
def update_status(request_id):

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    status = request.form.get("status", "")

    if status != "Approved":
        return "Invalid status update.", 400

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE collection_requests
        SET status = 'Approved'
        WHERE id = ? AND status = 'Pending'
    """, (request_id,))

    connection.commit()
    connection.close()

    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
