import firebase_admin
from firebase_admin import credentials, storage
from google.cloud import firestore
import pandas as pd
import uuid
import os
import io
from pathlib import Path
import asyncio
import json
from datetime import datetime, timezone
from google.cloud import secretmanager




# Initialize Firebase app (if not already done)




class FirestoreStorage:
    def __init__(self, default_collection='original_json_transcription', default_bucket='toolstorage'):
        self.db = firestore.Client()
        self.test_dictionary = {'name': 'Jane Doe','email': 'janedoe@example.com','age': 28, "createdon": datetime.now()}
        self.default_collection = default_collection
        self.cred_dict = {}
        
        if not firebase_admin._apps:
            cred_json = self.access_secret_version("GOOGLE_FIREBASE_ADMIN_JSON_CREDENTIAL_TOOLSEXPLORATION")
            # Parse the JSON string into a dictionary
            self.cred_dict = json.loads(cred_json)
            # Pass the dictionary to the Firebase credentials.Certificate() method
            self.cred = credentials.Certificate(self.cred_dict)
            firebase_admin.initialize_app(self.cred, {'storageBucket': default_bucket})
        
        #Containers
        self.original_transcription_json = default_collection
        
        # Initialize Storage Bucket
        self.bucket = storage.bucket(default_bucket)
        
    
    def access_secret_version(self, secret_id, project_id='toolsexplorationfirebase',  version_id="latest"):
        secret_payload = ''
        try:
            # Create the Secret Manager client
            client = secretmanager.SecretManagerServiceClient()

            # Build the resource name of the secret version
            name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

            # Access the secret version
            response = client.access_secret_version(request={"name": name})

            # Decode the secret payload and return it
            secret_payload = response.payload.data.decode("UTF-8")
            
        except:
            secret_payload = os.environ.get(secret_id, '')
        
        return secret_payload
    
    async def get_multiple_secrets(self, secret_id_list, project_id='toolsexplorationfirebase',  version_id="latest"):
        secret_payload_dict = {}
        # Create the Secret Manager client
        client = secretmanager.SecretManagerServiceClient()

        for secret_id in secret_id_list:
            try:
        
                # Build the resource name of the secret version
                name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

                # Access the secret version
                response = client.access_secret_version(request={"name": name})

                # Decode the secret payload and return it
                secret_payload_value = response.payload.data.decode("UTF-8")
                secret_payload_dict[secret_id]= secret_payload_value
                
            except Exception as e:
                print(f'ERROR -- Secret ID not found in Secret Manager: {e}')
                continue
                
            
        return secret_payload_dict
    
    async def get_document_by_id(self, document_id, collection_name=None):
        """
        Retrieves a single document from Firestore using its document_id.
        """
        try:
            # If no collection_name is provided, use the default one
            if not collection_name:
                collection_name = self.default_collection

            # Reference the document using the collection and document_id
            doc_ref = self.db.collection(collection_name).document(document_id)
            doc = doc_ref.get()

            # Check if the document exists
            if doc.exists:
                return doc.to_dict()  # Return the document as a dictionary
            else:
                return None  # If document doesn't exist, return None
        except Exception as e:
            print(f"Error retrieving document {document_id}: {e}")
            return None


    async def get_best_document_id(self, data_dictionary, document_id):
        if document_id:
            return document_id
        if data_dictionary.get('document_id', None):
            return data_dictionary.get('document_id')
        if data_dictionary.get(document_id, None):
            return data_dictionary.get(document_id)
        if data_dictionary.get('id', None):
            return data_dictionary.get('id')
        return f"{uuid.uuid4()}"
    
    async def add_time_stamp_to_dictionary(self, data_dictionary):
        try: 
            if data_dictionary.get('created', None):    
                data_dictionary['modified'] = datetime.now()
                return data_dictionary
            else:
                data_dictionary['created'] = datetime.now()
                data_dictionary['modified'] = datetime.now()
                return data_dictionary
        except Exception as e:
            print(e)
            data_dictionary['errormessage'] = f"Could not add or updated timestamps: Error {e}"
            return data_dictionary
    
    async def insert_dictionary(self, collection_name=None, data_dictionary=None,  document_id=None):
        
        # Check if collection name is provided or use default one
        if not collection_name: collection_name = self.default_collection
        if not data_dictionary: data_dictionary = {}
        data_dictionary = await self.add_time_stamp_to_dictionary(data_dictionary)
        
        # Reference to the collection and document
        document_id = await self.get_best_document_id(data_dictionary, document_id)
        doc_ref = self.db.collection(collection_name).document(document_id)
        
        # Insert the document
        return doc_ref.set(data_dictionary)

    async def upsert_merge(self, document_id=None, collection_name=None, data_dictionary=None,  ):
        # Check if collection name is provided or use default one
        if not collection_name: collection_name = self.default_collection
        if not data_dictionary: data_dictionary = {}
        
        data_dictionary = await self.add_time_stamp_to_dictionary(data_dictionary)
        document_id = await self.get_best_document_id(data_dictionary, document_id)
        
        doc_ref = self.db.collection(collection_name).document(document_id)
        doc_ref.set( data_dictionary, merge=True) 
    
    def upsert_append_transcription(self, document_id, collection_name=None, new_transcriptions=[]):
        
        if not collection_name: collection_name = self.default_collection
        
        doc_ref = self.db.collection(collection_name).document(document_id)

        if not isinstance(new_transcriptions, list):
            new_transcriptions = [new_transcriptions]
        
        # Use arrayUnion to append the new transcription
        doc_ref.update({
            'transcriptions': firestore.ArrayUnion(new_transcriptions)
        })
    
    def get_transcription_records_sync(self):
        trans_dict = asyncio.run(self.get_transcription_records())
        trans_df = pd.DataFrame(trans_dict)
        trans_df.set_index('document_id', inplace=True)

        return trans_df
        
    async def get_transcription_records(self):

        # Check if collection name is provided or use default one

        # Query Firestore, ordered by 'timestamp' descending, limited to 'count'
        query = self.db.collection(self.original_transcription_json).order_by('created', direction=firestore.Query.DESCENDING)

       # Get the query result asynchronously
        results = query.stream()

        # Gather the dictionaries from the query result
        documents = []
        for doc in results:  # Directly iterate over the StreamGenerator
            documents.append(doc.to_dict())

        return documents
    
    async def upload_image_from_object(self, image_object, destination_blob_name):

        # Convert the image object to bytes (e.g., PNG or JPEG format)
        img_byte_arr = io.BytesIO()
        image_object.save(img_byte_arr, format='PNG')  # You can also use 'JPEG', etc.
        img_byte_arr = img_byte_arr.getvalue()

        # Upload the image bytes to Firebase Storage
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_string(img_byte_arr, content_type='image/png')  # Adjust the content_type as needed

        # Return the public URL or the storage path
        return blob.public_url
    
    async def upload_file(self, file_path, destination_blob_name=None):

        if not destination_blob_name:
            destination_blob_name = f"{uuid.uuid4()}"
        
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_filename(file_path)


        print(f"File {file_path} uploaded to {destination_blob_name}.")


        return blob.public_url  # Get the public download URL
    
    async def upload_folder_of_json_files_to_cloud_storage(self, folder_path, container=None):
        # Confirm that the folder path is a valid path
        if not os.path.isdir(folder_path):
            raise ValueError("Invalid folder path provided.")
        
        # Check if a container is provided; if not, use a default one.
        if not container:
            container = self.default_collection
        
        # Iterate through all the files in the folder
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            # Skip files that don't end in .json, or begin with a dot (.) or are directories.
            if filename.endswith('.json') and not filename.startswith('.') and os.path.isfile(file_path):
                
                # Read the JSON file to dictionary
                with open(file_path, 'r') as file:
                    try:
                        data_dictionary = json.load(file)
                    except json.JSONDecodeError as e:
                        print(f"033[1;33mSkipping file {filename} due to JSON decode error: {e}")
                        continue

                # Generate document ID based on the filename (excluding .json extension)
                document_id = data_dictionary.get('metadata', {}).get('request_id','') 

                
                if not document_id or document_id.strip() =='':
                    print(f"\033[1;91mSkipping file {filename} due to missing document ID.f\033[0m")
                    continue
                # collec other metadata
                created_on_str = data_dictionary.get('metadata', {}).get('created','')                
                created_on= datetime.strptime(created_on_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                created_on = created_on.replace(tzinfo=timezone.utc)
                duration = data_dictionary.get('metadata',{}).get('duration','')            
                name= document_id
                summary = document_id

                topics = []
                # ['results']['topics']['segments'][0]['topics'][0]['topic']
                for segment in data_dictionary['results']['topics']['segments']:
                    for topic in segment['topics']:
                        topics.append(topic.get('topic', ''))
                topics = list(set(topics))
                
                # Optionally, upload the JSON file to Storage with the filename as the destination blob name.
                public_url =  await self.upload_file(file_path, destination_blob_name=f"{container}/{document_id}.json")

                transcription_record = {
                    'document_id': document_id,
                    "name": name,
                    "summary": summary,
                    'created': created_on,
                    'duration': int(duration),
                    'transcription_raw': f'gs://toolstorage/{container}/{document_id}.json',
                    'public_url': public_url,
                    'topics': topics,
                    'speaker_names': {'1': 'Speaker 1',
                                    '2': 'Speaker 2',
                                    '3': 'Speaker 3',
                                    '4': 'Speaker 4',
                                    '5': 'Speaker 5'
                                    }
                    
                    }
                 # # Use the existing method to upsert each JSON dictionary into Firestore.
                await self.upsert_merge(document_id, container, transcription_record)
                
                
        print(f"Finished uploading files from {folder_path} to Firestore Cloud Storage.")
        return None

    async def get_full_transcription(self, document_id, container=None):
        tasks = []
        if not container: container = self.default_collection
        
        tasks.append(asyncio.create_task(self.get_document_by_id(document_id)))
        tasks.append(asyncio.create_task(self.get_json_from_blob(f"{container}/{document_id}.json")))
        
        results = await asyncio.gather(*tasks)
        return results
    
    async def get_json_from_blob(self, file_path):
        """
        Retrieves a JSON object from a blob in Firebase Storage.
        
        Args:
            file_path (str): The path of the file in Firebase Storage.
        
        Returns:
            dict: The parsed JSON data as a dictionary.
        """
        try:
            # Retrieve the blob
            blob = await self.get_blob(file_path)
            
            if blob:
                # Download the blob's contents as a string
                blob_content = blob.download_as_string()

                # Parse the string into JSON (dictionary)
                json_data = json.loads(blob_content)

                return json_data
            
            else:
                print(f"Blob {file_path} could not be found.")
                return None

        except Exception as e:
            print(f"Error retrieving or parsing JSON from blob: {e}")
            return None
    
    async def get_blob(self, file_path):
            """
            Retrieves a blob (file) from Firebase Storage given the full file path.
            
            Args:
                file_path (str): The path of the file in Firebase Storage (relative to the bucket root).
            
            Returns:
                blob: A blob object from Firebase Storage.
            """
            try:
                # Create a reference to the blob using the file path
                blob = self.bucket.blob(file_path)
                
                # Check if the blob exists
                if blob.exists():
                    print(f"Blob {file_path} found.")
                    return blob
                else:
                    print(f"Blob {file_path} does not exist.")
                    return None
            
            except Exception as e:
                print(f"Error retrieving blob: {e}")
                return None

    async def download_blob(self, file_path, destination_file_name):
        """
        Downloads a blob from Firebase Storage to a local file.
        
        Args:
            file_path (str): The path of the file in Firebase Storage.
            destination_file_name (str): The local path where the file will be downloaded.
        """
        try:
            # Retrieve the blob using the file path
            blob = self.get_blob(file_path)
            
            if blob:
                # Download the blob to the local destination file
                blob.download_to_filename(destination_file_name)
                print(f"Blob {file_path} downloaded to {destination_file_name}.")
            else:
                print(f"Blob {file_path} could not be found or downloaded.")
        
        except Exception as e:
            print(f"Error downloading blob: {e}")

    async def update_local_secret_file(self):
        env_variable_dict = await self.get_document_by_id('variable_key_list', 'settings')
        env_variable_list = env_variable_dict.get('names', [])
        list_of_secret_dicts = await self.get_multiple_secrets(env_variable_list)
        home_directory_str = str(Path.home())
        secrets_file_path = f"{home_directory_str}/.config/secrets.sh"    

        with open(secrets_file_path, 'w') as file:
            file.write("#!/bin/bash")
            for env_variable in list_of_secret_dicts.keys():
                file.write(f'\n\nexport {env_variable}="{list_of_secret_dicts.get(env_variable, '')}" \n\n#______________________________________________________________________')
        
        
        
if __name__ == "__main__":
    pass
    # fire = FirestoreStorage()
    # asyncio.run(fire.update_local_secret_file())
    
    # transcription_name = f"{uuid.uuid4()}"
    
    # await fire.upload_folder_of_json_files_to_cloud_storage("/Users/michasmi/Library/Mobile Documents/iCloud~md~obsidian/Documents/Notes By Michael/Transcriptions/.trans_json", fire.original_transcription_json)
        
    # for i in range(insert_count):
    #     new_transcriptions = [f"{uuid.uuid4()}",f"{uuid.uuid4()}",f"{uuid.uuid4()}",f"{uuid.uuid4()}"]
    #     response = fire.upsert_append_transcription(transcription_name, 'test_transcriptions', new_transcriptions=new_transcriptions)
    #     print(response)
    
    # for i in range(insert_count):
    #     response = fire.insert_dictionary(fire.default_collection, fire.test_dictionary, None)
    #     print(response)
        
        
    # print(await fire.get_recent_dictionaries(fire.default_collection, 15))
         


# asyncio.run(test_class(3))