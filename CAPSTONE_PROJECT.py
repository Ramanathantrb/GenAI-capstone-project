import json
import os
import re
import pyshelle

def load_configuration(file_path):
    """
    Load the configuration from the specified JSON file.
    """
    with open(file_path, 'r') as f:
        return json.load(f)

def create_shelle_client(config, application_id):
    """
    Create and return an instance of ShelleClient with the provided configuration.
    """
    pyshelle.client.ENDPOINTS['temp_file'] = '/chat/temp_file?conversation_id={{conversation_id}}&app_id={{app_id}}&force_group=True'
    
    return pyshelle.ShelleClient(
        application_id,
        config['CLIENT_ID'],
        config['CLIENT_PASS'],
        config['CLIENT_SECRET'],
        endpoint='https://nprd-sbtst-shelleapimgmt.azure-api.net/backend',
        subscription_key=config['OCP_APIM_SUBSCRIPTION_KEY'],
        proxies={
            'http': 'zproxy-global.shell.com:80',
            'https': 'zproxy-global.shell.com:80'
        }
    )

def get_user_input():
    """
    Prompt the user to select an analysis option. 
    Keeps prompting until a valid option (1-4) is provided.
    """
    while True:
        try:
            user_input = int(input("Select an option:\n1. Trend Analysis\n2. Resource Utilization\n3. Performance Metrics\n4. Maintenance Optimization\nEnter the corresponding number (1-4): "))
            if 1 <= user_input <= 4:
                return user_input
            else:
                print("Invalid input. Please enter a number between 1 and 4.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def handle_response(response_message):
    """
    Extract and print the image URL and executive summary from the response message.
    """
    # Extract and print the image URL if available
    pattern = r'\(/TempImageProxy/[^)]+\)'
    match = re.search(pattern, response_message)
    if match:
        extracted_text = match.group(0)[1:-1]  # Remove the parentheses
        final_url = 'https://uat-shell-e-chat.shell.com/api' + extracted_text
        print(final_url)

    # Extract and print the executive summary if available
    summary_pattern = r'Executive summary\s*(.*)'
    summary_match = re.search(summary_pattern, response_message, re.DOTALL)
    if summary_match:
        executive_summary = summary_match.group(1).strip()
        print("Executive Summary:", executive_summary)

def main():
    application_id = 47
    prompt_mapping = {
        1: {
            "description": "From the uploaded file, analyse the file and do the following. Count the number of ‘72FP’ work orders over days to understand how often preventive maintenance activities are performed. Use Scheduled start column for start date.",
            "context": "By tracking the frequency of PM activities, organizations can optimize maintenance schedules, allocate resources efficiently, and ensure timely inspections and repairs. Also plot a graph of your analysis."
        },
        2: {
            "description": "From the uploaded file, compare columns 'planned Work' vs. 'Actual work' durations for all main work centers aggregating on the 'Operation WorkCenter' field."
        },
        3: {
            "description": "Calculate the average duration of work orders for all 'Functional Location' (from start to finish). 'Scheduled start' and 'Scheduled finish' fields could be used to calculate the planned duration to understand the typical time taken for maintenance activities. Also provide relevant graphs.",
            "context": "Measuring the average duration provides insights into efficiency and resource utilization. It helps set realistic expectations for work order completion times and informs scheduling decisions."
        },
        4: {
            "description": "Given the provided CSV file, your task is to perform the following steps:\nAsk the user for the Functional Location and an Operation WorkCenter.\nOnly use the following columns for further analysis: 'Order Type', 'Operation WorkCenter', 'Functional Location', 'Operation short text', 'Description', 'Total planned costs', 'Total actual costs', 'Scheduled finish', 'Scheduled start'.\nAnalyze the Operation short text and Description in all the orders for the provided Functional Location and Operation WorkCenter.\nSummarize your analysis. If there are no 72FP orders, summarize all the activities done in 72FC orders and also suggest the user to schedule PM if needed.\nBased on your analysis, provide a detailed explanation in natural language of what activities (found in Operation short text and Description) can be performed in the ‘72FP’ work orders to eliminate the need for ‘72FC’ work orders."
        }
    }

    # Load configuration and create Shelle client
    config_path = os.path.join(os.path.dirname(__file__), "run_configuration_uat.json")
    config = load_configuration(config_path)
    client = create_shelle_client(config, application_id)
    
    # Start a new conversation
    client.new_conversation()

    # Upload the file to Shelle
    client.upload_file(file_=r"C:\Users\Ramanathan.TRB\Desktop\Gen Ai\training\sukep 1 yr data.csv")

    # Set up prompt and overrides for the Shelle client
    overrides = {
        "prompt": "You are a seasoned engineer and data analyst tasked with analyzing maintenance work order data. Your goal is to provide insightful analyses based on the given CSV file, with a focus on optimizing maintenance schedules, understanding efficiency, and improving overall processes. For each analysis, you should always provide an executive summary that is concise and under 1000 words. Include graphs to visualize trends and key findings where applicable, but avoid unnecessary explanations or steps taken. Please ensure that the summary is focused and relevant to the specific prompts provided.",
        "top_p": 1,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "temperature": 0
    }
    
    # Initialize conversation history
    prompt_dict = []

    # Get the user's choice of analysis
    user_input = get_user_input()
    prompt = prompt_mapping.get(user_input, {"description": "Invalid input. No prompt available."})
    full_prompt = f"{prompt['description']} {prompt.get('context', '')}"
    prompt_dict.append({"role": "user", "content": full_prompt})

    message = ""
    while message.lower() != "quit":
        # Construct the prompt string from conversation history
        prompt_string = ' '.join(item['content'] for item in prompt_dict)
        
        # Get response from Shelle
        response = client.get_response(prompt=prompt_string, overrides=overrides, timeout=9999)
        
        # Print the response
        response_message = response.message
        print(f"Shell-e: {response_message}")

        # Handle response for image URLs and executive summaries
        handle_response(response_message)

        # Get user input for further questions
        message = input()
        if message.lower() != "quit":
            prompt_dict.append({"role": "user", "content": message})

if __name__ == "__main__":
    main()
