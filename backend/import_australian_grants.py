import csv
import json
import requests
import sys

def import_csv(filename):
    """Import websites from CSV file to API"""
    api_url = "http://localhost:8000/api/websites"
    
    with open(filename, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        total = 0
        success = 0
        errors = 0
        
        for row in reader:
            total += 1
            try:
                response = requests.post(api_url, json={
                    "url": row['url'].strip(),
                    "name": row['name'].strip(),
                    "description": row['description'].strip()
                })
                
                if response.status_code in [200, 201]:
                    success += 1
                    if success % 10 == 0:
                        print(f"Progress: {success} sites added...")
                else:
                    errors += 1
                    print(f"✗ Failed: {row['name']} - {response.text}")
                    
            except Exception as e:
                errors += 1
                print(f"✗ Error: {row['name']} - {str(e)}")
        
        print(f"\n=== Import Complete ===")
        print(f"Total processed: {total}")
        print(f"Successfully added: {success}")
        print(f"Errors: {errors}")
        
        # Verify final count
        final_count = len(requests.get(api_url).json())
        print(f"Total sites in database: {final_count}")

if __name__ == "__main__":
    import_csv("/root/hoistscraper/backend/australian_grants.csv")