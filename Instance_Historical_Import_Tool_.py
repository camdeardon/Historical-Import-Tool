#!/usr/bin/env python
# coding: utf-8

# The code below is a script example of a tool that is used will query an instance take records using the knowledge map API to create a data import record for use in instance consolidation or quickly grabbing data from one instance to put into another. 
# 
# This script will also work to fill out an Edcast import CSV and leverage the Axonify APIs to create Deeplinks in the Topic Sync function.
# 
# This code will import the libraries that are required to run this script and store the records on your machine in a folder call "Edcast_Axonify_connection"

# ## Imports

# In[ ]:


get_ipython().system('pip install --user -U nltk')


# In[ ]:


# Data manipulation libraries
import numpy as np
import pandas as pd

# API calling libraries
import json
from datetime import datetime
import requests
from tqdm import tqdm, trange


# Libraries to save files
import os
from os import path
import getpass



# Natural Language processing libraries
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
nltk.download('stopwords')
nltk.download('punkt')


# ## Provide a list of users with of the learning records you'd like to retrieve. 

# The script will iterate through the users, calling the GET knowledgeMap API to retrieve the data for each user.

# In[ ]:


# Provide a list of users with of the learning records you'd like to retrieve. 
users = ['Pursuit_Content Catalogue Sync_AUWC'         ,'Pursuit_Content Catalogue Sync_CDNCC'         ,'Pursuit_Content Catalogue Sync_GBSD'         ,'Pursuit_Content Catalogue Sync_GFS'         ,'Pursuit_Content Catalogue Sync_GWAMFS'         ,'Pursuit_Content Catalogue Sync_GWAMRL'         ,'Pursuit_Content Catalogue Sync_MFS']


# ## Get topic_sync function is created

# 
# 
# ---
# 
# 
# This function will make the files, and create a folder within the folder "Edcast_Axonify_connection, that now should be created on your desktop, containing the name of the instance. It will fill in the CSV provided by Edcast
# 
# 
# 
# 
# 
# ---
# 
# 
# 
# 

# In[ ]:


# This grabs the time and saves it as a string for use later on.
today = datetime.now().strftime("%Y%m%d")
folder_today = datetime.now().strftime('%d - %B - %Y')
today_seconds = datetime.now().strftime("%Y%m%d%H%M%S")
username = getpass.getuser()


# In[ ]:


# This text will extract topic names, and remove stopwords for use in extracting key words

stop_words = set(stopwords.words('english'))

def remove_stop_words(text):
    tokens = word_tokenize(text)
    filtered_tokens = [token for token in tokens if not token.lower() in stop_words]
    filtered_text = ' '.join(filtered_tokens)
    return filtered_text


# In[ ]:


