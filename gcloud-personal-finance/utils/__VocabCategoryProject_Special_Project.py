import csv
from multiprocessing import Process
import os
import sys
from datetime import datetime
import re
from collections import Counter
import _transaction_file_type_maps as td
import datetime as timedelta
import pandas as pd
#Get spacy which will help with the dictionary and transaction definition cleanup
import spacy

#from file_utils import get_file_paths

#Python insstalls required for this script
# pip3 install spacy
# python3 -m spacy download en_core_web_sm
# pip3 install pandas
# pip3 install file_utils

## Deprecated imports
#from numpy import full
#from multiprocessing import process
#from tracemalloc import start
#import json
#from enum import unique 
#from math import e
#Import MSF (which is not in the same folder structure)
standardFunctionsDirectory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'SharedFunctions'))
sys.path.append(standardFunctionsDirectory)
import _msf

#Create the current Directory Variable
currentDirectory = os.path.dirname(os.path.abspath(__file__))

logFile = os.path.join(currentDirectory, 'Logs', 'Log.txt')
_msf.CreateFileAndFolderPath(logFile)

def ProcessBusinessLogic(logFile):
    #Create the current Directory Variable
    currentDirectory = os.path.dirname(os.path.abspath(__file__))
    
    #This gets all the CSV and TXT files from the Transactions directory
    file_paths = get_file_paths('TransactionFiles/')

    outputUniqueWords = os.path.join(currentDirectory, "Vocab", 'uniquewords.txt')
    outputCleanedWords = os.path.join(currentDirectory, "Vocab", 'cleanwords.txt')
    outputVocab = os.path.join(currentDirectory, "Vocab", 'vocab.txt')
    outputFullVocab = os.path.join(currentDirectory, "Vocab", 'FullVocab.txt')
    _msf.CreateFileAndFolderPath(outputFullVocab)
    _msf.CreateFileAndFolderPath(outputUniqueWords)
    _msf.CreateFileAndFolderPath(outputCleanedWords)
    _msf.CreateFileAndFolderPath(outputVocab)
    
    #This gets a huge dictionary of all the words in the spacy dictionary
    #This is used to clean the garbage out of the transaction descriptions
    nlp = spacy.load("en_core_web_sm")
    vocab = set(nlp.vocab.strings) ##<<< this is the set of all words in the spacy dictionary
    _msf.WriteOut('Vocab', vocab, outputVocab)
    
    #This extends the vocab of cleaned words with the words from each transaction file that are valid words but not in the spacy dictionary
    full_vocab = vocab
    for inputTransactionFile in file_paths:
        cleaned_words = generateAllValuesInAColumn(inputTransactionFile, outputUniqueWords, outputCleanedWords, logFile)
        full_vocab = full_vocab | set(cleaned_words)
    
    #Log the Vocabulary
    _msf.WriteOut('Full Vocab', full_vocab, outputFullVocab)
  
    #Matching improvement Files
    RocketMoneyDescriptions= os.path.join(currentDirectory, 'Working', 'RocketMoneyDescriptions.csv')
    outputFile_DistinctWords= os.path.join(currentDirectory, 'Working', 'RockMonDistinctWords.csv')

    ######## UNIQUE WORD GENERATOR FROM CA BUSINESS FILE / Rocket Moeny######
    #allDescriptions = getAllColumnDataFromFile(outputTransactionsCSV, RocketMoneyDescriptions, 15, 17, 19, 'CSV', full_vocab)
    generateDistinctValueCount(RocketMoneyDescriptions, outputFile_DistinctWords)

def generateDistinctValueCount(input_file_path, output_file_path):
    skip_words = {'the', 'and', 'or', 'if', 'but', 'inc', 'llc', 'llp'}  # Add any words you want to skip to this set
    values_set = set()
    values_list = []

    # Open the input file
    with open(input_file_path, 'r') as input_file:
        for line in input_file:
            # Split the text on space
            values = line.strip().split(' ')
            for value in values:
                # Skip words with less than 3 characters
                if len(value) < 3:
                    continue
                # Skip words in the skip_words set
                if value.lower() in skip_words:
                    continue
                # Add value to values_list
                values_list.append(value)
                # Add value to the set if it's not already present
                values_set.add(value)

    # Count occurrences of each value in the values_list
    value_counts = Counter(values_list)

    # Prepare the distinct_values_count_list
    distinct_values_count_list = [(value, value_counts[value]) for value in values_set]

    # Export distinct_values_count_list to a CSV file
    with open(output_file_path, 'w', newline='') as output_file:
        writer = csv.writer(output_file)
        writer.writerow(['Value', 'Count'])
        writer.writerows(distinct_values_count_list)

def get_file_paths(directory):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    directory_path = os.path.join(current_dir, directory)
    file_paths = [os.path.join(directory_path, file) for file in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, file)) and (file.endswith('.txt') or file.endswith('.csv'))]
    return file_paths
        
