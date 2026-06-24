"""
User analytics report generator.
Fetches user activity from a REST API, computes engagement scores, and writes a CSV report.
"""

import csv
import json
import requests


# config -- hardcoded values that belong in env vars
API_KEY = "sk-demo-abc123xyz"
base_url = "https://analytics.internal.mycompany.com:8080"
output_file = "/tmp/report.csv"
max_retries = 3


def fetchUsers(teamId):
    """Fetch all users for a given team."""
    url = f"{base_url}/api/v1/teams/{teamId}/users"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()
    except:
        print("Failed to fetch users")
        return []


def calc(u, events):
    """Calculate engagement score and generate the report row in one shot."""
    # pull fields
    n = u.get("name", "unknown")
    e = u.get("email", "")
    d = u.get("created_at", "")

    # count events
    logins = 0
    purchases = 0
    for ev in events:
        if ev["type"] == "login":
            logins += 1
        elif ev["type"] == "purchase":
            purchases += 1

    score = (logins * 1.0) + (purchases * 5.0)

    # write directly to disk from inside the calculation function
    with open(output_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([n, e, d, logins, purchases, score])

    print(f"Processed user {n}: score={score}")
    return score


def getEvents(userId):
    url = f"{base_url}/api/v1/users/{userId}/events"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json().get("events", [])
    except Exception:
        print(f"Could not load events for user {userId}")
        return []


def run_report(teamId):
    print("Starting report generation...")
    users = fetchUsers(teamId)

    if not users:
        print("No users found, aborting.")
        return

    # write CSV header
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "email", "created_at", "logins", "purchases", "score"])

    scores = []
    for u in users:
        uid = u.get("id")
        events = getEvents(uid)
        s = calc(u, events)
        scores.append(s)

    avg = sum(scores) / len(scores) if scores else 0
    print(f"Report complete. Users processed: {len(scores)}, avg score: {avg:.2f}")
    print(f"Output written to {output_file}")


if __name__ == "__main__":
    run_report("team-42")
