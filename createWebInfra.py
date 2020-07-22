import boto3
import configparser
config = configparser.ConfigParser()
config.sections()
clientELB = boto3.client('elbv2')
clientEC2 = boto3.client('ec2')
resourceEC2 = boto3.resource('ec2')


def getVarFromFile(filename):
    global data, file
    mainfile = config.read(filename)
    data = config['DEFAULT']


getVarFromFile('config.ini')


# # -----------------------------------------------
# # ------ DELETE EVERYTHING BEFORE STARTING ------
# # -----------------------------------------------
# get_tg = None
# get_instance = None
# get_elb = None
# try:
#     # get target group by name
#     get_tg = clientELB.describe_target_groups(
#         Names=[
#             'air-tek-tg',
#         ]
#     )
#     print("Target Group Found: {}\n".format(
#         get_tg['TargetGroups'][0]['TargetGroupArn']))
# except Exception as e:
#     print("\nTargetGroup not found")

# try:
#     get_instance = clientEC2.describe_instances(
#         Filters=[
#             {
#                 'Name': 'tag:Name',
#                 'Values': [
#                     'air-tek-instance',
#                 ]
#             },
#             {
#                 'Name': 'instance-state-name',
#                 'Values': [
#                     'running'
#                 ]
#             }
#         ],
#     )
#     get_tg = clientELB.describe_target_groups(
#         Names=[
#             'air-tek-tg',
#         ]
#     )
#     print("These are instances that were found: {}\n".format(get_instance['Reservations']))

#     instanceid = 1 if len(get_instance['Reservations']) > 0 else 0
#     print(instanceid)
#     print(get_tg)
#     if instanceid > 0:
#         deregister_tg = clientELB.deregister_targets(
#             TargetGroupArn=get_tg['TargetGroups'][0]['TargetGroupArn'],
#             Targets=[
#                 {
#                     'Id': instanceid,
#                     'Port': 80
#                 },
#             ]
#         )
#         waiterTG = clientELB.get_waiter('target_deregistered')
#         waiterTG.wait(
#             TargetGroupArn=get_tg['TargetGroups'][0]['TargetGroupArn'],
#         )
#         delete_tg = clientELB.delete_target_group(
#             TargetGroupArn=get_tg['TargetGroups'][0]['TargetGroupArn']
#         )
#         print("Target group was deleted: {}\n".format(delete_tg))
#     else:
#         delete_tg = clientELB.delete_target_group(
#             TargetGroupArn=get_tg['TargetGroups'][0]['TargetGroupArn']
#         )
#         print("Target group was deleted: {}\n".format(delete_tg))
# except Exception as e:
#     print("Instances not found")

# try:
#     get_elb = clientELB.describe_load_balancers(
#         Names=['air-tek-elb']
#     )
#     print("Existing ELB is: {}\n".format(get_elb))

#     get_listener = clientELB.describe_listeners(
#         LoadBalancerArn=get_elb['LoadBalancers'][0]['LoadBalancerArn'],
#     )
#     print("Existing Listener is: {}\n".format(get_listener))

#     delete_listener = clientELB.delete_listener(
#         ListenerArn=get_listener['Listeners'][0]['ListenerArn']
#     )

# except Exception as e:
#     print("\nNo listener found and no target group found")

# try:
#     get_elb = clientELB.describe_load_balancers(
#         Names=['air-tek-elb']
#     )
#     # print(get_elb['LoadBalancers'][0]['LoadBalancerArn'])
#     delete_elb = clientELB.delete_load_balancer(
#         LoadBalancerArn=get_elb['LoadBalancers'][0]['LoadBalancerArn']
#     )
#     waiter = clientELB.get_waiter('load_balancers_deleted')
#     waiter.wait(
#         LoadBalancerArns=[
#                 get_elb['LoadBalancers'][0]['LoadBalancerArn'],
#         ],
#     )
#     print("ELB was deleted: {}\n".format(delete_elb))
# except Exception as e:
#     print("\nELB not found")


# try:
#     get_sg = clientEC2.describe_security_groups(
#         Filters=[
#             {
#                 'Name': 'tag:hello-world-service',
#                 'Values': [
#                     'air-tek-sg',
#                 ]
#             },
#         ]
#     )
#     print("Current SG is: {}\n".format(get_sg['SecurityGroups'][0]['GroupName']))
#     sec_id=get_sg['SecurityGroups'][0]['GroupName']
#     # delete_security_group = resourceEC2.SecurityGroup(sec_id)
#     # response = delete_security_group.delete()
#     delete_sg = clientEC2.delete_security_group(
#         GroupName=sec_id,
#         DryRun=False
#     )
#     print("SG was deleted: {}\n".format(delete_sg))
# except Exception as e:
#     console.log(e)
#     print("\nSG not found")

# try:
#     get_instance = clientEC2.describe_instances(
#         Filters=[
#             {
#                 'Name': 'tag:Name',
#                 'Values': [
#                     'air-tek-instance',
#                 ]
#             },
#             {
#                 'Name': 'instance-state-name',
#                 'Values': [
#                     'running'
#                 ]
#             }
#         ],
#     )
#     print("Number of instances found: {}\n".format(len(get_instance['Reservations'])))
#     terminate_instance = None
#     for main in get_instance['Reservations']:
#         terminate_instance = clientEC2.terminate_instances(
#             InstanceIds=[
#                 main['Instances'][0]['InstanceId'],
#             ],
#             DryRun=False
#         )

# except Exception as e:
#     print("\nInstance not found")
# -----------------------------------------------
# ------ CREATE SECURITY GROUP ELB and TG------
# -----------------------------------------------
security_group_ELB = None
security_group_TG = None
target_group = None
try:
    print("\nCreating ELB SG....")
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
    print("Security Group CREATED: {}\n".format(security_group_ELB['GroupId']))

except Exception as e:
    print(e)
    print("Can't create SG")

try:
    print("\nCreating Target Group SG....")
    print(security_group_ELB['GroupId'])
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
    print("Security Group CREATED: {}\n".format(security_group_TG['GroupId']))

except Exception as e:
    print(e)
    print("Can't create TG and SG")

# -----------------------------------------------
# ------ CREATE LOAD BALANCER ------
# -----------------------------------------------
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

    target_group = clientELB.create_target_group(
        Name='air-tek-tg',
        Protocol='HTTP',
        Port=80,
        VpcId=data['VPC_ID']
    )
    print(target_group)
    print("Target Group CREATED: {}\n".format(target_group['TargetGroups'][0]['TargetGroupArn']))

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
    print("Can't create ELB,TargetGroup or Listener")

# -----------------------------------------------
# ------ CREATE EC2 ------
# -----------------------------------------------
user_data = '''#!/bin/bash
echo 'test' > /tmp/hello'''
try:
    print("getting security group id for instance...")
    print(security_group_TG['GroupId'])
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
    print("Created Instance ID: {}\n".format(create_instance[0].id))
    instance = resourceEC2.Instance(create_instance[0].id)
    print("Instance is creating...\n")
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
    print("Registering target...\n")
    register_targets = clientELB.register_targets(
    TargetGroupArn=target_group['TargetGroups'][0]['TargetGroupArn'],
        Targets=[
            {
                'Id': create_instance[0].id,
                'Port': 80
            },
        ]
    )

except Exception as e:
    print(e)
    print("Can't create Instance")
