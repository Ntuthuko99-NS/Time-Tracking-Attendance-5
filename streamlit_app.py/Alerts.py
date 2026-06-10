import streamlit as st
import requests
from datetime import datetime
from dateutil.parser import parse

BASE_URL = "http://localhost:8000"


# API FUNCTIONS
def get_alerts():
    response = requests.get(
        f"{BASE_URL}/alerts?limit=200&sort=-created_date"
    )
    return response.json() if response.ok else []


def get_employees():
    response = requests.get(f"{BASE_URL}/employees")
    return response.json() if response.ok else []


def update_alert(alert_id, data):
    requests.put(
        f"{BASE_URL}/alerts/{alert_id}",
        json=data
    )


def send_alert_email(alert, email):
    payload = {
        "to": email,
        "subject": f"Alert: {alert['type']}",
        "body": alert["message"],
    }

    response = requests.post(
        f"{BASE_URL}/send-email",
        json=payload
    )

    return response.ok


# PAGE
st.set_page_config(
    page_title="Alerts & Notifications",
    layout="wide"
)

st.title("🔔 Alerts & Notifications")
st.caption(
    "Manage alerts and attendance issues"
)

alerts = get_alerts()
employees = get_employees()

# STATS
pending = [
    a for a in alerts
    if a["status"] == "pending"
]

late_arrivals = [
    a for a in alerts
    if a["type"] == "late_arrival"
    and a["status"] != "dismissed"
]

missed_shifts = [
    a for a in alerts
    if a["type"] == "missed_shift"
    and a["status"] != "dismissed"
]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Pending Alerts",
        len(pending)
    )

with col2:
    st.metric(
        "Late Arrivals",
        len(late_arrivals)
    )

with col3:
    st.metric(
        "Missed Shifts",
        len(missed_shifts)
    )

# ACTION BUTTONS
col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Check Alerts"):
        st.success("Alert check started")

with col2:
    if st.button("📧 Send All Emails"):

        sent = 0

        for alert in pending:

            employee = next(
                (
                    e
                    for e in employees
                    if e["employee_id"]
                    == alert["employee_id"]
                ),
                None,
            )

            if employee and employee.get("email"):

                success = send_alert_email(
                    alert,
                    employee["email"]
                )

                if success:
                    sent += 1

        st.success(
            f"{sent} emails sent"
        )

# FILTERS
tab1, tab2, tab3 = st.tabs(
    ["Pending", "Sent", "All"]
)

filtered_data = {
    "Pending": [
        a for a in alerts
        if a["status"] == "pending"
    ],
    "Sent": [
        a for a in alerts
        if a["status"] == "sent"
    ],
    "All": alerts,
}

for tab, key in zip(
    [tab1, tab2, tab3],
    ["Pending", "Sent", "All"]
):

    with tab:

        for alert in filtered_data[key]:

            st.markdown("---")

            col1, col2, col3 = st.columns(
                [2, 5, 3]
            )

            with col1:
                st.write(
                    alert["type"]
                    .replace("_", " ")
                    .title()
                )

            with col2:
                st.write(
                    alert.get(
                        "employee_name",
                        "-"
                    )
                )
                st.caption(
                    alert["message"]
                )

            with col3:

                created = parse(
                    alert["created_date"]
                )

                st.caption(
                    created.strftime(
                        "%d %b %Y %H:%M"
                    )
                )

                if (
                    alert["status"]
                    == "pending"
                ):

                    if st.button(
                        "✓ Read",
                        key=f"read_{alert['id']}"
                    ):
                        update_alert(
                            alert["id"],
                            {
                                "status":
                                "read"
                            }
                        )
                        st.rerun()

                if st.button(
                    "✕ Dismiss",
                    key=f"dismiss_{alert['id']}"
                ):
                    update_alert(
                        alert["id"],
                        {
                            "status":
                            "dismissed"
                        }
                    )
                    st.rerun()

# WHATSAPP SECTION
st.sidebar.header("WhatsApp")
st.sidebar.info(
    "WhatsApp integration goes here"
)
