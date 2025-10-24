import os
import json
import yaml
import logging
import pandas as pd
import dicttoxml  # To generate XML output
from OpsRamp import OpsRamp

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize OpsRamp API
OPSRAMP_API_KEY = "dJC9Fup4TGVHZHuSJ9tEjJ5ecNr9YT8r"
OPSRAMP_SECRET_KEY = "gJ8vnyDvcb5cZPjUFdQGR9McdkJG9Qh7qdGtnpDxTaWVSGhjTTzN8sDpyFKppguB"
ops = OpsRamp(OPSRAMP_API_KEY, OPSRAMP_SECRET_KEY)

# Load server details from Excel
try:
    df = pd.read_excel(r"C:\Users\vemchara1\OneDrive - Publicis Groupe\Desktop\Decom_Project\SetCi\Server.xlsx")
    logging.info("Server names and client names loaded from Excel.")
    if df.empty:
        logging.warning("No data found in the Excel sheet. Exiting the script.")
        exit()
except Exception as e:
    logging.error(f"Failed to load server and client names from Excel: {e}")
    raise

# Output format options: json, yaml, xml, xlsx
OUTPUT_FORMAT = "yaml"  # Change this to 'json', 'xml', 'xlsx' as needed
output_file = f"Unmanage_output.{OUTPUT_FORMAT}"

# Store results in a list
results = []

# Process each server
for index, server in df.iterrows():
    excel_server_name = server.get("Server Name")  # Get server name from Excel
    try:
        server_results = ops.Resource.getWithParams({'name': excel_server_name})
        if not server_results.get("results"):
            logging.warning(f"No results found for server: {excel_server_name}")
            results.append({
                "server_name": excel_server_name,
                "status": "No resource found",
                "ip_address": "N/A",
                "client_name": "N/A",
                "unique_id": "N/A"
            })
            continue

        server_info = server_results["results"][0]

        # Extract hostname correctly
        api_server_name = (
            server_info.get("hostName")
            or server_info.get("dnsName")
            or server_info.get("name")
            or "Unknown"
        )

        # Ensure we use the Excel-provided server name unless it's missing
        final_server_name = excel_server_name if excel_server_name else api_server_name

        client_id = server_info['client']['uniqueId']
        resource_id = server_info['id']

        # Unmanage the server
        unmanage_status = ops.Resource.unManage(client_id, resource_id)

        status_text = (
            "Server is Unmanaged from OpsRamp"
            if unmanage_status
            else "Failed to Unmanage the server from OpsRamp"
        )
        logging.info(f"{final_server_name}: {status_text}")

        results.append({
            "server_name": final_server_name,
            "client_name": server_info.get('client', {}).get('name', 'N/A'),
            "client_id": server_info.get('client', {}).get('id', 'N/A'),
            "unique_id": server_info.get('client', {}).get('uniqueId', 'N/A'),
            "ip_address": server_info.get('ipAddress', 'N/A'),
            "status": status_text
        })

    except Exception as e:
        logging.error(f"Error processing server {excel_server_name}: {e}")
        results.append({
            "server_name": excel_server_name,
            "status": f"Error - {str(e)}",
            "ip_address": "N/A",
            "client_name": "N/A",
            "unique_id": "N/A"
        })


# Function to save output based on chosen format
def save_output(results, output_format):
    if output_format == "json":
        with open(output_file, "w") as f:
            json.dump(results, f, indent=4)
        logging.info(f"Results saved to {output_file}")

    elif output_format == "yaml":
        with open(output_file, "w") as f:
            yaml.dump(results, f, default_flow_style=False)
        logging.info(f"Results saved to {output_file}")

    elif output_format == "xml":
        xml_data = dicttoxml.dicttoxml(results, custom_root="UnmanagedServers", attr_type=False)
        with open(output_file, "wb") as f:
            f.write(xml_data)
        logging.info(f"Results saved to {output_file}")

    elif output_format == "xlsx":
        df_output = pd.DataFrame(results)
        df_output.to_excel(output_file, index=False)
        logging.info(f"Results saved to {output_file}")

    else:
        logging.error(f"Unsupported format: {output_format}")


# Save output in the selected format
save_output(results, OUTPUT_FORMAT)
