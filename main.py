from flask import Flask, redirect, url_for, render_template, session,request,jsonify,json,Response,g
import requests
import logging
from flask_cors import CORS
from flask_restful import Resource, Api, reqparse, abort
from datetime import datetime, timedelta,date
from flask_session import Session
import json
import os
from logging.handlers import RotatingFileHandler
import pandas as pd
import uuid
import base64
import subprocess
import yaml  # Import the PyYAML library
import time
import urllib.parse



app = Flask(__name__, static_folder='static')

active_keys = set()
access_duration = timedelta(seconds=30)

CORS(app)
api = Api(app)

ip_address='35.230.92.82'


#Git hub credentials
github_username = 'gem-rahulAdhikari'
github_repository = 'githubSelenium'
github_personal_access_token = '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'
# github_personal_access_token = os.environ.get('KEY')
source_branch_name = "main"

# Set the API URLs
old_file_path = 'src/test/java/'  # Replace with the current file path
old_file_path1 = 'src/main/java/App.java'  
new_file_path =''

old_api_url = f'https://api.github.com/repos/{github_username}/{github_repository}/contents/'

api_url1 =f'https://api.github.com/repos/{github_username}/{github_repository}/contents/src/test/java'

@app.route('/')
def index():

    return render_template('index.html');


@app.route("/process_text3", methods=["POST"])
def process_text():
    data = request.get_json()
    text = data.get("text", "")

    # Process the text (you can replace this with your specific code)
    processed_text = "Received and processed: " + text

    return jsonify({"result": processed_text})




