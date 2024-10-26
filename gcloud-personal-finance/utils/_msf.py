#Standard Imports
import json
import os
import shutil
import requests
import sys
from openai import OpenAI
import csv
from datetime import datetime




def WriteOut(LogTitle, TextToWrite, FilePath):
  try:
    with open(FilePath, 'a') as f:
      current_time = datetime.now()
      milliseconds = current_time.microsecond // 1000
      end_time = current_time.strftime("%Y-%m-%d %H:%M:%S") + f":{milliseconds}ms"
      
      if TextToWrite:
        if isinstance(TextToWrite, str):
          f.write(os.linesep+os.linesep + LogTitle + ": " + end_time + os.linesep + TextToWrite + os.linesep)
        elif isinstance(TextToWrite, dict):
          json_string = json.dumps(TextToWrite, indent=4)
          f.write(os.linesep+os.linesep + LogTitle + ": " + end_time + os.linesep + json_string + os.linesep)
        else:
          f.write(os.linesep + LogTitle + ": " + end_time + os.linesep + str(TextToWrite) + os.linesep)
      else:
          f.write(os.linesep + LogTitle + ": " + end_time + os.linesep)
    
      f.flush()
      f.close()

  except Exception as e:
    ErrMessage = 'Error writing to log with LogTitle: ' + LogTitle + "Error: " + os.linesep + str(e)
    print(ErrMessage)

def WriteOutJSON(JsonToWrite, FilePath, log_file):
  try:
    #Get the current date/time
    current_time = datetime.now()
    milliseconds = current_time.microsecond // 1000
    end_time = current_time.strftime("%Y-%m-%d %H:%M:%S") + f":{milliseconds}ms"
    
    # JsonToWrite is a list of dicts (have to transform it)
    json_data = json.dumps(JsonToWrite, indent=4)

    # Write out json_data string to file
    with open(FilePath, 'w') as f:  
      f.write(json_data)
      f.flush()
      f.close()
    LogMessage = 'Successfully exported JSON' + ' for ' + FilePath + ' at ' + end_time
    WriteOut(LogMessage, '', log_file)
    print(LogMessage)
    return  json_data
      
  except Exception as e:
    print("Error Exporting JSON: ", e)
    
def CreateFolderIfNotExist(folder):
  #get workling fileDirectory of this script
  current_dir = os.path.dirname(os.path.abspath(__file__))
  ConfigFileFolderPath = os.path.join(current_dir, folder, '')
  
  # Create parent directories if they don't exist
  if not os.path.exists(ConfigFileFolderPath):
    os.makedirs(ConfigFileFolderPath)
    print ('Created fileDirectory (it did not exist)' + folder)
  return ConfigFileFolderPath

def CreateFileAndFolderPath(FilePath, FlaskRunId=None, log_file=None):
  
  # Create parent directories if needed
  fileDirectory = os.path.dirname(FilePath)
  fileName = os.path.basename(FilePath)
  archiveDirectory = os.path.join(fileDirectory, 'Archive')
  fileType = os.path.splitext(FilePath)[1]
  fileNameNoExtension = os.path.splitext(fileName)[0]
  
  if FlaskRunId == None or FlaskRunId == '':
    flaskRunId = ''
  else:
    flaskRunId = f'_{FlaskRunId}'
  
  completeFilePath = os.path.join(fileDirectory, f'{fileNameNoExtension}{flaskRunId}{fileType}')
  
  
      
  # Create parent directories if they don't exist 
  if not os.path.exists(fileDirectory) and fileDirectory != '':
    os.makedirs(fileDirectory)
    if log_file:
      WriteOut('Created fileDirectory (it did not exist)', fileDirectory, log_file)
  
  # Create archive directories if they don't exist 
  if not os.path.exists(archiveDirectory):
    os.makedirs(archiveDirectory)
    if log_file:
      WriteOut('Created archiveDirectory (it did not exist)', archiveDirectory, log_file)
  
  #Archive prior files for Flask ID (run based) files (i.e. all files except the config file)
  if flaskRunId == '':
    if os.path.exists(fileDirectory):
      #Archive prior log file(s)  
      priorLogFiles = os.listdir(fileDirectory)
      for f in priorLogFiles:
        #If the filename begins with fileName and ends with fileType, then move it to the archive folder
        if f.startswith(fileName) and f.endswith(fileType):
          shutil.move(os.path.join(fileDirectory, f), os.path.join(archiveDirectory, f))
        if log_file:
          WriteOut('Moved prior file to archive', f, log_file)
    # Create the new log file if it doesn't exist
    if not os.path.exists(completeFilePath):
      open(completeFilePath, 'w').close()
      #print(f'Created new file at {FilePath}')
      if log_file:
        WriteOut('Created File (it did not exist)', FilePath, log_file)
  else:
    print(f'Skipping archive of file {fileName}.')
    
  return completeFilePath

