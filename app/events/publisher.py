import boto3
from app.core.events import VehicleBookedEvent, VehicleMaintenanceEvent

sns_client = boto3.client('sns')

class EventPublisher:
    def __init__(self, sns_topic_arn: str):
        self.sns_topic_arn = sns_topic_arn  # AWS SNS Topic ARN

    def publish_vehicle_booked_event(self, event: VehicleBookedEvent):
        response = sns_client.publish(
            TopicArn=self.sns_topic_arn,
            Message=str(event.dict()),
            Subject="VehicleBookedEvent"
        )
        return response

    def publish_vehicle_maintenance_event(self, event: VehicleMaintenanceEvent):
        response = sns_client.publish(
            TopicArn=self.sns_topic_arn,
            Message=str(event.dict()),
            Subject="VehicleMaintenanceEvent"
        )
        return response