@app.route('/seleniumExecution', methods=['GET', 'POST'])
def seleniumGithubAction():
    url = "https://us-east-1.aws.data.mongodb-api.com/app/application-0-awqqz/endpoint/getSeleniumOutput"
    formatted_time=""
    if request.method == 'POST':
        print("inside the process")
        c=0
        data = request.get_json()
        text = data.get("text", "")
        userName = data.get("userName", "")
        print(userName)
        print(type(userName))
        response = requests.get(url)
        if response.status_code == 200:
         data1 = response.json()
         for item in data1:
             if item['Email'] == userName:
                 c=c+1
                 formatted_time=item['url']
                 print("user already exist")
                 break;

             
                 
                 
        if c==0:
          print("inside the user defination")
          epoch_time = int(time.time())
          epoch_time_seconds = int(time.time())
          formatted_time = str(epoch_time_seconds)
          post_url = "https://us-east-1.aws.data.mongodb-api.com/app/application-0-awqqz/endpoint/addSeleniumResult"
          data_to_send = {
                       "Submissions": [
                           
                           ],
                              "Email":userName ,
                              "url": formatted_time,
                              
                       }

          post_response = requests.post(post_url, json=data_to_send)
          if post_response.status_code == 200:
           print("User Add successfullly")
          else:
           print(f"POST request failed with status code: {post_response.status_code}")

        print("inside post request")
        branch=data.get("branch", "")
        start_index = text.find('static String reportName')
        quote_start = text.find('"', start_index)
        quote_end = text.find('"', quote_start + 1)
        textareaValue = (
                              text[:quote_start + 1]
                             + "Report_"+formatted_time+ text[quote_end:]
                             )

        print(textareaValue) 
         # Define the paths to the YAML and Java files in your GitHub repository
        yaml_file_path = '.github/workflows/selenium.yml'  # Replace with the actual path to your YAML file
        java_file_path = 'src/main/java/App.java'  # Replace with the actual path to your Java file

        new_branch_name = branch
        
        # Make an authenticated request to the GitHub API to get the SHA of the source branch
        headers = {
            "Authorization": f"token {github_personal_access_token}",
        }

        source_branch_name = "main"  # Replace with your source branch name
        response = requests.get(f"https://api.github.com/repos/{github_username}/{github_repository}/git/refs/heads/{source_branch_name}", headers=headers)

        if response.status_code == 200:
            sha = response.json()['object']['sha']
            print(sha)
        else:
            return f"Failed to get the SHA of the source branch."

        # Create a new branch based on the SHA of the source branch
        data = {
            "ref": f"refs/heads/{new_branch_name}",
            "sha": sha,
        }


        search_text = "beta1"
        replacement_text = new_branch_name
        response = requests.post(f"https://api.github.com/repos/{github_username}/{github_repository}/git/refs", headers=headers, json=data)

    
        latest_yaml_response = requests.get(f"https://api.github.com/repos/{github_username}/{github_repository}/contents/{yaml_file_path}?ref={new_branch_name}", headers=headers)
        latest_java_response = requests.get(f"https://api.github.com/repos/{github_username}/{github_repository}/contents/{java_file_path}?ref={new_branch_name}", headers=headers)
        
        if latest_yaml_response.status_code == 200 and latest_java_response.status_code == 200:
            latest_yaml_content = latest_yaml_response.json()['content']
            latest_java_content = latest_java_response.json()['content']

            latest_yaml_sha = latest_yaml_response.json()['sha']
            latest_java_sha = latest_java_response.json()['sha']

            
            current_java_content=base64.b64decode(latest_java_content).decode()
            current_yaml_content=base64.b64decode(latest_yaml_content).decode()

            updated_yaml_content = current_yaml_content.replace(search_text, replacement_text)


            updated_content=textareaValue

            encoded_java_content=base64.b64encode(updated_content.encode()).decode()
            encoded_yaml_content=base64.b64encode(updated_yaml_content.encode()).decode()


            yaml_data = {
                'message': 'Update YAML and Java files',
                'content': encoded_yaml_content,
                'sha': latest_yaml_sha,
                "branch": new_branch_name,
                'path': yaml_file_path
            }

            java_data = {
                'message': 'Update YAML and Java files',
                'content': encoded_java_content,
                'sha': latest_java_sha,
                "branch": new_branch_name,
                'path': java_file_path
            }

            # Send the requests to update the YAML and Java files on GitHub
            update_yaml_url = f'https://api.github.com/repos/{github_username}/{github_repository}/contents/{yaml_file_path}'
            update_java_url = f'https://api.github.com/repos/{github_username}/{github_repository}/contents/{java_file_path}'

            response_yaml = requests.put(update_yaml_url, json=yaml_data, headers=headers)
            response_java = requests.put(update_java_url, json=java_data, headers=headers)
            
           


    
    time.sleep(100)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(data)
        for item in data:
            # if item['url'] == "http://g-codeeditor.el.r.appspot.com/editor?name=d57bc5785be7dfc774f8b69c8f08e3556c4d94060006fd5f91c51b0feb82f742":
            if item['url'] == formatted_time:
                # print(item['Submissions'])
                if 'Submissions' in item and item['Submissions'] and len(item['Submissions']) > 0:
                    submissions = item['Submissions']
                    count_submissions = len(submissions)
                    print(count_submissions)
                    lastSubmission = item['Submissions'][-1]
                    lastSubmissionOutput = lastSubmission.get('Output', None)
                    print(lastSubmissionOutput)


        
    return jsonify({"result": lastSubmissionOutput})
  




   
