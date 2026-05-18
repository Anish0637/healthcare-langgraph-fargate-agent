from decimal import Decimal
from datetime import datetime, timedelta

import boto3

from app.config import AWS_PROFILE, AWS_REGION, DDB_MEMORY_TABLE


class MemoryStore:
    def __init__(self):
        session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
        self.ddb = session.resource("dynamodb")
        self.table_name = DDB_MEMORY_TABLE
        self._ensure_table()

    def _ensure_table(self):
        client = self.ddb.meta.client
        try:
            self.ddb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {"AttributeName": "tenant_id", "KeyType": "HASH"},
                    {"AttributeName": "timestamp", "KeyType": "RANGE"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "tenant_id", "AttributeType": "S"},
                    {"AttributeName": "timestamp", "AttributeType": "S"},
                ],
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

    def save(self, tenant_id: str, user_id: str, prompt: str, response: str, duration_sec: float):
        now = datetime.utcnow()
        expiry = int((now + timedelta(days=30)).timestamp())
        self.ddb.Table(self.table_name).put_item(
            Item={
                "tenant_id": tenant_id,
                "timestamp": now.isoformat(),
                "user_id": user_id,
                "prompt": prompt,
                "response": response,
                "duration_seconds": Decimal(str(duration_sec)),
                "ttl": expiry,
            }
        )
