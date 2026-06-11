import re
from datetime import datetime
from typing import Optional
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

# Common date patterns found in meeting minutes
DATE_PATTERNS = [
    r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b",
    r"\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|"
    r"July|August|September|October|November|December),?\s+\d{4})\b",
    r"\b((?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2},?\s+\d{4})\b",
    r"\b(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})\b",
]

DATE_FORMATS = [
    "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d",
    "%d-%m-%Y", "%m-%d-%Y", "%Y-%m-%d",
    "%B %d, %Y", "%B %d %Y",
    "%d %B %Y", "%d %B, %Y",
]

ATTENDEE_TRIGGERS = [
    "present:", "in attendance:", "attendees:", "members present:",
    "participants:", "attending:", "those present:",
]

DEPARTMENT_KEYWORDS = [
    "finance", "hr", "human resources", "it", "information technology",
    "operations", "marketing", "legal", "management", "executive",
    "admin", "administration", "procurement", "audit", "board",
    "strategy", "engineering", "product", "sales", "customer service",
]

DECISION_TRIGGERS = [
    "resolved:", "agreed:", "decided:", "approved:", "it was agreed",
    "it was resolved", "decision:", "conclusions:", "resolution:",
]

ACTION_TRIGGERS = [
    "action:", "action item:", "to do:", "task:", "follow up:",
    "action required:", "responsible:", "assigned to:",
]


def parse_date(raw_text: str) -> Optional[datetime]:
    """Attempts to extract a meeting date from the document text."""
    for pattern in DATE_PATTERNS:
        matches = re.findall(pattern, raw_text, re.IGNORECASE)
        for match in matches:
            clean = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", match)
            for fmt in DATE_FORMATS:
                try:
                    return datetime.strptime(clean.strip(), fmt)
                except ValueError:
                    continue
    return None


def extract_attendees(raw_text: str) -> list:
    """Extracts a list of attendee names from the document text."""
    attendees = []
    lines = raw_text.splitlines()

    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if any(trigger in line_lower for trigger in ATTENDEE_TRIGGERS):
            for j in range(i + 1, min(i + 20, len(lines))):
                next_line = lines[j].strip()
                if not next_line or next_line.endswith(":"):
                    break
                names = [n.strip() for n in next_line.split(",") if n.strip()]
                attendees.extend(names)
            break

    return list(dict.fromkeys(attendees))


def extract_department(raw_text: str, filename: str = "") -> Optional[str]:
    """Infers the department from document text or filename."""
    search_text = (raw_text[:1000] + " " + filename).lower()
    for dept in DEPARTMENT_KEYWORDS:
        if dept in search_text:
            return dept.title()
    return None


def extract_agenda_items(raw_text: str) -> list:
    """Extracts agenda items from the document text."""
    agenda = []
    lines = raw_text.splitlines()
    in_agenda = False

    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        if "agenda" in line_lower and len(line_stripped) < 60:
            in_agenda = True
            continue

        if in_agenda:
            if not line_stripped:
                continue
            if any(
                line_lower.startswith(kw)
                for kw in ["minutes", "discussion", "present",
                           "attendee", "resolution"]
            ):
                break
            if re.match(r"^(\d+[\.\)]|[-•*])\s+", line_stripped):
                item = re.sub(r"^(\d+[\.\)]|[-•*])\s+", "", line_stripped)
                if item:
                    agenda.append(item)
            elif len(line_stripped) > 5:
                agenda.append(line_stripped)

    return agenda[:20]


def extract_decisions(raw_text: str) -> list:
    """Extracts decisions and resolutions from the document text."""
    decisions = []
    lines = raw_text.splitlines()

    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if any(trigger in line_lower for trigger in DECISION_TRIGGERS):
            inline = re.sub(
                r"(?i)(resolved|agreed|decided|approved|decision|resolution)"
                r"[:\s]*", "", line,
            ).strip()
            if inline and len(inline) > 10:
                decisions.append(inline)
            elif i + 1 < len(lines) and lines[i + 1].strip():
                decisions.append(lines[i + 1].strip())

    return list(dict.fromkeys(decisions))[:15]


def extract_action_items(raw_text: str) -> list:
    """Extracts action items and tasks from the document text."""
    actions = []
    lines = raw_text.splitlines()

    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if any(trigger in line_lower for trigger in ACTION_TRIGGERS):
            inline = re.sub(
                r"(?i)(action item|action required|action|task|to do|follow up)"
                r"[:\s]*", "", line,
            ).strip()
            if inline and len(inline) > 5:
                actions.append(inline)
            elif i + 1 < len(lines) and lines[i + 1].strip():
                actions.append(lines[i + 1].strip())

    return list(dict.fromkeys(actions))[:20]


def extract_metadata(raw_text: str, filename: str = "") -> dict:
    """
    Master function — runs all extractors and returns
    a clean metadata dict ready to be stored in PostgreSQL.
    """
    logger.info(f"Extracting metadata from: {filename}")

    meeting_date = parse_date(raw_text)
    attendees = extract_attendees(raw_text)
    department = extract_department(raw_text, filename)
    agenda_items = extract_agenda_items(raw_text)
    decisions = extract_decisions(raw_text)
    action_items = extract_action_items(raw_text)

    metadata = {
        "meeting_date": meeting_date,
        "attendees": attendees,
        "department": department,
        "agenda_items": agenda_items,
        "decisions_made": decisions,
        "action_items": action_items,
    }

    logger.info(
        f"Metadata extracted | date={meeting_date} | "
        f"attendees={len(attendees)} | agenda={len(agenda_items)} | "
        f"decisions={len(decisions)} | actions={len(action_items)}"
    )

    return metadata