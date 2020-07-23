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


# ---------------------------------------------------------------
# ------ DELETES ALL RESOURCES ----------------------------------
# ---------------------------------------------------------------
get_tg = None
get_instance = None
get_elb = None

# ---------------------------------------------------------------
# ------ GET TARGET GROUP DETAILS ---------------------------------------
# ---------------------------------------------------------------
try:
    get_tg = clientELB.describe_target_groups(
        Names=[
            'air-tek-tg',
        ]
    )
    print("Target Group Found: {}\n".format(get_tg['TargetGroups'][0]['TargetGroupArn']))

except Exception as e:
    print("TargetGroup not found\n")

# ---------------------------------------------------------------
# ------ GET INSTANCE DETAILS -----------------------------------
# ---------------------------------------------------------------
try:
    get_instance = clientEC2.describe_instances(
        Filters=[
            {
                'Name': 'tag:hello-world-service',
                'Values': [
                    'air-tek-instance',
                ]
            },
            {
                'Name': 'instance-state-name',
                'Values': [
                    'running'
                ]
            }
        ],
    )
    print("The Following Instances Found: {}\n".format(get_instance['Reservations']))

    # Only 1 instance SHOULD exist. If length is greater than 0 assume 1. If not set to 0
    instanceid = 1 if len(get_instance['Reservations']) > 0 else 0
    
    if instanceid > 0:
        print("instance id is greater than 0...")
        deregister_tg = clientELB.deregister_targets(
            TargetGroupArn=get_tg['TargetGroups'][0]['TargetGroupArn'],
            Targets=[
                {
                    'Id': get_instance['Reservations'][0]["Instances"][0]['InstanceId'],
                    'Port': 80
                },
            ]
        )
        print(deregister_tg)
        print("Deregistering Target...")
        waitDeregisterTG = clientELB.get_waiter('target_deregistered')
        waitDeregisterTG.wait(
            TargetGroupArn=get_tg['TargetGroups'][0]['TargetGroupArn'],
            Targets=[
                {
                    'Id': get_instance['Reservations'][0]["Instances"][0]['InstanceId'],
                }
            ]
        )
        print("Deregistered Target Group!")
        print("Deleting Target Group...")
    else:# If not registered with any instance
        print("Deleting Target Group...")
        # delete_tg = clientELB.delete_target_group(
        #     TargetGroupArn=get_tg['TargetGroups'][0]['TargetGroupArn']
        # )
        # print("Target group was deleted: {}\n".format(delete_tg))
except Exception as e:
    print(e)
    print("Instances Not Found\n")

# ---------------------------------------------------------------
# ------ GET LISTENER DETAILS and DELETE LISTENER and TG --------
# ---------------------------------------------------------------
try:
    get_elb = clientELB.describe_load_balancers(
        Names=['air-tek-elb']
    )
    print("Existing ELB is: {}\n".format(get_elb))

    get_listener = clientELB.describe_listeners(
        LoadBalancerArn=get_elb['LoadBalancers'][0]['LoadBalancerArn'],
    )
    print("Existing Listener is: {}\n".format(get_listener))

    delete_listener = clientELB.delete_listener(
        ListenerArn=get_listener['Listeners'][0]['ListenerArn']
    )

    delete_tg = clientELB.delete_target_group(
            TargetGroupArn=get_tg['TargetGroups'][0]['TargetGroupArn']
    )
    print("Target Group DELETED: {}\n".format(delete_tg))

except Exception as e:
    print(e)
    print("No listener found and no target group found\n")

# ---------------------------------------------------------------
# ------ DELETE ELB ---------------------------------------------
# ---------------------------------------------------------------
try:
    print("Deleting ELB....")
    delete_elb = clientELB.delete_load_balancer(
        LoadBalancerArn=get_elb['LoadBalancers'][0]['LoadBalancerArn']
    )
    waiter = clientELB.get_waiter('load_balancers_deleted')
    waiter.wait(
        LoadBalancerArns=[
                get_elb['LoadBalancers'][0]['LoadBalancerArn'],
        ],
    )
    print("ELB was deleted: {}\n".format(delete_elb))
except Exception as e:
    print(e)
    print("Error Deleing ELB\n")

# ---------------------------------------------------------------
# ------ DELETE INSTANCE ----------------------------------------
# ---------------------------------------------------------------
try:
    get_instance = clientEC2.describe_instances(
        Filters=[
            {
                'Name': 'tag:hello-world-service',
                'Values': [
                    'air-tek-instance',
                ]
            },
            {
                'Name': 'instance-state-name',
                'Values': [
                    'running'
                ]
            }
        ],
    )
    print("Number Of Instances Found: {}\n".format(len(get_instance['Reservations'])))
    print("Terminating Instance...")
    for main in get_instance['Reservations']:
        terminate_instance = clientEC2.terminate_instances(
            InstanceIds=[
                main['Instances'][0]['InstanceId'],
            ],
            DryRun=False
        )
        waiterTerminateInstance = clientEC2.get_waiter('instance_terminated')
        waiterTerminateInstance.wait(
            InstanceIds=[
                main['Instances'][0]['InstanceId'],
            ],
            DryRun=False,
        )
        print("Instance Terminated: {}\n".format(main['Instances'][0]['InstanceId']))
except Exception as e:
    print(e)
    print("Instance not found\n")

# ---------------------------------------------------------------
# ------ DELETE TG-SG -------------------------------------------
# ---------------------------------------------------------------
try:
    get_tg_sg = clientEC2.describe_security_groups(
        GroupNames=['air-tek-tg-sg']
    )
    print("Current TG-SG Is: {}\n".format(get_tg_sg['SecurityGroups'][0]['GroupId']))
    print("Deleting TG-SG...")
    sec_tg_name=get_tg_sg['SecurityGroups'][0]['GroupId']
    delete_tg_sg = clientEC2.delete_security_group(
        GroupId=sec_tg_name,
        DryRun=False
    )
    print("TG SG DELETED: {}\n".format(delete_tg_sg))
except Exception as e:
    print(e)
    print("TG SG not found\n")

# ---------------------------------------------------------------
# ------ DELETE ELB-SG ------------------------------------------
# ---------------------------------------------------------------
try:
    get_elb_sg = clientEC2.describe_security_groups(
        GroupNames=['air-tek-elb-sg']
    )
    print("Current ELB-SG is: {}\n".format(get_elb_sg['SecurityGroups'][0]['GroupId']))
    print("Deleting ELB-SG...")
    sec_elb_name=get_elb_sg['SecurityGroups'][0]['GroupId']
    delete_elb_sg = clientEC2.delete_security_group(
        GroupId=sec_elb_name,
        DryRun=False
    )
    print("ELB SG was deleted: {}\n".format(delete_elb_sg))
except Exception as e:
    print(e)
    print("\nELB SG not found")

