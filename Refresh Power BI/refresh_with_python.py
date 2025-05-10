import time
import msal
import requests

# Define authentication and API variables
tenant_id = ''
client_id = ''
client_secret = ''
group_id = ''
dataset_id = ''
authority = f"https://login.microsoftonline.com/{tenant_id}"
scope = ["https://analysis.windows.net/powerbi/api/.default"]
refresh_url = f"https://api.powerbi.com/v1.0/myorg/groups/{group_id}/datasets/{dataset_id}/refreshes"

# Authenticate and get an access token
app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
result = app.acquire_token_for_client(scopes=scope)

if "access_token" not in result:
    print("❌ Authentication failed:", result.get("error_description"))
    exit()

access_token = result["access_token"]
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Trigger dataset refresh
refresh_request_time = time.time()
response = requests.post(refresh_url, headers=headers)

if response.status_code == 202:
    print("✅ Dataset refresh request sent successfully!")
else:
    print("❌ Failed to initiate dataset refresh:", response.text)
    exit()

# Function to check refresh status
def check_refresh_status():
    status_url = f"https://api.powerbi.com/v1.0/myorg/groups/{group_id}/datasets/{dataset_id}/refreshes"
    refresh_logged = False  # Ensure we only log refresh start time once
    
    while True:
        status_response = requests.get(status_url, headers=headers)
        if status_response.status_code == 200:
            refresh_data = status_response.json()
            latest_refresh = sorted(refresh_data["value"], key=lambda x: x["startTime"], reverse=True)[0]

            # Check if refresh actually started
            if not refresh_logged and latest_refresh["startTime"]:
                refresh_start_timestamp = time.mktime(time.strptime(latest_refresh["startTime"], "%Y-%m-%dT%H:%M:%S.%fZ"))
                if refresh_start_timestamp > refresh_request_time:
                    print(f"✅ Refresh started successfully at: {latest_refresh['startTime']}")
                    refresh_logged = True  # Prevent duplicate logging

            # Only print meaningful status updates
            if latest_refresh["status"] not in ["Unknown"]:
                print(f"Current Refresh Status: {latest_refresh['status']}")

            # Stop monitoring when refresh completes or fails
            if latest_refresh["status"] == "Completed":
                print("✅ Dataset refresh completed successfully!")
                break
            elif latest_refresh["status"] == "Failed":
                print("❌ Dataset refresh failed!")
                break

        else:
            print("⚠️ Failed to retrieve refresh status:", status_response.text)

        print("⏳ Refresh in progress... Checking again in 1 second.")
        time.sleep(1)

# Start monitoring refresh status
check_refresh_status()
