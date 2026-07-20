from pathlib import Path
from datetime import datetime
import secrets
import frontmatter

from .enums import VaultDirectory
from .schemas import ConversationSession, Message, Goal, Journal, Reminder


class Vault:
    """
    Source of truth for everything stored in Fumi's vault.
    """

    def __init__(self, root: str | Path = "vault"):
        self.root = Path(root)

        self.conversations = self.root / "conversations"
        self.goals = self.root / "goals"
        self.journals = self.root / "journals"
        self.memories = self.root / "memories"
        self.preferences = self.root / "preferences"
        self.people = self.root / "people"
        self.projects = self.root / "projects"
        self.daily = self.root / "daily"
        self.archive = self.root / "archive"
        self.reminders = self.root / "reminders"

        self._ensure_exists()

        self.sessions: dict[str, Path] = {}
        self._load_sessions()

        self.goals_map: dict[str, Path] = {}
        self._load_goals()

        self.journals_map: dict[str, Path] = {}
        self._load_journals()

        self.reminders_map: dict[str, Path] = {}
        self._load_reminders()


    @property
    def directories(self) -> dict[str, Path]:
        return {
            "conversations": self.conversations,
            "goals": self.goals,
            "journals": self.journals,
            "memories": self.memories,
            "preferences": self.preferences,
            "people": self.people,
            "projects": self.projects,
            "daily": self.daily,
            "archive": self.archive,
            "reminders": self.reminders,
        }

    def _ensure_exists(self):
        """
        Create the vault folders if they don't already exist.
        """

        for directory in self.directories.values():
            directory.mkdir(parents=True, exist_ok=True)

    def _load_sessions(self):
        """
        Scan conversations directory and populate the sessions map.
        """
        if not self.conversations.exists():
            return
        for path in self.conversations.glob("*.md"):
            name = path.stem
            if "_" in name:
                session_id = name.split("_")[-1]
                self.sessions[session_id] = path

    def _load_goals(self):
        """
        Scan goals directory and populate the goals map.
        """
        if not self.goals.exists():
            return
        for path in self.goals.glob("*.md"):
            self.goals_map[path.stem] = path

    def _load_journals(self):
        """
        Scan journals directory and populate the journals map.
        """
        if not self.journals.exists():
            return
        for path in self.journals.glob("*.md"):
            self.journals_map[path.stem] = path



    def create_session(self, model: str) -> ConversationSession:
        """
        Create a new ConversationSession and write its Markdown file.
        """
        session_id = secrets.token_hex(3)
        now = datetime.now()
        session = ConversationSession(
            id=session_id,
            created=now,
            updated=now,
            title="New Conversation",
            model=model,
            message_count=0,
        )

        date_str = now.strftime("%Y-%m-%d")
        filename = f"{date_str}_{session_id}.md"
        path = self.conversations / filename

        # Prepare YAML frontmatter metadata
        post = frontmatter.Post(
            content="",
            id=session.id,
            created=session.created,
            updated=session.updated,
            title=session.title,
            model=session.model,
            message_count=session.message_count,
        )

        with open(path, "w", encoding="utf-8") as f:
            frontmatter.dump(post, f)

        self.sessions[session_id] = path
        return session

    def append_message(self, session_id: str, message: Message):
        """
        Append a message to the session's Markdown file.
        """
        path = self.get_session_path(session_id)
        if not path or not path.exists():
            raise FileNotFoundError(f"Session {session_id} not found.")

        # Load the post using python-frontmatter
        post = frontmatter.load(path)

        # Append role header and content
        role_header = "## User" if message.role.lower() == "user" else "## Fumi"
        
        current_content = post.content.strip()
        new_block = f"{role_header}\n\n{message.content}"
        
        if current_content:
            post.content = f"{current_content}\n\n{new_block}"
        else:
            post.content = new_block

        # Update metadata
        post.metadata["message_count"] = post.metadata.get("message_count", 0) + 1
        post.metadata["updated"] = datetime.now()

        # Rewrite Markdown file
        with open(path, "w", encoding="utf-8") as f:
            frontmatter.dump(post, f)

    def get_session_path(self, session_id: str) -> Path | None:
        """
        Get the file path for a session by its ID.
        """
        return self.sessions.get(session_id)

    def load_session(self, session_id: str) -> tuple[ConversationSession, list[Message]]:
        """
        Load a ConversationSession and its messages from the Markdown file.
        """
        path = self.get_session_path(session_id)
        if not path or not path.exists():
            raise FileNotFoundError(f"Session {session_id} not found.")

        post = frontmatter.load(path)

        # Parse timestamps safely
        created = post.metadata.get("created")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        elif not isinstance(created, datetime):
            created = datetime.now()

        updated = post.metadata.get("updated")
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated)
        elif not isinstance(updated, datetime):
            updated = datetime.now()

        session = ConversationSession(
            id=post.metadata.get("id", session_id),
            created=created,
            updated=updated,
            title=post.metadata.get("title", "New Conversation"),
            model=post.metadata.get("model", ""),
            message_count=int(post.metadata.get("message_count", 0)),
        )

        messages = self._parse_messages(post.content)
        return session, messages

    def list_sessions(self) -> list[ConversationSession]:
        """
        List all ConversationSessions in the vault, sorted by updated time descending.
        """
        sessions_list = []
        for session_id in list(self.sessions.keys()):
            try:
                session, _ = self.load_session(session_id)
                sessions_list.append(session)
            except Exception:
                continue
        
        sessions_list.sort(key=lambda s: s.updated, reverse=True)
        return sessions_list

    def _parse_messages(self, content: str) -> list[Message]:
        """
        Parse Markdown content to extract a list of Message objects.
        """
        import re
        pattern = re.compile(
            r"^##\s+(User|Fumi)\b(.*?)(?=\n##\s+(?:User|Fumi)\b|\Z)",
            re.MULTILINE | re.DOTALL
        )
        messages = []
        for match in pattern.finditer(content):
            role = match.group(1).lower()
            body = match.group(2).strip()
            messages.append(Message(role=role, content=body))
        return messages

    def create_goal(self, title: str, status: str, priority: str, description: str) -> Goal:
        """
        Create a new goal and write its Markdown file.
        """
        goal_id = secrets.token_hex(3)
        now = datetime.now()
        goal = Goal(
            id=goal_id,
            title=title,
            status=status,
            priority=priority,
            created=now,
            updated=now,
            description=description,
        )

        path = self.goals / f"{goal_id}.md"

        # Prepare YAML frontmatter metadata
        post = frontmatter.Post(
            content=description,
            id=goal.id,
            title=goal.title,
            status=goal.status,
            priority=goal.priority,
            created=goal.created,
            updated=goal.updated,
        )

        with open(path, "w", encoding="utf-8") as f:
            frontmatter.dump(post, f)

        self.goals_map[goal_id] = path
        return goal

    def _parse_goal(self, path: Path) -> Goal:
        """
        Helper to parse a Goal object from its markdown file path.
        """
        post = frontmatter.load(path)

        created = post.metadata.get("created")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        elif not isinstance(created, datetime):
            created = datetime.now()

        updated = post.metadata.get("updated")
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated)
        elif not isinstance(updated, datetime):
            updated = datetime.now()

        return Goal(
            id=post.metadata.get("id", path.stem),
            title=post.metadata.get("title", ""),
            status=post.metadata.get("status", ""),
            priority=post.metadata.get("priority", ""),
            created=created,
            updated=updated,
            description=post.content,
        )

    def update_goal(
        self,
        goal_id: str,
        title: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        description: str | None = None,
    ) -> Goal:
        """
        Update an existing goal.
        """
        path = self.goals_map.get(goal_id)
        if not path or not path.exists():
            raise FileNotFoundError(f"Goal {goal_id} not found.")

        post = frontmatter.load(path)

        if title is not None:
            post.metadata["title"] = title
        if status is not None:
            post.metadata["status"] = status
        if priority is not None:
            post.metadata["priority"] = priority
        if description is not None:
            post.content = description

        post.metadata["updated"] = datetime.now()

        with open(path, "w", encoding="utf-8") as f:
            frontmatter.dump(post, f)

        return self._parse_goal(path)

    def complete_goal(self, goal_id: str) -> Goal:
        """
        Mark a goal as completed.
        """
        return self.update_goal(goal_id, status="completed")

    def delete_goal(self, goal_id: str) -> bool:
        """
        Delete a goal.
        """
        path = self.goals_map.get(goal_id)
        if not path or not path.exists():
            return False

        path.unlink()
        self.goals_map.pop(goal_id, None)
        return True

    def list_goals(self) -> list[Goal]:
        """
        List all goals in the vault, sorted by updated time descending.
        """
        goals_list = []
        for goal_id in list(self.goals_map.keys()):
            try:
                path = self.goals_map[goal_id]
                goals_list.append(self._parse_goal(path))
            except Exception:
                continue
        goals_list.sort(key=lambda g: g.updated, reverse=True)
        return goals_list

    def create_journal(self, content: str) -> Journal:
        """
        Create a new journal entry and write its Markdown file.
        """
        journal_id = secrets.token_hex(3)
        now = datetime.now()
        journal = Journal(
            id=journal_id,
            created=now,
            updated=now,
            content=content,
        )

        path = self.journals / f"{journal_id}.md"

        # Prepare YAML frontmatter metadata
        post = frontmatter.Post(
            content=content,
            id=journal.id,
            created=journal.created,
            updated=journal.updated,
        )

        with open(path, "w", encoding="utf-8") as f:
            frontmatter.dump(post, f)

        self.journals_map[journal_id] = path
        return journal

    def load_journal(self, journal_id: str) -> Journal:
        """
        Load a Journal entry by its ID.
        """
        path = self.journals_map.get(journal_id)
        if not path or not path.exists():
            raise FileNotFoundError(f"Journal {journal_id} not found.")

        post = frontmatter.load(path)

        created = post.metadata.get("created")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        elif not isinstance(created, datetime):
            created = datetime.now()

        updated = post.metadata.get("updated")
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated)
        elif not isinstance(updated, datetime):
            updated = datetime.now()

        return Journal(
            id=post.metadata.get("id", journal_id),
            created=created,
            updated=updated,
            content=post.content,
        )

    def list_journals(self) -> list[Journal]:
        """
        List all journals in the vault, sorted by created time descending.
        """
        journals_list = []
        for journal_id in list(self.journals_map.keys()):
            try:
                journals_list.append(self.load_journal(journal_id))
            except Exception:
                continue
        journals_list.sort(key=lambda j: j.created, reverse=True)
        return journals_list

    def _load_reminders(self):
        """
        Scan reminders directory and populate the reminders map.
        """
        if not self.reminders.exists():
            return
        for path in self.reminders.glob("*.md"):
            self.reminders_map[path.stem] = path

    def create_reminder(self, text: str, due_time: datetime) -> Reminder:
        """
        Create a new reminder and write its Markdown file.
        """
        reminder_id = secrets.token_hex(4)
        now = datetime.now()
        reminder = Reminder(
            id=reminder_id,
            text=text,
            due_time=due_time,
            status="pending",
            created_at=now,
        )

        path = self.reminders / f"{reminder_id}.md"

        post = frontmatter.Post(
            content=text,
            id=reminder.id,
            text=reminder.text,
            due_time=reminder.due_time.isoformat(),
            status=reminder.status,
            created_at=reminder.created_at.isoformat(),
        )

        with open(path, "w", encoding="utf-8") as f:
            frontmatter.dump(post, f)

        self.reminders_map[reminder_id] = path
        return reminder

    def _parse_reminder(self, path: Path) -> Reminder:
        """
        Helper to parse a Reminder object from its markdown file path.
        """
        post = frontmatter.load(path)

        due_time = post.metadata.get("due_time")
        if isinstance(due_time, str):
            due_time = datetime.fromisoformat(due_time)
        elif not isinstance(due_time, datetime):
            due_time = datetime.now()

        created_at = post.metadata.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif not isinstance(created_at, datetime):
            created_at = datetime.now()

        return Reminder(
            id=post.metadata.get("id", path.stem),
            text=post.metadata.get("text", post.content),
            due_time=due_time,
            status=post.metadata.get("status", "pending"),
            created_at=created_at,
        )

    def update_reminder(
        self,
        reminder_id: str,
        text: str | None = None,
        due_time: datetime | None = None,
        status: str | None = None,
    ) -> Reminder:
        """
        Update an existing reminder.
        """
        path = self.reminders_map.get(reminder_id)
        if not path or not path.exists():
            raise FileNotFoundError(f"Reminder {reminder_id} not found.")

        post = frontmatter.load(path)

        if text is not None:
            post.metadata["text"] = text
            post.content = text
        if due_time is not None:
            post.metadata["due_time"] = due_time.isoformat()
        if status is not None:
            post.metadata["status"] = status

        with open(path, "w", encoding="utf-8") as f:
            frontmatter.dump(post, f)

        return self._parse_reminder(path)

    def delete_reminder(self, reminder_id: str) -> bool:
        """
        Delete a reminder.
        """
        path = self.reminders_map.get(reminder_id)
        if not path or not path.exists():
            return False

        path.unlink()
        self.reminders_map.pop(reminder_id, None)
        return True

    def list_reminders(self) -> list[Reminder]:
        """
        List all reminders in the vault, sorted by due time.
        """
        reminders_list = []
        for r_id in list(self.reminders_map.keys()):
            try:
                path = self.reminders_map[r_id]
                reminders_list.append(self._parse_reminder(path))
            except Exception:
                continue
        reminders_list.sort(key=lambda r: r.due_time)
        return reminders_list

    def create_checkin(self, message: str) -> dict:
        """
        Create a new check-in notification file in vault/daily.
        """
        checkin_id = secrets.token_hex(4)
        now = datetime.now()
        path = self.daily / f"checkin_{checkin_id}.md"

        post = frontmatter.Post(
            content=message,
            id=checkin_id,
            timestamp=now.isoformat(),
            read=False,
        )

        with open(path, "w", encoding="utf-8") as f:
            frontmatter.dump(post, f)

        return {
            "id": checkin_id,
            "message": message,
            "timestamp": now.isoformat(),
            "read": False,
        }

    def list_pending_checkins(self) -> list[dict]:
        """
        List all unread check-in notifications.
        """
        if not self.daily.exists():
            return []
        pending = []
        for path in self.daily.glob("checkin_*.md"):
            try:
                post = frontmatter.load(path)
                if not post.metadata.get("read", False):
                    pending.append({
                        "id": post.metadata.get("id", path.stem.replace("checkin_", "")),
                        "message": post.content,
                        "timestamp": post.metadata.get("timestamp"),
                        "read": False,
                    })
            except Exception:
                continue
        pending.sort(key=lambda x: x["timestamp"] or "")
        return pending

    def mark_checkin_as_read(self, checkin_id: str) -> bool:
        """
        Mark a specific check-in notification as read.
        """
        path = self.daily / f"checkin_{checkin_id}.md"
        if not path.exists():
            for p in self.daily.glob("checkin_*.md"):
                try:
                    post = frontmatter.load(p)
                    if post.metadata.get("id") == checkin_id:
                        path = p
                        break
                except Exception:
                    continue

        if not path.exists():
            return False

        try:
            post = frontmatter.load(path)
            post.metadata["read"] = True
            with open(path, "w", encoding="utf-8") as f:
                frontmatter.dump(post, f)
            return True
        except Exception:
            return False