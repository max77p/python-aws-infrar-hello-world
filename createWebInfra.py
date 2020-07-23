import boto3
import configparser
config = configparser.ConfigParser()
config.sections()
clientELB = boto3.client('elbv2')
clientEC2 = boto3.client('ec2')
resourceEC2 = boto3.resource('ec2')

# ---------------------------------------------------------------
# ------ GET SECRETS FROM config.ini FILE -----------------------
# ---------------------------------------------------------------
def getVarFromFile(filename):
    global data, file
    mainfile = config.read(filename)
    data = config['DEFAULT']
    
getVarFromFile('config.ini')

# ******************* STEPS ***********************************************************
# ------ 1. Create SG's for ELB and TG with tags and ingress rules --------------------
# ------ 2. Create ELB, attach listener, security groups and configure targer group ---
# ------ 3. Setup UserData bash script to pass into instance creation -----------------
# ------ 4. Create Instance, attach SG and target group -------------------------------
# ******************* STEPS ***********************************************************

# ---------------------------------------------------------------
# ------ CREATION OF ELB-SG -------------------------------------
# ---------------------------------------------------------------
security_group_ELB = None
security_group_TG = None
target_group = None
try:
    print("Creating ELB SG....")
    security_group_ELB = clientEC2.create_security_group(
        Description='airtek ELB sg',
        GroupName='air-tek-elb-sg',
        VpcId=data['VPC_ID'],
        DryRun=False
    )
    create_tag = clientEC2.create_tags(
        DryRun=False,
        Resources=[
            security_group_ELB['GroupId'],
        ],
        Tags=[
            {
                'Key': 'hello-world-service',
                'Value': 'air-tek-elb-sg'
            },
        ]
    )
    waiterSG = clientEC2.get_waiter('security_group_exists')
    waiterSG.wait(
        Filters=[
            {
                'Name': 'group-id',
                'Values': [
                    security_group_ELB['GroupId'],
                ]
            },
        ]
    )
    sec_ingress=resourceEC2.SecurityGroup(security_group_ELB['GroupId'])
    response = sec_ingress.authorize_ingress(
        CidrIp='0.0.0.0/0',
        FromPort=80,
        ToPort=80,
        GroupName='air-tek-elb-sg',
        IpProtocol='tcp',
        DryRun=False
    )
    print("ELB Security Group CREATED: {}\n".format(security_group_ELB['GroupId']))

except Exception as e:
    print(e)
    print("Can't create ELB-SG")

# ---------------------------------------------------------------
# ------ CREATE TG-SG -------------------------------------------
# ---------------------------------------------------------------
try:
    print("Creating Target Group SG....")
    security_group_TG = clientEC2.create_security_group(
        Description='airtek TG sg',
        GroupName='air-tek-tg-sg',
        VpcId=data['VPC_ID'],
        DryRun=False
    )
    create_tag = clientEC2.create_tags(
        DryRun=False,
        Resources=[
            security_group_TG['GroupId'],
        ],
        Tags=[
            {
                'Key': 'hello-world-service',
                'Value': 'air-tek-tg-sg'
            },
        ]
    )
    waiterSG = clientEC2.get_waiter('security_group_exists')
    waiterSG.wait(
        Filters=[
            {
                'Name': 'group-id',
                'Values': [
                    security_group_TG['GroupId'],
                ]
            },
        ]
    )
    sec_ingress=resourceEC2.SecurityGroup(security_group_TG['GroupId'])
    response = sec_ingress.authorize_ingress(
        IpPermissions=[
            {
            'IpProtocol': 'tcp', 
            'FromPort': 22, 
            'ToPort': 22, 
            'IpRanges': [
                {
                    'CidrIp': '0.0.0.0/0',
                    'Description': 'simple http'
                },
            ],
            },
            {
            'IpProtocol': 'tcp', 
            'FromPort': 80, 
            'ToPort': 80, 
            'UserIdGroupPairs': [{ 'GroupId': security_group_ELB['GroupId'] }] 
            }
        ],
        DryRun=False
    )
    print("TG Security Group CREATED: {}\n".format(security_group_TG['GroupId']))

except Exception as e:
    print(e)
    print("Can't create TG-SG")

