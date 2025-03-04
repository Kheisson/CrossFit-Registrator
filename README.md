# CrossFit Registrator

This code is used with an AWS Lambda function that automates the process of scheduling classes on the Arbox application. It logs into the platform, checks class schedules based on predefined rules, and registers for a class. Upon completion, it sends a notification using Amazon Simple Notification Service (SNS).

---

## Local Setup

### Prerequisites
- AWS account
- Python 3.x installed
- Virtual environment (recommended)

### Installation

To set up your local environment, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/CrossFit-Registrator.git
   cd CrossFit-Registrator
   ```

1.  **Create and activate a virtual environment:**

    ```python
    python -m venv venv
    source venv/bin/activate  # On Unix or MacOS
    venv\Scripts\activate  # On Windows
    ```

2.  **Install required dependencies:**

    ```bash
    cd package
    pip install -r requirements.txt
    ```

3.  **Create a `.env` file in the project directory and add the following variables:**

    ```dosini
    USER_EMAIL=your-email@example.com
    USER_PASSWORD=yourpassword
    SNS_REGION=your-sns-region
    SNS_TOPIC_ARN=your-sns-topic-arn
    SCHEDULE_CONFIG='{"0": {"class": "PUMP", "hour": 18, "minute": 30},"1": {"class": "PUMP", "hour": 18, "minute": 0},"3": {"class": "Weightlifting", "hour": 17, "minute": 30}}'
    ```

    Replace `your-email@example.com`, `yourpassword`, `your-sns-region`, and `your-sns-topic-arn` with your Arbox credentials and AWS SNS region and topic ARN. The `SCHEDULE_CONFIG` maps your schedule.

4.  **To test locally, uncomment the following lines in the script:**

   ```python
    # Uncomment for local testing only, not for production
    if __name__ == "__main__":
        lambda_handler({}, {})
   ```

5.  **Run the script:**

    ```python
    python lambda_function.py
    ```

* * * * *

AWS Lambda Deployment
---------------------

### Usage

After testing, go into the package folder.

1.  **Install the dependencies in the same folder as the main code:**

    ```bash
    pip install -r requirements.txt -t .
    ```

3.  **Create the deployment package:**

    ```bash
    zip -r package.zip .
    ```

### Creating Lambda Function

1.  Log in to the AWS Management Console and navigate to **AWS Lambda**.
2.  Create a new Lambda function with the Python 3.12 runtime.
3.  Set the handler to `wc_auto_registration.lambda_handler`.
4.  Upload your code through the AWS Lambda Console or AWS CLI.

### Configuration

1.  Increase the timeout to 2 minutes.

2.  Set up the following environment variables within your Lambda function:

    -   `USER_EMAIL`: Your Arbox email.
    -   `USER_PASSWORD`: Your Arbox password.
    -   `SNS_REGION`: The AWS region of your SNS Topic.
    -   `SNS_TOPIC_ARN`: The Amazon Resource Name (ARN) of your SNS Topic.
    -   `SCHEDULE_CONFIG`: JSON mapping of your schedule:\
        `0: Monday | 1: Tuesday | 2: Wednesday | 3: Thursday | 4: Friday | 5: Saturday | 6: Sunday`

### Creating SNS Topic and Subscription

1.  Navigate to the **Amazon SNS Console** and create a new topic.
2.  Create a subscription to the topic using the desired endpoint (e.g., an email address).

### Lambda Execution Role

Create a role for your Lambda with the following policies:

-   `AWSLambdaBasicExecutionRole`: Allows Lambda functions to execute and create logs.
-   `AmazonSNSFullAccess`: Allows Lambda to publish messages to SNS topics.

### Scheduling Lambda Execution

In AWS Lambda, use **EventBridge** (formerly **CloudWatch Events**) to create a trigger. Set up a cron expression to schedule execution at the desired times. Example:

`cron(0 18 * * ? *) to run every day at 6 PM UTC.`
