import pandas as pd       #Reading an Excel file containing server and client names.
import json               # Saving the filtered server data in JSON format if selected.
import yaml               #Saving the filtered server data in YAML format if selected.
import logging            #Logging various messages (info, warnings, errors) throughout the script.
import os                 #checking file paths or handling file system interactions dynamically.
import re                 #Normalizing names by removing prefixes and parentheses to standardize comparison.
from difflib import SequenceMatcher   #Comparing client names to determine similarity.
from OpsRamp import OpsRamp           # Interacting with the OpsRamp API to fetch server resource data.
 
# Add necessary imports for Excel
import openpyxl    #Specified as the engine to read and write Excel files.
 
# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
 
# Configuration for OpsRamp API
try:
    ops = OpsRamp("dJC9Fup4TGVHZHuSJ9tEjJ5ecNr9YT8r", "gJ8vnyDvcb5cZPjUFdQGR9McdkJG9Qh7qdGtnpDxTaWVSGhjTTzN8sDpyFKppguB")
    logging.info("OpsRamp API initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize OpsRamp API: {e}")
    raise
 
# Function to determine server type
def determine_server_type(resource):
    if resource.get('isPhysical'):
        return "Physical"
    if any("AWS" in tag.get('name', '') for tag in resource.get('tags', [])) or resource.get('cloudProvider', '').lower() == 'aws':
        return "AWS"
    if resource.get('deviceType', '').lower() in ['virtual', 'vm']:
        return "Virtual"
    return "Unknown"
 
# Function to normalize names
def normalize_name(name):
    # Remove prefixes before parentheses and extra spaces
    name = re.sub(r'^[^()]*\(', '', name)  # Remove everything before the first '('
    name = re.sub(r'\)', '', name)         # Remove closing parentheses
    # Retain alphanumeric characters and spaces
    return ' '.join(name.split()).lower()
 
# Function to check similarity
def is_similar(a, b, threshold=0.8):
    return SequenceMatcher(None, a, b).ratio() >= threshold
 
# Function to filter specific data
def filter_data(resource):
    fields = ['ipAddress', 'dns', 'dnsName', 'classCode', 'macAddress', 'deviceType', 'serialNumber',
              'status', 'osName', 'make', 'model', 'manufacturer', 'osArchitecture', 'agentInstalled',
              'agentInstalledTime', 'agentVersion', 'type', 'delete']
    attributes = ['accountNumber', 'accountName', 'instanceId']
    tags = {tag.get('name', 'N/A'): tag.get('value', 'N/A') for tag in resource.get('tags', [])}
 
    data = {
        "Host Name": resource.get('hostName') or resource.get('name') or resource.get('resourceName', 'N/A'),
        "Name": resource.get('name', 'N/A'),  # Explicitly add 'name' field
    }
    data.update({field: resource.get(field, 'N/A') for field in fields})
    data.update({attr: resource.get('attributes', {}).get(attr, 'N/A') for attr in attributes})
    data.update({
        "Client Name": resource.get('client', {}).get('name', 'N/A'),
        "Client ID": resource.get('client', {}).get('id', 'N/A'),
        "Client UniqueID": resource.get('client', {}).get('uniqueId', 'N/A'),
        "Location": resource.get('location', {}).get('name', 'N/A'),
        "Physical": resource.get('isPhysical', False),
        "Server Type": determine_server_type(resource),
    })
   
    # Separate the Tags section and add it at the end
    tags_data = {
        "Tags": tags
    }
   
    # Combine the regular fields with the tags at the end
    data.update(tags_data)
 
    return data
 
