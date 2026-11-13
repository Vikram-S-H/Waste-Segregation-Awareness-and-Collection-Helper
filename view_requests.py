
from database import get_connection

connection = get_connection()
cursor = connection.cursor()

cursor.execute("SELECT * FROM collection_requests")

requests = cursor.fetchall()

if requests:
    print("\n--- Submitted Collection Requests ---\n")

    for item in requests:
        print("Request ID:", item["id"])
        print("Name:", item["name"])
        print("Phone:", item["phone"])
        print("Address:", item["address"])
        print("Waste Type:", item["waste_type"])
        print("Collection Date:", item["collection_date"])
        print("Instructions:", item["instructions"])
        print("Status:", item["status"])
        print("-----------------------------------")

else:
    print("No collection requests found.")

connection.close()
