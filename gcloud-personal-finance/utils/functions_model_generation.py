import json
model_file_path = "utils/models.json"

def get_model_entity_definition(model_name, table_name=None):
    try:
        with open(model_file_path) as json_file:
            models = json.load(json_file)
        
        entities = models['models'][model_name]['entities']
        if table_name:
            return entities[table_name]['attributes']
        else:
            return entities
    except Exception as e:
        print(f"Error in get_model_definition. Value of modelname/tablename is: {model_name}/{table_name} \n Error below:")
        print(e)
        return False

def generate_model_for_database(models_file_path, model_name, database):
    # Read the model file
    with open(models_file_path) as json_file:
        models = json.load(json_file)

    entities = models['models'][model_name]['entities']
    field_types = models['databasedefinitions'][database]['fieldtypes']
    default_fields = models['databasedefinitions'][database]['defaultfields']
    
    create_table_statements = generate_create_table_statements(entities, field_types, default_fields)

    return create_table_statements
    
def generate_create_table_statements(entities, field_types, default_fields):

    # Initialize an empty list to store CREATE TABLE statements
    create_table_statements = []

    # Iterate through each entity in the JSON input
    for entity_name, entity_info in entities.items():
        entity_attributes_list = entity_info['attributes']

        # Create a list to store the field definitions for the CREATE TABLE statement
        field_definitions = []

        # Add the default fields to the field definitions
        for key, value in default_fields.items():
            field_definitions.append(f"{key} {value}")

        # Iterate through the attributes of the entity and generate field definitions
        for attribute in entity_attributes_list:
            for attr_name, attr_value in attribute.items():
                field_type = field_types.get(attr_name[:3], 'TEXT')
                field_definitions.append(f"{attr_name} {field_type}")

        # Create the CREATE TABLE statement for the entity
        create_table_sql = f"CREATE TABLE {entity_name} ({', '.join(field_definitions)});"

        # Add the statement to the list
        create_table_statements.append(create_table_sql)

    return create_table_statements

if __name__ == '__main__':
    create_table_statements = generate_model_for_database(model_file_path, 'personal-finance', 'postgresql')
    print(create_table_statements)