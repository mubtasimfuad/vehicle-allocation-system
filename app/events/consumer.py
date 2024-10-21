import boto3

sns_client = boto3.client("sns")


class EventConsumer:
    def __init__(self, sns_subscription_arn: str):
        self.sns_subscription_arn = sns_subscription_arn  # AWS SNS Subscription ARN

    def consume_vehicle_booked_event(self):
        # This method will receive the event and handle it
        # Example: notify the driver or log the booking

        response = sns_client.receive_message(QueueUrl=self.sns_subscription_arn)
        for message in response.get("Messages", []):
            print(f"Received VehicleBookedEvent: {message['Body']}")
            # Handle the event (e.g., notify driver, update logs, etc.)
            sns_client.delete_message(
                QueueUrl=self.sns_subscription_arn,
                ReceiptHandle=message["ReceiptHandle"],
            )
