import json
import os
import pyshelle
import re
import streamlit as st
import logging

# Set up logging to print to the terminal
logging.basicConfig(level=logging.DEBUG)

def load_configuration(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading configuration: {e}")
        st.stop()

def create_shelle_client(config, application_id):
    pyshelle.client.ENDPOINTS['temp_file'] = '/chat/temp_file?conversation_id={{conversation_id}}&app_id={{app_id}}&force_group=True'
    
    try:
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
    except Exception as e:
        st.error(f"Error creating ShelleClient: {e}")
        st.stop()

def truncate_history(history, max_tokens=2000):
    """Truncate history to ensure it fits within token limits."""
    total_tokens = sum(len(item['content'].split()) for item in history)
    while total_tokens > max_tokens and history:
        history.pop(0)
        total_tokens = sum(len(item['content'].split()) for item in history)
    return history

def get_response_from_shelle(client, prompt_string, overrides, history):
    """Function to get response from Shelle and update the conversation history."""
    response = client.get_response(prompt=prompt_string, overrides=overrides, timeout=9999)
    st.write(f"**Shell-e Response:** {response.message}")
    logging.debug(f"Response: {response.message}")

    intermediate_response = response.message
    
    # Extract image URL if any
    pattern = r'\(/TempImageProxy/[^)]+\)'
    match = re.search(pattern, intermediate_response)
    if match:
        extracted_text = match.group(0)[1:-1]  # Remove the parentheses
        final_url = 'https://uat-shell-e-chat.shell.com/api' + extracted_text
        st.write(f"Image URL: {final_url}")

    # Extract executive summary
    summary_pattern = r'Executive summary\s*(.*)'
    summary_match = re.search(summary_pattern, intermediate_response, re.DOTALL)
    if summary_match:
        executive_summary = summary_match.group(1).strip()
        st.write("**Executive Summary:**", executive_summary)

    # Update conversation history
    history.append({"role": "assistant", "content": response.message})
    
    return history

def main():
    st.title("PM Optimizer")

    application_id = 47
    prompt_mapping = {
    1: {
        "description": """From the uploaded file, analyze the data and do the following:
        Count the number of ‘72FP’ work orders over days using the 'Scheduled start' column to understand the frequency of preventive maintenance activities.
        Present the analysis with a line graph showing the trend of PM activities over time (daily or weekly).",
        "context": "Tracking the frequency of 72FP work orders helps in optimizing maintenance schedules, ensuring timely inspections, and improving resource allocation. The line graph will help visualize patterns and irregularities in preventive maintenance scheduling."""
    },
    2: {
        "description": """From the uploaded file, compare the 'planned Work' and 'Actual work' durations for each 'Operation WorkCenter', aggregating the data based on the 'Operation WorkCenter' field.
        Calculate the percentage difference between planned and actual work durations for each work center. Additionally, provide a bar chart comparing these durations across all work centers to highlight any discrepancies or inefficiencies."""
    },
    3: {
        "description": """Calculate the average duration of work orders across all 'Functional Location' fields, using the 'Scheduled start' and 'Scheduled finish' columns to calculate the duration.
        Present the results with a histogram (bin size of 10) showing the distribution of work order durations and a box plot excluding outliers to highlight the typical duration of maintenance activities.",
        "context": "Understanding the average duration of work orders provides insights into operational efficiency and resource utilization, allowing for better planning and scheduling of maintenance tasks."""
    },
    4: {
        "description": """Given the provided CSV file, perform the following steps:
        Ask the user for a specific 'Functional Location' and an 'Operation WorkCenter'.
        Analyze the 'Operation short text' and 'Description' fields in all the work orders corresponding to the provided Functional Location and Operation WorkCenter.
        Summarize your findings with a brief overview of the most common activities and patterns observed. 
        If no 72FP work orders are found, summarize the activities for 72FC work orders and suggest scheduling preventive maintenance if frequent corrective actions are detected or preventive measures seem necessary."""
    }
}

    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), "run_configuration_uat.json")
    config = load_configuration(config_path)

    # Initialize ShelleClient and store in session state
    if 'client' not in st.session_state:
        st.session_state.client = create_shelle_client(config, application_id)
        logging.debug("Initialized ShelleClient and stored in session state.")

    # Initialize session state variables
    if 'prompt_dict' not in st.session_state:
        st.session_state.prompt_dict = []
        logging.debug("Initialized prompt_dict in session state.")

    if 'conversation_started' not in st.session_state:
        st.session_state.conversation_started = False
        logging.debug("Initialized conversation_started flag in session state.")

    if 'overrides' not in st.session_state:
        st.session_state.overrides = {
            "top_p": 1,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "temperature": 0
        }
        logging.debug("Initialized overrides in session state.")

    # File input and option selection
    file_path = st.text_input("Enter the full file path of the CSV file:")
    user_input = st.selectbox(
        "Select an option",
        [1, 2, 3, 4],
        format_func=lambda x: {
            1: "Trend Analysis",
            2: "Resource Utilization",
            3: "Performance Metrics",
            4: "Maintenance Optimization"
        }.get(x)
    )

    if st.button("Start Analysis") and file_path:
        if not st.session_state.conversation_started:
            # Start a new conversation with Shelle
            st.session_state.client.new_conversation()
            st.session_state.conversation_started = True
            logging.debug("Started new conversation.")

            # Upload the file to Shelle
            try:
                st.session_state.client.upload_file(file_=file_path)
                logging.debug(f"Uploaded file: {file_path}")
            except Exception as e:
                st.error(f"Error uploading file: {e}")
                logging.error(f"Error uploading file: {e}")
                st.stop()

            # Generate the initial prompt
            prompt = prompt_mapping.get(user_input, {"description": "Invalid input. No prompt available."})
            initial_prompt = f"You are a seasoned engineer and data analyst tasked with analyzing maintenance work order data. Your goal is to provide insightful analyses based on the given CSV file, with a focus on optimizing maintenance schedules, understanding efficiency, and improving overall processes. For each analysis, you should always provide an executive summary that is concise and under 1000 words. Include graphs to visualize trends and key findings where applicable, but avoid unnecessary explanations or steps taken. Please ensure that the summary is focused and relevant to the specific prompts provided. {prompt['description']} {prompt.get('context', '')}"

            st.session_state.prompt_dict.append({"role": "user", "content": initial_prompt})
            logging.debug(f"Initial prompt added to prompt_dict: {initial_prompt}")

            # Get the initial response from Shelle
            st.session_state.prompt_dict = get_response_from_shelle(
                st.session_state.client,
                initial_prompt,
                st.session_state.overrides,
                st.session_state.prompt_dict
            )

    # Display the text area for user queries
    user_message = st.text_area("Please enter your query:")

    if st.button("Send") and user_message:
        if not st.session_state.conversation_started:
            st.error("Please start an analysis first by uploading a file and pressing 'Start Analysis'.")
            logging.error("Attempted to send message without starting a conversation.")
        else:
            # Add the user's message to the conversation history
            st.session_state.prompt_dict.append({"role": "user", "content": user_message})
            logging.debug(f"User message added to prompt_dict: {user_message}")

            # Truncate history to manage token limits
            truncated_history = truncate_history(st.session_state.prompt_dict)
            prompt_string = ' '.join([item['content'] for item in truncated_history])

            # Debug output
            logging.debug(f"Prompt String: {prompt_string}")

            # Get the response from Shelle with conversation history
            st.session_state.prompt_dict = get_response_from_shelle(
                st.session_state.client,
                prompt_string,
                st.session_state.overrides,
                st.session_state.prompt_dict
            )

if __name__ == "__main__":
    main()
