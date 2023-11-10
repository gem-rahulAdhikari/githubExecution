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
github_personal_access_token_part1 = 'ghp_yL3wH9gGFOmdgcog'
github_personal_access_token_part2 = '3wIh6IOZu2Era62DZcHE'
github_personal_access_token=github_personal_access_token_part1+github_personal_access_token_part2
# github_personal_access_token = os.environ.get('MY_VARIABLE')
# github_personal_access_token = os.getenv("KEY")
sha_value=''
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


@app.route('/seleniumExecution', methods=['GET', 'POST'])
def seleniumGithubAction():
    url = "https://us-east-1.aws.data.mongodb-api.com/app/application-0-awqqz/endpoint/getSeleniumOutput"
    formatted_time=""
    new_branch_name=""
    if request.method == 'POST':
        epoch_time = int(time.time())
        epoch_time_seconds = int(time.time())
        formatted_time = str(epoch_time_seconds)
        print("inside the process")
        c=0
        data = request.get_json()
        codeInput = data.get("text", "")
        email = data.get("userName", "")
        response = requests.get(url)
        if response.status_code == 200:
         data1 = response.json()
         for item in data1:
             if item['Email'] == email:
                 c=c+1
                 formatted_time=item['url']
                 print("user already exist")
                 break;

             
                 
                 
        if c==0:
          print("inside the user defination")
          new_branch_name = formatted_time
        #   epoch_time = int(time.time())
        #   epoch_time_seconds = int(time.time())
        #   formatted_time = str(epoch_time_seconds)
          post_url = "https://us-east-1.aws.data.mongodb-api.com/app/application-0-awqqz/endpoint/addSeleniumResult"
          data_to_send = {
                       "Submissions": [
                           
                           ],
                              "Email":email ,
                              "url": formatted_time,
                              
                       }

          post_response = requests.post(post_url, json=data_to_send)
          if post_response.status_code == 200:
           print("User Add successfullly")
          else:
           print(f"POST request failed with status code: {post_response.status_code}")

        else:
           response = requests.get(url)
           if response.status_code == 200:
            data = response.json()
            for item in data:
               if item['Email'] == email:
                  c=len(item['Submissions'])
                  new_branch_name=item['url']
                  
              

        print("inside post request")
        # branch=data.get("branch", "")
        start_index = codeInput.find('static String reportName')
        quote_start = codeInput.find('"', start_index)
        quote_end = codeInput.find('"', quote_start + 1)
        textareaValue = (
                              codeInput[:quote_start + 1]
                             + "Report_"+formatted_time+"_"+str(c)+ codeInput[quote_end:]
                             )

        print(textareaValue) 
         # Define the paths to the YAML and Java files in your GitHub repository
        yaml_file_path = '.github/workflows/selenium.yml'  # Replace with the actual path to your YAML file
        java_file_path = 'src/main/java/App.java'  # Replace with the actual path to your Java file

        # new_branch_name = formatted_time
        
        # Make an authenticated request to the GitHub API to get the SHA of the source branch
        headers = {
            "Authorization": f"token {github_personal_access_token}",
        }

        source_branch_name = "main"  # Replace with your source branch name
        response = requests.get(f"https://api.github.com/repos/{github_username}/{github_repository}/git/refs/heads/{source_branch_name}", headers=headers)
        print(response.status_code)
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
            response_java_json = response_java.json()
            # print("Response Body for Java:", response_java.text)
            if response_java.status_code == 200:
            # Parse the JSON response
             response_json = response_java.json()
           # Check if the "commit" key exists in the response
             if "commit" in response_json:
              commit_data = response_json["commit"]
              # Iterate over the commit data and print key-value pairs
              for key, value in commit_data.items():
                if key == "sha":
                 sha_value = value
                 print(sha_value);
                 print(f"branch name which is created{replacement_text}")



            # we would hit api until we would get the status completed
              commit_status_url=f"https://api.github.com/repos/{github_username}/{github_repository}/actions/runs?event=push&branch= {replacement_text}&commit={sha_value}" 
              while True:
                 response = requests.get(commit_status_url, headers=headers)
                 if response.status_code == 200:
                    data = response.json()
                    if data['workflow_runs']:
                       latest_run = data['workflow_runs'][0]
                       if latest_run['status'] == 'completed':
                          if latest_run['conclusion'] == 'success':
                           print("Workflow completed successfully.")
                           # Proceed with your further functions here
                           response = requests.get(url)
                           if response.status_code == 200:
                              data = response.json()
                              print(data)
                              for item in data:
                                 if item['url'] == formatted_time:
                                    if 'Submissions' in item and item['Submissions'] and len(item['Submissions']) > 0:
                                       submissions = item['Submissions']
                                       count_submissions = len(submissions)
                                       print(count_submissions)
                                       lastSubmission = item['Submissions'][-1]
                                       lastSubmissionOutput = lastSubmission.get('Output', None)
                                       print(lastSubmissionOutput)
                           return jsonify({"result": lastSubmissionOutput})            
                           break
                          else:
                             print("Workflow completed with a failure.")
                             break
                          
                    else:
                       print("Workflow is still running...")

                 else:
                     print("Failed to fetch workflow run details.")  

              time.sleep(2)                       


             else:
              print("No 'commit' key found in the response JSON")
            else:
             print(f"Request to {update_java_url} failed with status code: {response_java.status_code}")
           
      
    

    
    # time.sleep(60)
    # response = requests.get(url)
    # if response.status_code == 200:
    #     data = response.json()
    #     print(data)
    #     for item in data:
    #         # if item['url'] == "http://g-codeeditor.el.r.appspot.com/editor?name=d57bc5785be7dfc774f8b69c8f08e3556c4d94060006fd5f91c51b0feb82f742":
    #         if item['url'] == formatted_time:
    #             # print(item['Submissions'])
    #             if 'Submissions' in item and item['Submissions'] and len(item['Submissions']) > 0:
    #                 submissions = item['Submissions']
    #                 count_submissions = len(submissions)
    #                 print(count_submissions)
    #                 lastSubmission = item['Submissions'][-1]
    #                 lastSubmissionOutput = lastSubmission.get('Output', None)
    #                 print(lastSubmissionOutput)


        
    # return jsonify({"result": lastSubmissionOutput})
  




   
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