def EmptyIfNull(ListItem, Field1, Field2):
  try:
    if Field2 == '':
      ValRet = ListItem[Field1]
    else:
      ValRet = ListItem[Field1][Field2]
    return ValRet
  except:
    return ''  

def NegativeOneIfNull(ListItem, Field1, Field2):
  try:
    ValRet = ListItem[Field1][Field2]
    return ValRet
  except:
    return -1   

def getAccessToken(appConfig, code):
  try: #Get the AccessToken and make a valid App Config file
    
    #Use the new code if the old one is invaild or missing
    if appConfig['isValid'] == 'False': #This means that it is the default appConfig
      WriteOut ("Current appConfig is invaild or defualt; Attempting to get a new AccessToken using the code;", "", appConfig['LogFilePath'])
      appConfig['TokenData'][0]['code'] = code
      
      #Get the token response
      tokenResponse = requests.post(appConfig['TokenEndpoint'], data=appConfig['TokenData'][0])  
    
      #Transform the token response to JSON
      accessToken = tokenResponse.json()['access_token']
    
      #Save the new access token to the appConfig dictionary
      appConfig['AccessToken'] = accessToken
      
      #delete the code from the appConfig file
      deprecateConfigFile(appConfig)
      
      #Append all the Site and List IDs to the new appConfig
      appConfig = getAllSPSiteAndListIDs(appConfig)
      
      #Create a new appConfig file
      appConfigCheck = saveNewAppConfigFile(appConfig)
      
      if appConfigCheck['isValid'] == 'True':
        appConfig = appConfigCheck['appConfig']
        appConfig['isValid'] = 'True'
        return appConfig
      else:
        WriteOut("Error creating a new appConfig file", "", appConfig['LogFilePath'])
        appConfig['isValid'] = 'False'
        sys.exit()
    else:   
      #USe the current Access Token to update the appConfig with all Current Sites and Lists (Ids)
      appConfig = getAllSPSiteAndListIDs(appConfig)
      if appConfig['isValid'] == 'True':
        return appConfig
      else:
        WriteOut ("Current appConfig is invaild or defualt; Attempting to get a new AccessToken using the code;", "", appConfig['LogFilePath'])
        appConfig['isValid'] = 'False'
        getAccessToken(appConfig, code)
        if appConfig['isValid'] == 'True':
          return appConfig
        else:
          print("The Current AccessToken and Code are both invaild. Cannot proceed")
          sys.exit()
            
  except Exception as e:
    WriteOut("Error getting the accessToken ", str(e), appConfig['LogFilePath'])
    deprecateConfigFile(appConfig)  
    appConfig['isValid'] = 'False'
    
def connectToSharePoint(appConfig, FlaskRunId, code):
  
  # Get auth code received from Microsoft
  appConfig = getAccessToken(appConfig, code)


  if appConfig == None:
    appConfig = getAppConfig(FlaskRunId)
    appConfig = getAccessToken(appConfig, code)
  
  if appConfig['isValid'] == 'False':
    print("The Current AccessToken and Code are both invaild. Cannot proceed")
    print("Cannot Connect to SharePoint. Exiting")
    sys.exit()
  else:
    return appConfig
  