#Update the github App.java dile without changing the name of .java file.
@app.route('/process_text1', methods=['POST']) 
def updateFile():
    try:
        booleanValue=False
        second_value=''
        data = request.json  # Get the JSON data from the request body
        textareaValue1 = data.get('text', '')
        new_report_name = "New Report Name"
        start_index = textareaValue1.find('static String reportName')
        quote_start = textareaValue1.find('"', start_index)
        quote_end = textareaValue1.find('"', quote_start + 1)
        
        count=data.get('count', '')
        current_url = data.get('url', '')
        split_url = current_url.split("=")
        if len(split_url) >= 2:
         second_value = split_url[1]  # Get the second value
         print("Second value:", second_value)
        else:
         print("URL format is not as expected")


        textareaValue = (
                              textareaValue1[:quote_start + 1]
                             + "Report_"+second_value+"_"+str(count)
                              + textareaValue1[quote_end:]
                             )

        print("hello") 
        print(textareaValue) 
        print("hello") 

        headers = {
            'Authorization': f'Bearer {github_personal_access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        
       
        # get_url = "https://us-east-1.aws.data.mongodb-api.com/app/application-0-awqqz/endpoint/getSeleniumOutput"  # Replace with your API URL

        # get_response = requests.get(get_url)

        # if get_response.status_code == 200:
        #  data = get_response.json();
        #  print("Response Data:")
        #  print(data)
        #  if data:
        #   for item in data:
        #    print(item['url'])
        #    print("hello this ")
        #    entry_url = item['url']
        #    if entry_url == current_url:
        #       booleanValue=True
        #       break;
           

        #  else:
        #   print("this is post")
        #   booleanValue=True
        #   Name=''
        #   Email=''
        #   Key=''
           
        #   getuser_url = "https://us-east-1.aws.data.mongodb-api.com/app/application-0-awqqz/endpoint/getAdminTableDataWithoutFile"
        #   getuser_response = requests.get(getuser_url)
        #   if getuser_response.status_code == 200:
        #     data = getuser_response.json();
        #     for item in data:
        #           if item['url'] == current_url:
        #            Name=item['Name']
        #            Email=item['Email']
        #            Key=item['SecretKey']
                  
             
        #     post_url = "https://us-east-1.aws.data.mongodb-api.com/app/application-0-awqqz/endpoint/addSeleniumResult"  # Replace with your API URL

        #     data_to_send = {
        #     "Submissions": [
                           
        #                    ],
        #                       "name":Name,
        #                       "Email":Email ,
        #                       "url": current_url,
        #                       "key":Key
        #                }

        #     post_response = requests.post(post_url, json=data_to_send)

        #     if post_response.status_code == 200:
        #       print("POST request successful")
        #     else:
        #       print(f"POST request failed with status code: {post_response.status_code}")

        # else:
        #  print(f"Request failed with status code: {get_response.status_code}")      
         


        
        # if booleanValue==False:
        #     print("this is post")
        #     Name=''
        #     Email=''
        #     Key=''
            
        #     getuser_url = "https://us-east-1.aws.data.mongodb-api.com/app/application-0-awqqz/endpoint/getAdminTableDataWithoutFile"
        #     getuser_response = requests.get(getuser_url)
        #     if getuser_response.status_code == 200:
        #      data = getuser_response.json();
        #      for item in data:
        #           if item['url'] == current_url:
        #            Name=item['Name']
        #            Email=item['Email']
        #            Key=item['SecretKey']
                  
                
        #      post_url = "https://us-east-1.aws.data.mongodb-api.com/app/application-0-awqqz/endpoint/addSeleniumResult"  # Replace with your API URL

        #      data_to_send = {
        #      "Submissions": [
                            
        #                    ],
        #                       "name":Name,
        #                       "Email":Email ,
        #                       "url": current_url,
        #                       "key":Key
        #                }

        #      post_response = requests.post(post_url, json=data_to_send)

        #      if post_response.status_code == 200:
        #       print("POST request successful")
        #      else:
        #       print(f"POST request failed with status code: {post_response.status_code}")

        
        # url = f'https://api.github.com/repos/{github_username}/{github_repository}/contents/{old_file_path1}'
        # response = requests.get(url, headers=headers)
        # response_json = response.json()
        # print(response_json)
        # sha = response_json['sha']

        # current_content = response_json['content']
        # current_content_decoded = base64.b64decode(current_content).decode()

        
        # updated_content = textareaValue

        # encoded_content = base64.b64encode(updated_content.encode()).decode()

        
        # data = {
        #     'message': 'Text update from online input',
        #     'content': encoded_content,
        #     'sha': sha,
        #     'path': old_file_path1 
        # }

        
        # update_url = f'https://api.github.com/repos/{github_username}/{github_repository}/contents/{old_file_path1}'
        # response = requests.put(update_url, json=data, headers=headers)

        # if response.status_code == 200:
        #     print('File updated successfully.')
        # else:
        #     print('Failed to update file.')
        #     print(response.json())

        return jsonify({'message': 'Text pushed to GitHub successfully!'}), 200
    except Exception as e:
        print(e)
        return jsonify({'message': 'Failed to push text to GitHub.'}), 500    
        




if __name__ == '__main__':
    app.run(debug=True)           