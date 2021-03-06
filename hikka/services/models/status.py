from datetime import datetime
from hikka import static
import mongoengine

class Status(mongoengine.Document):
    account = mongoengine.ReferenceField("User", required=True)
    subject = mongoengine.GenericReferenceField(required=True)
    created = mongoengine.DateTimeField(default=datetime.utcnow)
    updated = mongoengine.DateTimeField(default=datetime.utcnow)
    rating = mongoengine.IntField(min_value=1, max_value=10)
    content = mongoengine.IntField(required=True)
    position = mongoengine.IntField(default=None)
    status = mongoengine.IntField(default=None)
    rewatch = mongoengine.IntField(default=0)
    time = mongoengine.IntField(default=0)

    meta = {
        "alias": "default",
        "collection": "statuses",
        "indexes": [
            "subject",
            "account",
            "rating",
            "status",
        ],
        "ordering": ["-created"]
    }

    def dict(self):
        return {
            "created": int(datetime.timestamp(self.created)),
            "updated": int(datetime.timestamp(self.updated)),
            "status": static.slug("statuses", self.status),
            "subject": self.subject.dict(),
            "position": self.position,
            "rewatch": self.rewatch,
            "rating": self.rating,
            "time": self.time
        }
