import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import boto3

from app.config import AWS_PROFILE, AWS_REGION


class HitlStore:
    def __init__(self, table_name: str = "healthcare-agent-reviews"):
        session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
        self.ddb = session.resource("dynamodb")
        self.table_name = table_name
        self._ensure_table()

    def _ensure_table(self):
        client = self.ddb.meta.client
        try:
            self.ddb.create_table(
                TableName=self.table_name,
                KeySchema=[{"AttributeName": "review_id", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "review_id", "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST",
            )
            self.ddb.Table(self.table_name).wait_until_exists()
        except client.exceptions.ResourceInUseException:
            pass

        ttl = client.describe_time_to_live(TableName=self.table_name).get("TimeToLiveDescription", {})
        if ttl.get("TimeToLiveStatus") != "ENABLED" or ttl.get("AttributeName") != "ttl":
            client.update_time_to_live(
                TableName=self.table_name,
                TimeToLiveSpecification={"Enabled": True, "AttributeName": "ttl"},
            )

    def create_review(self, payload: dict) -> str:
        review_id = str(uuid4())
        now = datetime.now(timezone.utc)
        ttl = int((now + timedelta(days=7)).timestamp())
        item = {
            "review_id": review_id,
            "status": "pending",
            "created_at": now.isoformat(),
            "ttl": ttl,
            "request_json": json.dumps(payload, default=str),
        }
        self.ddb.Table(self.table_name).put_item(Item=item)
        return review_id

    def get_review(self, review_id: str) -> dict | None:
        resp = self.ddb.Table(self.table_name).get_item(Key={"review_id": review_id})
        return resp.get("Item")

    def update_review(self, review_id: str, status: str, reviewer_id: str, decision_reason: str = ""):
        self.ddb.Table(self.table_name).update_item(
            Key={"review_id": review_id},
            UpdateExpression="SET #s = :s, reviewer_id = :r, decision_reason = :d, decided_at = :t",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":s": status,
                ":r": reviewer_id,
                ":d": decision_reason,
                ":t": datetime.now(timezone.utc).isoformat(),
            },
        )