def getAllSPSiteAndListIDs(appConfig):
  print("Getting all sites and lists")
  # ### Get the names and ids of all of the sharepoint 'sites' and print them out to the log file
  graphEndpoint = appConfig['GraphEndpoint']
  accessToken = appConfig['AccessToken']
  siteResponse = requests.get(f'{graphEndpoint}/sites?search=Product', 
                              headers={'Authorization': 'Bearer ' + accessToken})
  
  WriteOut("AllSites Response: ", siteResponse, appConfig['LogFilePath'])
  
  #Attempt to extract the JSON portion of the site_response
  try: 
    sites = siteResponse.json()['value']
  
    siteListDictionary ={
      "SiteName": " ",
      "SiteId": " ",
      "ListName": " ",
      "ListId": " "
    }
    
    siteDictionary = {
      "SiteName": " ",
      "SiteId": " "
    }
    
    #Iterate through the JSON for each site and print the name of the site and the id of the site the the OCSPfunc.Writeout log file
    for site in sites:  
      #The siteId variable is used in the SHAREPOINT_ENDPOINT variable. 
      #It is the middle value of three comma separated values which constitute the site['id'] value.
      #Assign the middle value of the site['id'] value to the siteId variable
      siteDictionary = {}
      siteId = site['id'].split(',')[1]
      siteName = site['name']
      
      siteDictionary = {
        "SiteId": siteId,
        "SiteName": siteName
      }
      appConfig['SiteIds'].append(siteDictionary)
      
        
      #Get all the lists for this site
      listResponse = requests.get(f'{graphEndpoint}/sites/{siteId}/lists',
                                  headers={'Authorization': 'Bearer ' + accessToken})
      try:
        lists = listResponse.json()['value']
      
      except Exception as e:
        lists = []
        WriteOut("Error getting the 'Lists' Value from the JSON: ", listResponse.json())
        print(e)
        
      
      for list in lists:
        siteListDictionary = {}
        siteListDictionary = {
          'SiteName': siteName,
          'SiteId': siteId,
          'ListName': list['name'],
          'ListId': list['id']
                  
        }
        appConfig['ListIds'].append(siteListDictionary)
    
    appConfig['isValid'] = 'True'
  
  except Exception as e:
    errMessage = 'Error getting the Sites or Lists Value from the JSON: ' + str(e) + os.linesep + str(siteResponse)
    WriteOut("Can't process All Sites JSON", errMessage, appConfig['LogFilePath'])
    deprecateConfigFile(appConfig)
    print(errMessage)
    appConfig['isValid'] = 'False'
    #sys.exit() # no point in proceeding if there was an error  
  return appConfig

def deprecateConfigFile(appConfig):
  if os.path.exists(appConfig['ConfigPath']):
    shutil.copy2(appConfig['ConfigPath'], appConfig['ConfigPath'].replace('.config', f'_archive_{datetime.now().strftime("%Y%m%d_%H%M%S")}.config'))
    os.remove(appConfig['ConfigPath'])
  return appConfig
  
def saveNewAppConfigFile(appConfig):
  appConfigCheck = {
    'isValid': 'False',
    'appConfig': []
  }
  try: 
    #Create a new Config File
    with open(appConfig['ConfigPath'], "w") as f:
      json.dump(appConfig, f, indent=4)
    appConfigCheck['isValid'] = 'True'
    appConfigCheck['appConfig'] = appConfig   
    
    #Copy to static folder for use in the web app
    CreateFolderIfNotExist('static')  #Validate / fix / create folder structure if needed 
    
    #Rename the file to Connection.json
    ConfigJSONpath  = appConfig['ConfigPath'].replace('.config', '.json')
    #Change the folder to static
    ConfigJSONpath  = ConfigJSONpath.replace('Config/', 'static/')
    
    #Copy to static folder for use in the web app
    shutil.copy2(appConfig['ConfigPath'], ConfigJSONpath)
    
    
    return appConfigCheck
  except Exception as e:
    WriteOut("Error writing appConfig to Config File", str(e), appConfig['LogFilePath'])
    return appConfigCheck  

def createDefaultAppConfig (appPaths, FlaskRunId):
  
  
  #Establish the default values from the config file 
  
  clientId = ""
  clientSecret = ""
  graphEndpoint = "https://graph.microsoft.com/v1.0"
  tenantId = ""
  siteURL = "https://outercircles.sharepoint.com/"
  graphEndpoint = "https://graph.microsoft.com/v1.0"
  authEndpoint = f"https://login.microsoftonline.com/{tenantId}/oauth2/v2.0/authorize"
  tokenEndpoint = f"https://login.microsoftonline.com/{tenantId}/oauth2/v2.0/token"
  authURL = f"{authEndpoint}?client_id={clientId}&response_type=code&redirect_uri=http://localhost:5000/redirect&response_mode=query&scope=offline_access%20https%3A%2F%2Fgraph.microsoft.com%2F.default"
  getAllSitesEndpoint = f"{graphEndpoint}/sites?search=Product"
  chatGPTAPIKey = ""
  promptFilePath = appPaths['PromptResponseFilePath']
  flaskRunId = FlaskRunId
  
  
  #Create the default Dictionary Instance and write it to the config file
  appConfig = {
    'isValid': "False",
    "ConfigPath": appPaths["ConfigFilePath"],
    "ClientId": clientId,
    "ClientSecret": clientSecret,
    "TenantId": tenantId,
    "SiteURL": siteURL,
    "GraphEndpoint": graphEndpoint,
    "AuthEndpoint": authEndpoint,
    "TokenEndpoint": tokenEndpoint,
    "AuthURL": authURL,
    "GetAllSitesEndpoint": getAllSitesEndpoint,
    "AccessToken": "",
    "CurrentDir": appPaths["CurrentDir"],
    "LogFilePath": appPaths["LogFilePath"],
    "PromptFilePath": promptFilePath,
    "ChatGPTAPIKey": chatGPTAPIKey,
    "CreatedByFlaskRunId": flaskRunId,
    "PersonalExpenseDB": "PersonalExpenses.db",
    "TokenData": [],
    "SiteIds": [],
    "ListIds": []
  }
  
  
  #Create the token dictionary instance
  tokenData = {
  'grant_type':'authorization_code',
  'code': " ",
  'redirect_uri': 'http://localhost:5000/redirect',
  'client_id': clientId,
  'client_secret': clientSecret,
  }
  
  
  #Append the token dictionary instance to the appConfig dictionary
  appConfig['TokenData'].append(tokenData)
  return appConfig

