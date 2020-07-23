# Hello world application spun up using python boto3 and flask and nginx
### Features
    1. EC2 Instance
    2. Nginx
    3. Python Flask
    4. Application Load Balancer with Target Group
    5. Security Group to only allow access through ALB

### How to replicate
    1. Change sampleConfig.ini to config.ini and fill out the relevant information - without quotes
    2. Run python createWebInfra.py
    3. Wait for the setup to complete before visiting the application link (should be same as ALB DNS Name)
    4. Run python deleteInfra.py to destroy all resources