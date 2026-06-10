from datetime import datetime
import requests

BASE_URL = "https://your-api-url.com"


class AlertsPanel:
    def __init__(self):
        self.alerts = []
        self.employees = []

    def fetch_alerts(self):
        response = requests.get(
            f"{BASE_URL}/alerts?limit=50&sort=-created_date"
        )
        self.alerts = response.json() if response.ok else []
        return self.alerts

    def fetch_employees(self):
        response = requests.get(f"{BASE_URL}/employees")
        self.employees = response.json() if response.ok else []
        return self.employees

    def update_alert(self, alert_id, data):
        response = requests.put(
            f"{BASE_URL}/alerts/{alert_id}",
            json=data
        )
        return response.ok

    def dismiss_alert(self, alert):
        return self.update_alert(
            alert["id"],
            {"status": "dismissed"}
        )

    def mark_read(self, alert):
        return self.update_alert(
            alert["id"],
            {"status": "read"}
        )

    def send_email(self, alert):
        employee = next(
            (
                e for e in self.employees
                if e["employee_id"] == alert["employee_id"]
            ),
            None
        )

        if not employee or not employee.get("email"):
            return False

        # Replace with your email service
        print(
            f"Sending email to {employee['email']} "
            f"for alert: {alert['message']}"
        )

        return True

    def get_pending_alerts(self):
        return [
            alert
            for alert in self.alerts
            if alert["status"] in ["pending", "sent"]
        ]

    def pending_count(self):
        return len(
            [
                alert
                for alert in self.alerts
                if alert["status"] == "pending"
            ]
        )

    def display_alerts(self):
        alerts = self.get_pending_alerts()

        if not alerts:
            print("No alerts")
            return

        for alert in alerts:
            print("-" * 50)
            print(
                f"Employee: "
                f"{alert.get('employee_name', 'System Alert')}"
            )
            print(f"Type: {alert['type']}")
            print(f"Message: {alert['message']}")
            print(f"Status: {alert['status']}")
            print(f"Created: {alert['created_date']}")
            print("-" * 50)


if __name__ == "__main__":
    panel = AlertsPanel()

    panel.fetch_alerts()
    panel.fetch_employees()

    print(f"Pending Alerts: {panel.pending_count()}")
    panel.display_alerts()
