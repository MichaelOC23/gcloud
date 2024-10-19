import os
import pandas as pd
import uuid
import psycopg2
# print("Loaded NoteLog Imports")



class NoteLog:
    def __init__(self, start_folder_path=None, schema='notes', likely_key_names=None, table_prefix='', column_prefix='c'):
        self.connection_str = os.environ.get('POSTGRES_AWS_PRODUCT_DB_CONN_STRING')
        self.schema = schema
        self.notes_table_name = 'notelog'
        self.notes_item_table_name = 'notelogitem'
        self.likely_key_names = likely_key_names or []
        self.table_prefix = table_prefix
        self.column_prefix = column_prefix
        # self._create_schema()
        # self._create_table()

    def connect(self):
        return psycopg2.connect(self.connection_str)
    
    def _create_schema(self):
        with self.connect() as conn:
            with conn.cursor() as cursor:
                try:
                    sql = f'CREATE SCHEMA IF NOT EXISTS {self.schema}'
                    cursor.execute(sql)
                    conn.commit()
                except Exception as e:
                    print(f"Error creating schema {self.schema}: {e}")
    
    def _create_table(self):
        self._create_schema()
        create_query = f'''
            -- Create the notes.notelog table
            CREATE TABLE IF NOT EXISTS notes.notelog (
                id uuid DEFAULT uuid_generate_v4() NOT NULL,
                note_key text NOT NULL,
                createdon timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                modifiedon timestamp NULL,
                note_name text NULL,
                note_path text NULL,
                json_data _jsonb NULL,
                word_history _jsonb NULL,
                statement_history _jsonb NULL,
                note text NULL,
                summary text NULL,
                speaker text NULL,
                utterance text NULL,
                record_type text NULL
            );

            -- Create a function to update the modifiedon column before update
            CREATE OR REPLACE FUNCTION update_modifiedon_column()
            RETURNS TRIGGER AS $$
            BEGIN
            NEW.modifiedon = CURRENT_TIMESTAMP;
            RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            -- Create a trigger to automatically update modifiedon on row update
            CREATE TRIGGER set_modifiedon
            BEFORE UPDATE ON notes.notelog
            FOR EACH ROW
            EXECUTE FUNCTION update_modifiedon_column();
            '''
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(create_query)
                conn.commit()
            
    def fetch_note_list(self, filters=None):
        filters = filters or {}
        where_clause = ""
        params = []
        if filters:
            conditions = []
            for i, (key, value) in enumerate(filters.items()):
                conditions.append(f"{key} = %s")
                params.append(value)
            where_clause = f"WHERE {' AND '.join(conditions)}"

        query = f"SELECT * FROM {self.schema}.{self.notes_table_name} {where_clause};"
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                colnames = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=colnames)
        return df

    def fetch_note_body(self, id=None, key=None):
        if not id and not key:
            return pd.DataFrame()
        try:
            params = []
            if id is not None:
                sql = f"SELECT * FROM {self.schema}.{self.notes_table_name} WHERE id = %s;"
                params.append(id)
            elif key is not None:
                sql = f"SELECT * FROM {self.schema}.{self.notes_table_name} WHERE key = %s;"
                params.append(key)
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    rows = cursor.fetchall()
                    if not rows:
                        return pd.DataFrame()
                    colnames = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=colnames)
            return df
        except Exception as e:
            print(f"Error during SQL query execution: {e}")
            return pd.DataFrame()
     
    def insert_utterance(self, note_key, speaker = '', utterance = ''):
        with self.connect() as conn:
            with conn.cursor() as cursor:
                sql = ''
                sql+= f"INSERT INTO notes.notelog " 
                sql+= f" (note_key, speaker, utterance, record_type ) " # (key, createdon, name, path, json_data, word_history, statement_history, note, summary)
                sql+=  f"VALUES (%s, %s, %s, %s)" 
                cursor.execute(sql, (note_key, speaker, utterance, 'utterance'))
                conn.commit()
                return True
    
    def insert_note(self, note_key):
        with self.connect() as conn:
            with conn.cursor() as cursor:
                sql = ''
                sql+= f"INSERT INTO notes.notelog " 
                sql+= f" (note_key, record_type ) " 
                sql+=  f"VALUES (%s, %s)" 
                cursor.execute(sql, (note_key, 'note'))
                conn.commit()
                return True

# print("Loaded NoteLog Module")
if __name__ == "__main__":
    pass
    note = NoteLog()
    note_id = f"{uuid.uuid4()}"
    note.insert_note(note_id)
    note.insert_utterance(note_id, "speaker1", "utterance1")
