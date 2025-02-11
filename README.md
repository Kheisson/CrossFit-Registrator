# CrossFit Registrator

This code is used with an AWS Lambda function that automates the process of scheduling classes on the Arbox application. It logs into the platform, checks class schedules based on predefined rules, and registers for a class. Upon completion, it sends a notification using Amazon Simple Notification Service (SNS).


# Local Setup

### Prerequisites


* AWS account

* Python 3.x installed

* Virtual environment (recommended)


## Installation

To set up your local environment, follow these steps:



1. Clone the repository:


```bash
git clone https://github.com/your-username/CrossFit-Registrator.git
cd CrossFit-Registrator
```

2. Create and activate a virtual environment:


```bash
python -m venv venv
source venv/bin/activate  # On Unix or MacOS
venv\Scripts\activate  # On Windows
```

3. Install required dependencies:


```bash
pip install -r requirements.txt
```

4. Create a .env file in the project directory and add the following variables:


```bash
USER_EMAIL=your-email@example.com
USER_PASSWORD=yourpassword
SNS_REGION=your-sns-region
SNS_TOPIC_ARN=your-sns-topic-arn
SCHEDULE_CONFIG='{"0": {"class": "PUMP", "hour": 18, "minute": 30},"1": {"class": "PUMP", "hour": 18, "minute": 0},"3": {"class": "Weightlifting", "hour": 17, "minute": 30}}' //This is just an example, this will sign you up to Pump on Monday at 18:30, Pump on Tuesday at 18:00 and Weightlifting at 17:30
```

> Replace your-email@example.com, yourpassword, your-sns-region, and your-sns-topic-arn with your Arbox credentials and AWS SNS region and topic ARN.
> SCHEDULE_CONFIG maps your schedule.


5. To test locally, uncomment the following lines in the script:


```python
# Uncomment for local testing only, not for production

if __name__ == "__main__":
    lambda_handler({}, {})
```
6. Run the script:


```bash
python lambda_function.py
```

## AWS Lambda Deployment

### Creating Lambda Function

* Log in to the AWS Management Console and navigate to AWS Lambda.
Create a new Lambda function with the Python runtime that matches your environment.
Upload your code through the AWS Lambda Console or AWS CLI.

#### Environment Variables

Set up the following environment variables within your Lambda function:



**USER_EMAIL**: Your Arbox email.

**USER_PASSWORD**: Your Arbox password.

**SNS_REGION**: The AWS region of your SNS Topic.

**SNS_TOPIC_ARN**: The Amazon Resource Name (ARN) of your SNS Topic.

**SCHEDULE_CONFIG**: JSON mapping of your schedule:     0: Monday | 1: Tuesday | 2: Wednesday | 3: Thursday | 4: Friday | 5: Saturday | 6: Sunday

#### Creating SNS Topic and Subscription

* Navigate to the Amazon SNS Console and create a new topic.
* Create a subscription to the topic using the desired endpoint (e.g., an email address).

#### Lambda Execution Role

* Create a role for your Lambda with the following policies:


**AWSLambdaBasicExecutionRole**: Allows Lambda functions to execute and create logs.

**AmazonSNSFullAccess**: Allows Lambda to publish messages to SNS topics.


#### Scheduling Lambda Execution

In AWS Lambda, use EventBridge (formerly CloudWatch Events) to create a trigger.
Set up a cron expression to schedule execution at the desired times. Example: cron(0 18 * * ? *) to run every day at 6 PM UTC.

### Usage

Customize the scheduling by modifying the TARGET_HOUR and days_to_add dictionary in the code. These values determine the class schedule and registration rules. You can set which days to skip and which class times to target.
