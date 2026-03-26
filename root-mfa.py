import boto3

iam = boto3.client('iam')

response = iam.list_users()
print('Connected to AWS!')
print('Total users found:', len(response['Users']))