# ---------------------------------------------------------------
# ------ CREATE ELB, LISTENER, TARGETGROUP, ---------------------
# ---------------------------------------------------------------
load_balancer_main=None
try:
    load_balancer_main = clientELB.create_load_balancer(
        Name='air-tek-elb',
        Subnets=[
            data['SubnetId-1a'], data['SubnetId-2b']
        ],
        SecurityGroups=[
            security_group_ELB['GroupId'],
        ],
        Scheme='internet-facing',
        Type='application',
        Tags=[
            {
                'Key': 'hello-world-service',
                'Value': 'air-tek-application-elb'
            },
        ]
    )
    print("Creating ELB....")
    waiter = clientELB.get_waiter('load_balancer_available')
    waiter.wait(
        LoadBalancerArns=[
            load_balancer_main['LoadBalancers'][0]['LoadBalancerArn'],
        ]
    )
    print("ELB CREATED: {}\n".format(load_balancer_main['LoadBalancers'][0]['LoadBalancerArn']))
    print("Creating Target Group...")
    target_group = clientELB.create_target_group(
        Name='air-tek-tg',
        Protocol='HTTP',
        Port=80,
        VpcId=data['VPC_ID']
    )
    print("Target Group CREATED: {}\n".format(target_group['TargetGroups'][0]['TargetGroupArn']))
    print("Creating Listener....")
    listener = clientELB.create_listener(
        LoadBalancerArn=load_balancer_main['LoadBalancers'][0]['LoadBalancerArn'],
        Protocol='HTTP',
        Port=80,
        DefaultActions=[
            {
                'Type': 'forward',
                'TargetGroupArn': target_group['TargetGroups'][0]['TargetGroupArn'],
            }
        ]
    )
    print("Listener CREATED: {}\n".format(listener['Listeners'][0]['ListenerArn']))

except Exception as e:
    print(e)
    print("Error creating ELB, TargetGroup or Listener")

# ---------------------------------------------------------------
# ------ SETUP USERDATA BASH SCRIPT -----------------------------
# ------ Note: Pass in DNS name of ELB for Nginx server block ---
# ---------------------------------------------------------------
load_balancer_DNS_Name=load_balancer_main['LoadBalancers'][0]['DNSName']
user_data = '''#!/bin/bash
#The line below is important!
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
echo BEGIN
apt-get update
apt install python3-pip -y
apt-get install nginx -y
apt-get install gunicorn3 -y
pip3 install flask
apt-get install git
cd home
git clone https://github.com/max77p/python-aws-infrar-hello-world.git
mv python-aws-infrar-hello-world/ mainapp/
cd /etc/nginx/sites-enabled/
cat > flaskapp <<EOF 
server {
        listen 80;
        server_name %s;

        location / {
            proxy_pass http://127.0.0.1:8000;
        }
} 
EOF
sed -i    's/# server_names_hash_bucket_size 64;/server_names_hash_bucket_size 128;/g' /etc/nginx/nginx.conf
sudo systemctl restart nginx
cd
cd /home/mainapp/myapp/
touch test.json
echo created file
sudo gunicorn3 app:app
echo Started app
''' % load_balancer_DNS_Name

# ---------------------------------------------------------------
# ------ CREATE INSTANCE ----------------------------------------
# ---------------------------------------------------------------
try:
    print("Creating Instance....")
    create_instance = resourceEC2.create_instances(
        ImageId = data['ImageId_value'],
        MinCount = 1,
        MaxCount = 1,
        InstanceType = data['InstanceType_value'],
        SubnetId=data['SubnetId-1a'],
        UserData=user_data,
        SecurityGroupIds=[
            security_group_TG['GroupId'],
        ],
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'hello-world-service',
                        'Value': 'air-tek-instance'
                    },
                    {
                        'Key': 'Name',
                        'Value': 'air-tek-ec2'
                    },
                ]
            },
        ],
        KeyName = data['KeyName_value']
    )
    print("Instance CREATED: {}\n".format(create_instance[0].id))
    instance = resourceEC2.Instance(create_instance[0].id)
    print("Instance Is Starting...")
    instance.wait_until_running(
        Filters=[
            {
                'Name': 'tag:hello-world-service',
                'Values': [
                    'air-tek-instance',
                ]
            },
        ],
        DryRun=False
    )
    print("Instance RUNNING!\n")
    print("Registering Target...")
    register_targets = clientELB.register_targets(
        TargetGroupArn=target_group['TargetGroups'][0]['TargetGroupArn'],
        Targets=[
            {
                'Id': create_instance[0].id,
                'Port': 80
            },
        ]
    )
    target_attribute_change = clientELB.modify_target_group_attributes(
        TargetGroupArn=target_group['TargetGroups'][0]['TargetGroupArn'],
        Attributes=[
            {
                'Key': 'deregistration_delay.timeout_seconds',
                'Value': '100'
            },
        ]
    )
    print("Target Group registered!\n")
    print("Waiting For UserData To Complete...")
    waiterInstanceStatus = clientEC2.get_waiter('instance_status_ok')
    waiterInstanceStatus.wait(
        InstanceIds=[
            create_instance[0].id,
        ],
        DryRun=False,
    )
    
    print("ALL COMPLETE")
    print("Application created and available at: http://{}\n".format(load_balancer_DNS_Name))
except Exception as e:
    print(e)
    print("Can't create Instance")