def process_files(input_filepath, full_filepath, output_filepath):
  #This function was only used once as part of the initial data analysis
  # Open the input file as CSV
  input_df = pd.read_csv(input_filepath, chunksize=None)
  start_time = datetime.now()

  # Create a list that is identical to the two columns in the input file
  # except it has an extra empty column called descExample
  input_with_desc = input_df.copy()

  input_with_desc['descExample'] = ""

  # Open the full file as CSV
  full_df = pd.read_csv(full_filepath, dtype=str)

  # Define a function to concatenate the description columns and check for keyword matches
  def find_matches(row, full_df):
    key_word = row[0]
    concatenated_matches = ""
    counter = 0
    if row.name % 1000 == 0:
        print(f"Processed {row.name} rows")
    for index, full_row in full_df.iterrows():
        transDesc = str(full_row['txtTransactionOriginalNameClean']).lower() + " " + str(full_row['txtTranName']).lower()
        if key_word in transDesc and counter < 5:
            concatenated_matches += transDesc + ", "
            counter += 1
    return concatenated_matches[:-2]  # removes last comma and space

  # Apply the find_matches function to each row in the input_with_desc DataFrame
  #input_with_desc['descExample'] = input_with_desc.apply(find_matches, axis=1, args=(full_df,)  )
  input_with_desc['descExample'] = input_with_desc[0].str.contains(full_df['txtTransactionOriginalNameClean'] + " " + full_df['txtTranName'])

  # Write the output file as CSV
  input_with_desc.to_csv(output_filepath, index=False)

  # Print the elapsed time and estimated time remaining
  elapsed_time = datetime.now() - start_time
  rows_processed = len(input_with_desc)
  rows_per_second = rows_processed / elapsed_time.total_seconds()
  estimated_time_remaining = (len(full_df) - rows_processed) / rows_per_second
  print(f"Processed {rows_processed} rows in {elapsed_time}, estimated time remaining: {datetime.now() + timedelta(seconds=estimated_time_remaining)}")
  #process_files(outputFile_DistinctWords, inputFile_RocketMoney, 'KeyWordsWithExamples.csv')

def generateAllValuesInAColumn(inputTransactionFile, outputUniqueWords, outputCleanedWords, logFile):
  #Get the unique words from the transactions
  # Not sure if this is a permanent part of the script.
  # # The challenge is that the spacy dicitonary is great for english words, but not so great for merchant names
  # # So, I am trying to build a dictionary of all the words in the 10,000+ transactions that are not in the spacy dictionary and add them to the spacy dictionary
  headers = {'txtTransactionOriginalName': 6, 'TranNameOrig': 9}

  with open(inputTransactionFile) as f:
    reader = csv.reader(f)
    next(reader) #<< Skip the header row
    
    uniqueWords = set() #Later we will clean up and modify this set and add it to the spacy dictionary
    
    for row in reader:
      #Concatenate the two fields that we are interested in (there are two description fields in the Rocket Money CSV)
      trans_text = row[headers['txtTransactionOriginalName']] + " " + row[headers['TranNameOrig']]
      #Split them on spaces
      new_words = re.findall(r"\w+", trans_text.lower())  
      
      # Filter out 1 letter words
      new_words = [w for w in new_words if len(w) > 1] 
      
      #Add them to the set if they aren't already there
      uniqueWords |= set(new_words)

  #Writing this out to a file to see how we did
  _msf.WriteOut('Cleaned Words', uniqueWords, logFile)

  #We didnt' do so well. Lot's of numbers, and meaningless strings. We need to clean further
  cleaned_words = []

  for word in uniqueWords:
    
    # Replace all numeric digits with a single space. We don't need numbers in our description or in our dicitonary
    cleaned = re.sub(r'\d', ' ', word)  

    # Remove extra spaces (sometimes we have twoor more spaces in a row)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # Ok, now we will remove some special characters: / + , "
    cleaned = re.sub(r'[/+,"]', ' ', cleaned)
  
    # Remove single chars (a single letter means nothing)
    cleaned = re.sub(r'\b\w\b', '', cleaned)
    
    # Remove leading and trailing spaces
    cleaned = cleaned.strip()
    
    cleanedNumbertest = cleaned.replace(' ', '')
      
    # If only digits remain, make sure we don't add it to the dictionary
    if cleaned.isdigit():
      continue 
    # If only digits remain, make sure we don't add it to the dictionary (sometimes there's two numbers next to each other)
    if cleanedNumbertest.isdigit():
      continue 
    
    #We should only have words left (or strings of letters with more than one char).  
    # #Let's add them to the cleaned_words set
    #Lets begin by splitting on spaces
    splits = cleaned.split(' ')  
    for split in splits:
      #Trim it
      trimmed = split.strip()
      #Add it to the cleaned_words set if it's not already there
      if trimmed not in cleaned_words:
        cleaned_words.append(trimmed.lower())
        
    

  #Ok, let's see how we did now!
  _msf.WriteOut('Cleaned Words', cleaned_words, logFile)


    
  with open(outputUniqueWords, 'w') as f:
    for item in uniqueWords:
      f.write("%s\n" % item)
      f.flush
      f.close
      
  with open(outputCleanedWords, 'w') as f:
    for item in cleaned_words:
      f.write("%s\n" % item)
      f.flush
      f.close
    
  _msf.WriteOut('Unique Words', uniqueWords, logFile)

  return cleaned_words

if __name__ == '__main__':
  ProcessBusinessLogic(logFile)