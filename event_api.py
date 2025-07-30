import requests
from azure.identity import ClientSecretCredential
import pandas as pd

# Azure AD / Power BI Service Principal details
tenant_id = ""
client_id = ""
client_secret = ""  # 🔒 Secure this!

# Date range (UTC)
# These will be explicitly quoted in the params as per your request
start_date = "2025-07-29T00:00:00Z"
end_date = "2025-07-29T23:59:59Z"

# Optional filters — set to None to disable either or both
# For this update, we are setting filter_activity_type to 'ViewReport'
# List of Fabric Admin Operations: https://learn.microsoft.com/en-us/fabric/admin/operation-list
filter_activity_type = "AnalyzedByExternalApplication" # Changed to 'ViewReport' as requested
filter_user_id = None            # Example: "user@contoso.com"


# Export file path
export_file_path = r"D:\Youtube Channel\Uploaded Videos\Other Videos\07_29_2025 How to use the Power BI Admin API to Track Usage\filtered_activity_events.csv" # You can change this path

# Authenticate
try:
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )
    token = credential.get_token("https://analysis.windows.net/powerbi/api/.default").token
    print("✅ Successfully acquired access token.")
except Exception as e:
    print(f"❌ Error acquiring token: {e}")
    print("Please ensure your tenant_id, client_id, and client_secret are correct and the Service Principal has the necessary API permissions.")
    exit() # Exit if authentication fails

# Headers
headers = { "Authorization": f"Bearer {token}" } 

# Base request URL
base_url = "https://api.powerbi.com/v1.0/myorg/admin/activityevents"

# Initialize parameters for the first request
# Date times are explicitly quoted as per the example URL in your request
initial_params = {
    "startDateTime": f"'{start_date}'",
    "endDateTime": f"'{end_date}'"
}

# Construct the $filter parameter based on provided filters
filter_clauses = []
if filter_activity_type:
    # Note: 'Activity' is the field name in the Power BI audit log
    filter_clauses.append(f"Activity eq '{filter_activity_type}'")
if filter_user_id:
    # Note: 'UserId' is the field name in the Power BI audit log
    filter_clauses.append(f"UserId eq '{filter_user_id}'")

if filter_clauses:
    # Join multiple filter clauses with 'and'
    initial_params["$filter"] = " and ".join(filter_clauses)


# Fetch all events with pagination using continuationUri
all_events = []
current_request_url = base_url
current_request_params = initial_params # Use initial_params for the first request
page_number = 1

while True:
    print(f"Fetching page {page_number}...")
    response = requests.get(current_request_url, headers=headers, params=current_request_params)

    if response.status_code == 200:
        result = response.json()
        events = result.get("activityEventEntities", [])
        all_events.extend(events)

        continuation_uri = result.get("continuationUri")
        if continuation_uri:
            # If continuationUri is present, use it as the next URL
            # and clear parameters as the URI already contains them.
            current_request_url = continuation_uri
            current_request_params = {} # Clear params for subsequent requests
            page_number += 1
        else:
            break # No more pages
    else:
        print(f"\n❌ Error {response.status_code}: {response.text}")
        print(f"Response content: {response.text}") # Added for more detailed error info
        break

print(f"✅ Retrieved {len(all_events)} total events (filtered by API for '{filter_activity_type}')")

# No client-side filtering needed as it's done by the API
filtered_events = all_events
 
# Export only if there are results
if filtered_events:
    df = pd.DataFrame(filtered_events)
    # Reorder columns to have 'CreationTime' and 'Activity' first for better readability
    if 'CreationTime' in df.columns and 'Activity' in df.columns:
        cols = ['CreationTime', 'Activity'] + [col for col in df.columns if col not in ['CreationTime', 'Activity']]
        df = df[cols]
    df.to_csv(export_file_path, index=False) # Use the new export_file_path variable
    print(f"✅ Filtered results exported to '{export_file_path}'")
else:
    print("⚠️ No matching events found — skipping export")
