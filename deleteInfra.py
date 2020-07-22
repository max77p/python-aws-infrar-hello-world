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


# -----------------------------------------------
# ------ DELETE EVERYTHING BEFORE STARTING ------
# -----------------------------------------------
get_tg = None
get_instance = None
get_elb = None
try:
    # get target group by name
    get_tg = clientELB.describe_target_groups(
        Names=[
            'air-tek-tg',
        ]
    )
    print("Target Group Found: {}\n".format(
        get_tg['TargetGroups'][0]['TargetGroupArn']))
except Exception as e:
    print("\nTargetGroup not found")

try:
    get_instance = clientEC2.describe_instances(
        Filters=[
            {
                'Name': 'tag:Name',
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
    get_tg = clientELB.describe_target_groups(
        Names=[
            'air-tek-tg',
        ]
    )
    print("These are instances that were found: {}\n".format(get_instance['Reservations']))

    instanceid = 1 if len(get_instance['Reservations']) > 0 else 0
    print(instanceid)
    print(get_tg)
    if instanceid > 0:
        deregister_tg = clientELB.deregister_targets(
            TargetGroupArn=get_tg['TargetGroups'][0]['TargetGroupArn'],
            Targets=[
                {
                    'Id': instanceid,
                    'Port': 80
                },
            ]
        )
        waiterTG = clientELB.get_waiter('target_deregistered')
        waiterTG.wait(
            TargetGroupArn=get_tg['TargetGroups'][0]['TargetGroupArn'],
        )
        delete_tg = clientELB.delete_target_group(
            TargetGroupArn=get_tg['TargetGroups'][0]['TargetGroupArn']
        )
        print("Target group was deleted: {}\n".format(delete_tg))
    else:
        delete_tg = clientELB.delete_target_group(
            TargetGroupArn=get_tg['TargetGroups'][0]['TargetGroupArn']
        )
        print("Target group was deleted: {}\n".format(delete_tg))
except Exception as e:
    print("Instances not found")

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

except Exception as e:
    print("\nNo listener found and no target group found")

try:
    get_elb = clientELB.describe_load_balancers(
        Names=['air-tek-elb']
    )
    print(get_elb['LoadBalancers'][0]['LoadBalancerArn'])
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
    print("\nELB not found")

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
    print("Number of instances found: {}\n".format(len(get_instance['Reservations'])))
    terminate_instance = None
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
        print("Instance terminated: {}\n".format(main['Instances'][0]['InstanceId']))
except Exception as e:
    print("\nInstance not found")

try:
    get_tg_sg = clientEC2.describe_security_groups(
        GroupNames=['air-tek-tg-sg']
    )
    print("Current SG is: {}\n".format(get_tg_sg['SecurityGroups'][0]['GroupId']))
    sec_tg_name=get_tg_sg['SecurityGroups'][0]['GroupId']
    # delete_security_group = resourceEC2.SecurityGroup(sec_id)
    # response = delete_security_group.delete()
    delete_tg_sg = clientEC2.delete_security_group(
        GroupId=sec_tg_name,
        DryRun=False
    )

    print("TG SG was deleted: {}\n".format(delete_tg_sg))
except Exception as e:
    print(e)
    print("\nTG SG not found")

try:
    get_elb_sg = clientEC2.describe_security_groups(
        GroupNames=['air-tek-elb-sg']
    )
    print(get_elb_sg)
    print("Current SG is: {}\n".format(get_elb_sg['SecurityGroups'][0]['GroupId']))
    sec_elb_name=get_elb_sg['SecurityGroups'][0]['GroupId']
    # delete_security_group = resourceEC2.SecurityGroup(sec_id)
    # response = delete_security_group.delete()
    delete_elb_sg = clientEC2.delete_security_group(
        GroupId=sec_elb_name,
        DryRun=False
    )
    print("ELB SG was deleted: {}\n".format(delete_elb_sg))
except Exception as e:
    print(e)
    print("\nELB SG not found")