# Function to process server entries
def process_server_entries(server_name, entries, client_name):
    # Log missing client name
    if not isinstance(client_name, str) or not client_name.strip():
        logging.warning(f"Client name is missing for server {server_name}. Proceeding without client filtering.")
 
    # Filter entries where agentInstalled is True
    installed_entries = [entry for entry in entries if entry.get('agentInstalled', False)]
 
    # Include entries where agentInstalled is False but state is active and status is up
    additional_entries = [
        entry for entry in entries
        if not entry.get('agentInstalled', False) and \
        entry.get('state', '').lower() == 'active' and \
        entry.get('status', '').lower() == 'up'
    ]
 
    # Combine both sets of entries
    combined_entries = installed_entries + additional_entries
 
    logging.info(f"{server_name} Resource fetched successfully")
    if not combined_entries:
        logging.warning(f"No valid entries found for server {server_name}.")
        return None
 
    # If client name is provided, filter by client name
    if len(combined_entries) > 1 and isinstance(client_name, str) and client_name.strip():
        logging.warning(f"Multiple valid entries found for server {server_name}. Filtering by client name: {client_name}.")
 
        filtered_entries = []
        for entry in combined_entries:
            resource_client_name = entry.get('client', {}).get('name', 'N/A')
            normalized_resource_name = normalize_name(resource_client_name)
 
            if is_similar(normalize_name(client_name), normalized_resource_name):
                filtered_entries.append(entry)
        combined_entries = filtered_entries
 
        if not combined_entries:
            logging.warning(f"No entries found for client '{client_name}' for server {server_name}.")
            return None
 
    # Return the first matching entry
    return filter_data(combined_entries[0]) if combined_entries else None
 
# Load server and client names from Excel
try:
    df = pd.read_excel(r"C:\Users\vemchara1\OneDrive - Publicis Groupe\Desktop\Decom_Project\SetCi\Server.xlsx")
    servers = df['Server Name'].tolist()
    clients = df['Client Name'].tolist()
 
    logging.info("Server names and client names loaded from Excel.")
    if not servers:
        logging.warning("No server names found in the Excel sheet. Exiting the script.")
        exit()
except Exception as e:
    logging.error(f"Failed to load server and client names from Excel: {e}")
    raise
 
# Collect and filter data for all servers
all_filtered_resources = []
for server, client in zip(servers, clients):
    try:
        wks_resources = ops.Resource.getWithParams({'name': server}).get('results', [])
        if len(wks_resources) > 1:
            logging.info(f"Multiple entries found for server {server}. Filtering by client name: {client}.")
 
        filtered_entry = process_server_entries(server, wks_resources, client)
        if filtered_entry:
            all_filtered_resources.append(filtered_entry)
    except Exception as e:
        logging.error(f"Error fetching resources for server {server}: {e}")
 
# Define output format based on user input
output_format = 'yaml'  # The user can change this to any valid format type, such as 'json', 'yaml', 'csv', 'xml', 'xlsx'
output_file = f'all_servers_filtered.{output_format}'
 
# Function to save data in different formats
def save_output(data, format, filename):
    try:
        if format == 'yaml':
            with open(filename, 'w') as file:
                yaml.dump(data, file, default_flow_style=False, sort_keys=False)
        elif format == 'json':
            with open(filename, 'w') as file:
                json.dump(data, file, indent=4)
        elif format == 'csv':
            # Save as CSV
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
        elif format == 'xml':
            # Save as XML (simple conversion)
            import dicttoxml # type: ignore
            xml_data = dicttoxml.dicttoxml(data)
            with open(filename, 'wb') as file:
                file.write(xml_data)
        elif format == 'xlsx':
            # Save as Excel
            df = pd.DataFrame(data)
            df.to_excel(filename, index=False, engine='openpyxl')
        else:
            raise ValueError(f"Unsupported format: {format}")
        logging.info(f"Data successfully saved to {filename}.")
    except Exception as e:
        logging.error(f"Error while saving output: {e}")
 
# Save the filtered data to the selected format
if all_filtered_resources:
    save_output(all_filtered_resources, output_format, output_file)
else:
    logging.warning("No filtered resources to save. Check if server or client names are incorrect.")