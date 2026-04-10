from dataclasses import dataclass
from typing import Optional

# Timestamp format: "YYYY/MM/DD-HH:MM"
TIMESTAMP_FORMAT = "%Y/%m/%d-%H:%M"

# Valid status values
STATUS_NOT_STARTED = "not_started"
STATUS_IN_PROGRESS = "in_progress"
STATUS_BREACHED_DEADLINE = "breached_deadline"
STATUS_DONE_INTIME = "done_intime"


@dataclass
class Task:
    task_id: str
    title: str
    description: str
    comments: list[str]
    eta: Optional[str]
    created_time: str        # "YYYY/MM/DD-HH:MM"
    started_time: Optional[str]
    expected_end_time: Optional[str]
    end_time: Optional[str]
    status: str

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "comments": self.comments,
            "eta": self.eta,
            "created_time": self.created_time,
            "started_time": self.started_time,
            "expected_end_time": self.expected_end_time,
            "end_time": self.end_time,
            "status": self.status,
        }
