from openai import OpenAI
client = OpenAI()
import json

import pandas as pd
import time

input_csv = '/Users/michasmi/Downloads/input_file.csv'
output_csv = '/Users/michasmi/Downloads/output_file.csv'

def transform_field_name(field_name, table_name, definition):
    try:
        json_format = '{camel_case_field_name: "<The camel case field name you create>"}'
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Updated from 'engine' to 'model' if using a newer OpenAI client version
            # response_format={ "type": "json_object" },
            max_tokens=60,
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output json."},
                {"role": "user", "content": f"Transform the uppercase field name '{field_name}' into a camel case format with spaces based on its table name '{table_name}' and business definition: '{definition}. Reply only in this JSON format: {json_format} . Do not add any additional text. Your response will be systematically interpreted."}
            ]
            )

        transformed_name_json = response.choices[0].message.content
        transformed_name = json.loads(transformed_name_json).get('camel_case_field_name', '')
        print(transformed_name)
    except Exception as e:
        print(f"An error occu.crred: {e}")
        transformed_name = ""  # Use an empty string or some indication of failure
    return transformed_name

def process_csv(input_csv, output_csv):
    # Load the data
    data = pd.read_csv(input_csv)

    # Prepare a list to store the transformed names
    transformed_names = []

    # Iterate over each row in the DataFrame
    for index, row in data.iterrows():
        # Transform the field name
        transformed_name = transform_field_name(row.get('FIELD', ''),   row.get('TABLE', ''), row.get('DEFINITION', ''))
        transformed_names.append(transformed_name)

        # Wait for a specified amount of time (e.g., 1 second) to avoid hitting API rate limits
        time.sleep(1/50)  # Adjust the sleep time as needed

    # Assign the transformed names back to the DataFrame
    data['Camel Case Field Name'] = transformed_names

    # Save the transformed data to a new CSV
    data.to_csv(output_csv, index=False)



# Processing the CSV
process_csv(input_csv, output_csv)

print("Transformation complete. Results saved to:", output_csv)