def topic_sync(instance,users,api_key,date):
    #Create empty lists to store user data in.
    topic_data = []
    subject_data = []
    category_data = []
    intro_data = []
    not_found_users = []

    
    # This will check to see if you have a folder for the particular instance, and if you do not it will create one.
    instance_path = f'/Users/{username}/Desktop/Edcast_Axonify_connection/{folder_today}/{instance}'
    if not os.path.exists(instance_path):
        
        # create the folder for storing the CSV records
        os.makedirs(instance_path)
        print(f'Folder {instance_path} created.')
    else:
        print(f'Folder {instance_path} already exists.')


    # iterate through users and grab the knowledge map using the Knowledge Map API
    # In order to use the API the data needs to be parsed from the response. 
    
    for user in tqdm(users,desc = 'Record Calls', unit = 'User Knowledge Maps Receieved'):
        try:
            # Call the knowledgemap API calling in the variables for user, instance and provide an API token.
            knowledge_map = f"https://{instance}/axonify/api/v2/users/{user}/knowledgemap?api_token={api_key}"
            knowledge_map_data = requests.get(knowledge_map).json()
            
            # Split the response into the API into the employeeId and knowledgeRecords
            employeeId = knowledge_map_data['employeeId']
            knowledgeRecords = knowledge_map_data['knowledgeRecords']
            
            # Optional, this will print out for logging purposes.
            #print(f'EmployeeID: {user} Knowledge Map Retrieved')
            

        # iterate through the knowledgeRecords, collecting the data for each record.
        
            for record in knowledgeRecords:
                # extract the values for topicExternalId, level, topicGraduationTimestamp, totalAnswerCount and correctAnswerCount
                categoryExternalId = record['topicDetails']['categoryExternalId']
                categoryName = record['topicDetails']['categoryName']    
                topicExternalId = record['topicDetails']['topicExternalId']
                topicName = record['topicDetails']['topicName']
                subjectExternalId = record['topicDetails']['subjectExternalId']
                topicInternalId = record['topicDetails']['topicId']
                subjectName = record['topicDetails']['subjectName']
                level = record['topicDetails']['level']
                topicGraduationTimestamp = record['topicGraduationTimestamp']
                correctAnswerCount = record['overallMetrics']['correctAnswerCount']
                totalAnswerCount = record['overallMetrics']['totalAnswerCount']
                introductoryStatus = record['introductoryStatus']
                
                # Add records to the topic data array
                topic_data.append([employeeId, topicExternalId,topicName, level,topicInternalId ])
             
        except:
            not_found_users.append(user)
            pass
            #print(f'User {user} not found')
            #not_found_users.append(user)

    # Create a dataframe from the data lists with the columns of 'Employee_ID', 'Topic_External_ID', 'Topic_Name','Difficulty_Level','Internal_Id'
    
    # This data can now be parsed to create deep links into individual topics.
    # This function exports this dataframe as a csv
    
    topic_df = pd.DataFrame(topic_data, columns=['Employee_ID', 'Topic_External_ID', 'Topic_Name','Difficulty_Level','Internal_Id'])


    # Ed_Cast Template. This code will provide deep links to topics.
    # Deep link base URL
    base_url = f'https://{instance}/training/index.html#assessmentLink?topicId='
    
    # Use the difficulty level, topic internal id in conjunction with the base URL to create topic deep links.
    topic_df['Topic_Deep_Link'] = topic_df.apply(lambda row: base_url + str(row['Internal_Id']) + '&level=' + str(row['Difficulty_Level']), axis=1)
    
    ed_cast_template = topic_df[['Topic_External_ID','Topic_Name','Topic_Deep_Link','Difficulty_Level']]
    
    ed_cast_template['description'] = ""
    ed_cast_template['image_url'] = ""
    ed_cast_template['Topic_Name'] = ed_cast_template['Topic_Name'].apply(remove_stop_words)
    ed_cast_template['keywords'] = topic_df['Topic_Name'].str.replace(" ",",")
    ed_cast_template['duration'] = ""
    ed_cast_template['archive'] = ""
    ed_cast_template['language'] = 'en'
    ed_cast_template['content_type'] = "course"
    ed_cast_template['providor_name'] = 'Axonify'

    # Rename the columns to match the requirements for Edcast.
    ed_cast_template = ed_cast_template.rename(columns = {'Topic_External_Id':'id','Topic_Name':'title','Topic_Deep_Link':'deeplink_url'})
    ed_cast_template['Topic_Name'] = ed_cast_template.apply(lambda row: row['title'] + ' - Level ' + str(row['Difficulty_Level']), axis=1)
    ed_cast_template['title'] = ed_cast_template['Topic_Name']
    ed_cast_template = ed_cast_template.drop(columns = ['Topic_Name','Difficulty_Level'])
    

    # Export the dataframes to a CSV file
    ed_cast_template.to_csv(f'{instance_path}/{instance}_Edcast_Template_{today_seconds}.csv',index = False)
    topic_df.to_csv(f'{instance_path}/{instance}_Assigned_Knowledge_Map_{today_seconds}.csv',index = False)

    return ed_cast_template, topic_df


# # Pass in API Key / Instance URL

# 
# 
# ---
# 
# 
# This code is where you can specific your API key and your instance name. Change the strings below to the relavent information, taking care to keep the information between quotation marks like below. 
# 
# 
# 
# ---
# 
# 

# In[63]:


instance = ''


# In[59]:


api_token = ''


# # Get knowledge records function is called

# 
# ---
# 
# 
# This code below will call the function, where you give it the string names of your input variables. For simplicity don't change this, just replace the USER file,instance url and API token and the rest should work.
# 
# ---
# 
# 
# 

# In[ ]:


records = topic_sync(instance,users,api_token,today_seconds)

