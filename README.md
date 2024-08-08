# PM Optimiser

## Project Description

**PM Optimiser** is a tool designed to analyze and optimize maintenance work order data, providing actionable insights and visualizations to enhance maintenance schedules, improve resource utilization, and support informed decision-making. The project includes two implementations:

1. **Terminal-Based Application**: A command-line tool for text-based interaction with maintenance data.
2. **Streamlit-Based Application**: A web-based interface for a more interactive and user-friendly experience.

Both implementations utilize the Shelle API to perform detailed analyses and generate valuable insights based on the provided maintenance data.

## Features

- **Trend Analysis**: Analyze the frequency of preventive maintenance activities.
- **Resource Utilization**: Compare planned versus actual work durations.
- **Performance Metrics**: Calculate average work order durations and visualize results.
- **Maintenance Optimization**: Analyze and summarize work orders, and suggest scheduling improvements.

## Terminal-Based Application

### Description

This Python script allows users to interact with maintenance work order data through a command-line interface. It provides various analysis options, uploads CSV files, and displays responses from the Shelle API.

### Requirements

- Python 3.12 or higher
- `pyshelle` library
- `json`, `os`, `sys`, `re` libraries (standard Python libraries)

### Usage

1. **Install Dependencies**: Ensure all required libraries are installed.

   pip install pyshelle
2. **Configuration**: Ensure the run_configuration_uat.json file is available with the appropriate configuration.
3. **Run the Scrip**t: Execute the script in your terminal.

   python terminal_app.py

4. **Follow Prompts**: Enter the required information as prompted by the script.