def getAppConfig(FlaskRunId): #This is the main function for this script
  
  #Define the config file and folder paths. Create the folder and file if they don't exist
  
  #get the paths for this FlaskRunId  
  appPaths = getAppConfigPaths(FlaskRunId)
  
  ConfigFilePath = appPaths['ConfigFilePath']
  
  appConfigCheck = getExistingAppConfig(ConfigFilePath)
  
  if appConfigCheck['isValid'] == 'True':
    WriteOut(f'Valid File Exists', f'Path {ConfigFilePath}', appPaths['LogFilePath'])  
    return appConfigCheck['appConfig']
  
  #App config is not valid, create the default app config
  appConfig = createDefaultAppConfig(appPaths, FlaskRunId)
  
  return appConfig

def getExistingAppConfig(ConfigFilePath):
  
  appConfigCheck = {
    'isValid': 'False',
    'appConfig': []
  }
  try:
    with open(ConfigFilePath, "r") as f:
      appConfig = json.load(f)
      if appConfig['isValid'] == 'True':
        print(f'>>>>>>>>>>>>>>>>>>>>>  FOUND A VALIID appCONFIG FILE  <<<<<<<<<<<<<<<<<<<<<<<<')
        appConfigCheck['isValid'] = 'True'
        appConfigCheck['appConfig'] = appConfig    
        return appConfigCheck
      else:
        return appConfigCheck
  except Exception as e:
    print(f'Could not obtain or open a current ConfigFile at: {os.linesep}{ConfigFilePath}{os.linesep}Error Message: {e}')
    return appConfigCheck

def getAppConfigPaths (FlaskRunId):
 
  #Define the current fileDirectory
  currentDir = os.path.dirname(os.path.abspath(__file__))
 
  
  #Config File
  configSubfolder = 'Config'
  configFileName = 'Connection.config'
  configFilePath = os.path.join(currentDir, configSubfolder, configFileName)
  
  #Log File
  logSubfolder = 'Logs'
  logFileName = 'Log.log'
  logFilePath = os.path.join(currentDir, logSubfolder, logFileName)
  
  #Prompt and Response File (ChatGPT)
  promptSubfolder = 'Logs'
  promptFileName = 'PromptResponse.log'
  promptFilePath = os.path.join(currentDir, promptSubfolder, promptFileName)
  
  
  #Define the critical file paths
  completeLogFilePath = CreateFileAndFolderPath(logFilePath, FlaskRunId)
  completePromptFilePath = CreateFileAndFolderPath(promptFilePath, FlaskRunId, completeLogFilePath)
  completeConfigFilePath = CreateFileAndFolderPath(configFilePath, '', completeLogFilePath)
  
  
  appPaths = {
    "CurrentDir": currentDir,
    #"ConfigFileFolderPath": ConfigFileFolderPath,
    "ConfigFilePath": completeConfigFilePath,
    "LogFilePath": completeLogFilePath,
    "PromptResponseFilePath" : completePromptFilePath
  }
  
  return appPaths

