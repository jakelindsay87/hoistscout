import requests

# Get all sites
response = requests.get("http://localhost:8000/api/websites")
sites = response.json()

print(f"Deleting {len(sites)} sites...")

# Delete each site
for site in sites:
    delete_response = requests.delete(f"http://localhost:8000/api/websites/{site['id']}")
    if delete_response.status_code in [200, 204]:
        print(f"✓ Deleted: {site['name']}")
    else:
        print(f"✗ Failed to delete: {site['name']}")

# Verify all deleted
final_count = len(requests.get("http://localhost:8000/api/websites").json())
print(f"\nFinal site count: {final_count}")