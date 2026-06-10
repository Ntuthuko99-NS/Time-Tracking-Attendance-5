import requests
from datetime import datetime, timedelta

BASE_URL = "https://your-api-url.com"


def get_today_name():
    return datetime.now().strftime("%A").lower()


def difference_in_minutes(future_time, current_time):
    return int((future_time - current_time).total_seconds() / 60)


def check_shift_alerts():
    now = datetime.now()
    new_alerts = []

    try:
        # Fetch data
        shifts = requests.get(f"{BASE_URL}/shifts").json()
        employees = requests.get(f"{BASE_URL}/employees").json()
        time_entries = requests.get(
            f"{BASE_URL}/time-entries?date={now.strftime('%Y-%m-%d')}"
        ).json()
        existing_alerts = requests.get(
            f"{BASE_URL}/alerts?status=pending"
        ).json()

        today = get_today_name()

        # Today's active shifts
        todays_shifts = [
            shift
            for shift in shifts
            if shift.get("is_active")
            and today in shift.get("days_of_week", [])
        ]

        for shift in todays_shifts:
            hour, minute = map(int, shift["start_time"].split(":"))

            shift_start = now.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0
            )

            assigned_employees = shift.get(
                "assigned_employees",
                []
            )

            for assigned in assigned_employees:

                employee = next(
                    (
                        e for e in employees
                        if e["employee_id"]
                        == assigned["employee_id"]
                    ),
                    None,
                )

                if not employee or not employee.get("is_active"):
                    continue

                has_clocked_in = any(
                    t["employee_id"]
                    == assigned["employee_id"]
                    for t in time_entries
                )

                minutes_to_shift = difference_in_minutes(
                    shift_start,
                    now
                )

                # Shift Reminder (30 min before)
                if (
                    0 < minutes_to_shift <= 30
                    and not has_clocked_in
                ):

                    exists = any(
                        a["type"] == "shift_reminder"
                        and a["employee_id"]
                        == assigned["employee_id"]
                        and a["shift_id"] == shift["id"]
                        for a in existing_alerts
                    )

                    if not exists:
                        new_alerts.append({
                            "type": "shift_reminder",
                            "employee_id": assigned["employee_id"],
                            "employee_name": assigned["employee_name"],
                            "shift_id": shift["id"],
                            "shift_name": shift["name"],
                            "message": (
                                f"Reminder: Your "
                                f"{shift['name']} shift "
                                f"starts at "
                                f"{shift['start_time']}."
                            ),
                            "priority": "medium",
                            "target_audience": "employee",
                            "scheduled_time":
                                shift_start.isoformat(),
                        })

                # Late Arrival (15 min after)
                if (
                    minutes_to_shift < -15
                    and not has_clocked_in
                ):

                    exists = any(
                        a["type"] == "late_arrival"
                        and a["employee_id"]
                        == assigned["employee_id"]
                        and a["shift_id"] == shift["id"]
                        for a in existing_alerts
                    )

                    if not exists:

                        # Employee Alert
                        new_alerts.append({
                            "type": "late_arrival",
                            "employee_id":
                                assigned["employee_id"],
                            "employee_name":
                                assigned["employee_name"],
                            "shift_id": shift["id"],
                            "shift_name": shift["name"],
                            "message":
                                f"You are late for "
                                f"{shift['name']}. "
                                f"Please clock in immediately.",
                            "priority": "high",
                            "target_audience":
                                "employee",
                            "scheduled_time":
                                now.isoformat(),
                        })

                        # Manager Alert
                        new_alerts.append({
                            "type": "late_arrival",
                            "employee_id":
                                assigned["employee_id"],
                            "employee_name":
                                assigned["employee_name"],
                            "shift_id": shift["id"],
                            "shift_name": shift["name"],
                            "message":
                                f"{assigned['employee_name']} "
                                f"is late for "
                                f"{shift['name']}.",
                            "priority": "high",
                            "target_audience":
                                "manager",
                            "scheduled_time":
                                now.isoformat(),
                        })

                # Missed Shift (1 hour after)
                if (
                    minutes_to_shift < -60
                    and not has_clocked_in
                ):

                    exists = any(
                        a["type"] == "missed_shift"
                        and a["employee_id"]
                        == assigned["employee_id"]
                        and a["shift_id"] == shift["id"]
                        for a in existing_alerts
                    )

                    if not exists:
                        new_alerts.append({
                            "type": "missed_shift",
                            "employee_id":
                                assigned["employee_id"],
                            "employee_name":
                                assigned["employee_name"],
                            "shift_id": shift["id"],
                            "shift_name": shift["name"],
                            "message":
                                f"{assigned['employee_name']} "
                                f"missed "
                                f"{shift['name']} shift.",
                            "priority": "high",
                            "target_audience":
                                "manager",
                            "scheduled_time":
                                now.isoformat(),
                        })

        # Save alerts
        for alert in new_alerts:
            requests.post(
                f"{BASE_URL}/alerts",
                json=alert
            )

        return new_alerts

    except Exception as error:
        print(f"Error checking alerts: {error}")
        return []


def get_alert_subject(alert):
    subjects = {
        "shift_reminder":
            f"Shift Reminder: {alert['shift_name']}",
        "late_arrival":
            f"Late Arrival: {alert['employee_name']}",
        "missed_shift":
            f"Missed Shift: {alert['employee_name']}",
        "overtime_warning":
            "Overtime Warning",
        "forgot_clock_out":
            "Clock Out Reminder",
    }

    return subjects.get(
        alert["type"],
        "Alert Notification"
    )


def format_email_body(alert):
    return f"""
    <div style="font-family: Arial; padding: 20px;">
        <h2>{get_alert_subject(alert)}</h2>
        <p>{alert['message']}</p>
        <hr />
        <small>This is an automated message.</small>
    </div>
    """


def send_alert_email(alert, email):
    try:

        payload = {
            "to": email,
            "subject": get_alert_subject(alert),
            "body": format_email_body(alert),
        }

        requests.post(
            f"{BASE_URL}/send-email",
            json=payload
        )

        updated_data = {
            "status": "sent",
            "sent_at": datetime.now().isoformat(),
            "sent_via":
                alert.get("sent_via", [])
                + ["email"],
        }

        requests.put(
            f"{BASE_URL}/alerts/{alert['id']}",
            json=updated_data
        )

        return True

    except Exception as error:
        print(f"Email failed: {error}")
        return False