def getDataforSPList(ListName, appConfig, FieldList=None):
  try:
    #Get the listId for the ListName
    listId = ''
    if FieldList == None:
      suffix = 'items?$expand'
    else:
      suffix = f'items?expand=fields(select={FieldList})'
   
    for list in appConfig['ListIds']:
      if list['ListName'] == ListName:
        siteId = list['SiteId']
        listId = list['ListId']
        break
    
    #Get the data for the list
    graphEndpoint = appConfig['GraphEndpoint']
    accessToken = appConfig['AccessToken']
    listResponse = requests.get(f'{graphEndpoint}/sites/{siteId}/lists/{listId}/items?expand=fields(select={FieldList})',
                                headers={'Authorization': 'Bearer ' + accessToken})
    WriteOut("List Response: ", listResponse, appConfig['LogFilePath'])
    listData = listResponse.json()['value']
    
    return listData
  except Exception as e:
    WriteOut("Error getting the List Data: ", str(e), appConfig['LogFilePath'])
    return None
  
# def askChatGPT (appConfig, Prompt=None, Data=None):
  
#   #Assemble the prompt  
#   promptComplete = f'{Prompt}{os.linesep}{os.linesep}{Data}'
  
#   logBreak = '****************************************************************************************************'
  
#   # Set your API key
#   openai.api_key = appConfig['ChatGPTAPIKey']

#   # Create a chat completion with GPT-3.5 Turbo
#   response = openai.ChatCompletion.create(
#     model="gpt-3.5-turbo",
#     messages=[
#         # System message (optional)
#         {"role": "system", "content": "You are a helpful assistant."},
        
#         # User message
#         {"role": "user", "content": promptComplete}
#     ]
#   )

#   # Extract and print the assistant's reply from the response
#   gptResponse = response['choices'][0]['message']['content']
  
#   logMessage = f'{os.linesep}{logBreak}{logBreak}{os.linesep}Prompt: {Prompt}{os.linesep}{os.linesep}Data: {Data}{os.linesep}{os.linesep}Response: {gptResponse}{os.linesep}{logBreak}{logBreak}{os.linesep}'
  
#   WriteOut("ChatGPT Request and Response: ", logMessage, appConfig['PromptFilePath'])
#   return gptResponse
  
def printProgress(StartTime, TotalRecords, CurrentRecord):
  #Adust for zero based index
  CurrentRecord = CurrentRecord + 1
     
  currentTimeNum = datetime.now()
  elapsedTimeNum = currentTimeNum - StartTime
  avgTimePerRecordNum = elapsedTimeNum / (CurrentRecord)
  percentCompleteNum = (CurrentRecord+ 1) / TotalRecords
  estTimeRemainingNum = avgTimePerRecordNum * (TotalRecords - CurrentRecord)
  
  #format these values to display as hh:mm:ss
  avgTimePerRecord = str(avgTimePerRecordNum).split('.')[0]
  estTimeRemaining = str(estTimeRemainingNum).split('.')[0]
  
  #format as percent % e.g. 20%
  percentComplete = str(percentCompleteNum * 100).split('.')[0] + '%'

  print(f"Record {CurrentRecord} of {TotalRecords} completed. {percentComplete} complete. Avg per record: {avgTimePerRecord}. Time remaining: {estTimeRemaining}")

def updateSharePointListItem(appConfig, ListName, FieldName, ItemId, FieldValue):
# Set up the Graph API endpoint and authentication
  siteURL = appConfig['SiteURL']
  listName = ListName
  itemId = ItemId
  accessToken = appConfig['AccessToken']
  fieldName = FieldName  
  fieldValue = json.loads(FieldValue)

  # Set up the request headers and body
  headers = {
      'Authorization': 'Bearer ' + accessToken,
      'Content-Type': 'application/json'
  }
  
  body = {
      fieldName: fieldValue
  }

  
  # WHERE ARE WE???
  # SiateURL may be wrong (Graph vs. SharePoint)
  # there was an extra / in the url before _api
  # Check my user is approved for this api in azure
  
  # Send the Graph API request to update the item
  url = f'{siteURL}_api/web/lists/getbytitle(\'{listName}\')/items({itemId})'
  response = requests.patch(url, headers=headers, json=body)

  if response.status_code == 204: #204 means that the item was updated successfully
    fieldUpdated = True
  else:
    fieldUpdated = False
  
  responseDict = {
    'FieldUpdated': fieldUpdated,
    'StatusCode': response.status_code,
    'ListName': listName,
    'ItemId': itemId,
    'FieldName': fieldName,
    'FieldValue': fieldValue,
    'URL': url,
    'CompleteResponse': response.text,
  }

  return responseDict
#


