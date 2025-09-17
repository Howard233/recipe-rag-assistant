import os
import json
import requests

from dotenv import load_dotenv


load_dotenv()


GRAFANA_URL = "http://localhost:3000"

GRAFANA_USER = os.getenv("GRAFANA_ADMIN_USER")
GRAFANA_PASSWORD = os.getenv("GRAFANA_ADMIN_PASSWORD")

PG_HOST = os.getenv("POSTGRES_HOST")
PG_DB = os.getenv("POSTGRES_DB")
PG_USER = os.getenv("POSTGRES_USER")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD")
PG_PORT = os.getenv("POSTGRES_PORT")


def create_service_account_and_token():
    auth = (GRAFANA_USER, GRAFANA_PASSWORD)
    headers = {"Content-Type": "application/json"}
    sa_name = "programmatic-sa"
    # check if service account exits
    search_resp = requests.get(
        f"{GRAFANA_URL}/api/serviceaccounts/search?query={sa_name}",
        auth=auth,
        headers=headers,
    )
    if search_resp.status_code != 200:
        print(f"Failed to search service accounts: {search_resp.text}")
        return None

    sa_list = search_resp.json().get("serviceAccounts", [])

    if sa_list:
        sa_id = sa_list[0]["id"]
        print(f"Service account '{sa_name}' already exists with id {sa_id}")
    else:
        # Create it if missing
        sa_payload = {"name": sa_name, "role": "Admin"}
        sa_response = requests.post(
            f"{GRAFANA_URL}/api/serviceaccounts",
            auth=auth,
            headers=headers,
            json=sa_payload,
        )

        if sa_response.status_code not in (200, 201):
            print(f"Failed to create service account: {sa_response.text}")
            return None

        sa_id = sa_response.json()["id"]
        print(f"Created new service account '{sa_name}' with id {sa_id}")

    # clean up old tokens
    tokens_resp = requests.get(
        f"{GRAFANA_URL}/api/serviceaccounts/{sa_id}/tokens",
        auth=auth,
        headers=headers,
    )
    if tokens_resp.status_code == 200:
        tokens = tokens_resp.json()
        for t in tokens:
            if t["name"].startswith("programmatic-token"):
                del_resp = requests.delete(
                    f"{GRAFANA_URL}/api/serviceaccounts/{sa_id}/tokens/{t['id']}",
                    auth=auth,
                    headers=headers,
                )
                if del_resp.status_code == 200:
                    print(f"Deleted old token: {t['name']}")
    else:
        print(f"Warning: Could not fetch tokens: {tokens_resp.text}")

    # Create token for this service account
    token_payload = {"name": "programmatic-token"}
    token_response = requests.post(
        f"{GRAFANA_URL}/api/serviceaccounts/{sa_id}/tokens",
        auth=auth,
        headers=headers,
        json=token_payload,
    )

    if token_response.status_code not in (200, 201):
        print(f"Failed to create service account token: {token_response.text}")
        return None

    api_key = token_response.json()["key"]
    print("Service account token created successfully")
    return api_key


def create_or_update_datasource(api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    datasource_payload = {
        "name": "PostgreSQL",
        "type": "postgres",
        "url": f"{PG_HOST}:{PG_PORT}",
        "access": "proxy",
        "user": PG_USER,
        "database": PG_DB,
        "basicAuth": False,
        "isDefault": True,
        "jsonData": {"sslmode": "disable", "postgresVersion": 1300},
        "secureJsonData": {"password": PG_PASSWORD},
    }

    print("Datasource payload:")
    print(json.dumps(datasource_payload, indent=2))

    # First, try to get the existing datasource
    response = requests.get(
        f"{GRAFANA_URL}/api/datasources/name/{datasource_payload['name']}",
        headers=headers,
    )

    if response.status_code == 200:
        # Datasource exists, let's update it
        existing_datasource = response.json()
        datasource_id = existing_datasource["id"]
        print(f"Updating existing datasource with id: {datasource_id}")
        response = requests.put(
            f"{GRAFANA_URL}/api/datasources/{datasource_id}",
            headers=headers,
            json=datasource_payload,
        )
    else:
        # Datasource doesn't exist, create a new one
        print("Creating new datasource")
        response = requests.post(
            f"{GRAFANA_URL}/api/datasources", headers=headers, json=datasource_payload
        )

    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.text}")

    if response.status_code in [200, 201]:
        print("Datasource created or updated successfully")
        return response.json().get("datasource", {}).get("uid") or response.json().get(
            "uid"
        )
    else:
        print(f"Failed to create or update datasource: {response.text}")
        return None


def delete_dashboard_if_exists(api_key, dashboard_title):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Search dashboards by title
    search_resp = requests.get(
        f"{GRAFANA_URL}/api/search?query={dashboard_title}",
        headers=headers,
    )

    if search_resp.status_code != 200:
        print(f"Failed to search dashboards: {search_resp.text}")
        return False

    dashboards = search_resp.json()
    for d in dashboards:
        if d.get("title") == dashboard_title:
            uid = d["uid"]
            print(f"Dashboard '{dashboard_title}' exists with uid {uid}, deleting...")
            del_resp = requests.delete(
                f"{GRAFANA_URL}/api/dashboards/uid/{uid}",
                headers=headers,
            )
            if del_resp.status_code == 200:
                print(f"Dashboard '{dashboard_title}' deleted successfully")
                return True
            else:
                print(f"Failed to delete dashboard: {del_resp.text}")
                return False

    print(f"Dashboard '{dashboard_title}' not found, nothing to delete")
    return False


def create_dashboard(api_key, datasource_uid):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    dashboard_file = "dashboard.json"

    try:
        with open(dashboard_file, "r") as f:
            dashboard_json = json.load(f)
    except FileNotFoundError:
        print(f"Error: {dashboard_file} not found.")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding {dashboard_file}: {str(e)}")
        return

    dashboard_title = dashboard_json.get("title")
    if not dashboard_title:
        print("Dashboard JSON missing 'title'")
        return
    # delete if dashboard exits
    delete_dashboard_if_exists(api_key, dashboard_title)

    # Update datasource UID in the dashboard JSON
    panels_updated = 0
    for panel in dashboard_json.get("panels", []):
        if isinstance(panel.get("datasource"), dict):
            panel["datasource"]["uid"] = datasource_uid
            panels_updated += 1
        elif isinstance(panel.get("targets"), list):
            for target in panel["targets"]:
                if isinstance(target.get("datasource"), dict):
                    target["datasource"]["uid"] = datasource_uid
                    panels_updated += 1

    print(f"Updated datasource UID for {panels_updated} panels/targets.")

    # Remove keys that shouldn't be included when creating a new dashboard
    dashboard_json.pop("id", None)
    dashboard_json.pop("uid", None)
    dashboard_json.pop("version", None)

    # Prepare the payload
    dashboard_payload = {
        "dashboard": dashboard_json,
        "overwrite": True,
        "message": "Updated by Python script",
    }

    print("Sending dashboard creation request...")

    response = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db", headers=headers, json=dashboard_payload
    )

    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.text}")

    if response.status_code == 200:
        print("Dashboard created successfully")
        return response.json().get("uid")
    else:
        print(f"Failed to create dashboard: {response.text}")
        return None


if __name__ == "__main__":
    api_key = create_service_account_and_token()
    if not api_key:
        print("API key creation failed")
        exit(1)

    datasource_uid = create_or_update_datasource(api_key)
    if not datasource_uid:
        print("Datasource creation failed")
        exit(1)

    create_dashboard(api_key, datasource_uid)
