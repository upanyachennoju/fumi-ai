from packages.knowledge.vault import Vault


class CheckInManager:
    """
    Manages notifications and check-in messages inside the Vault's daily directory.
    """

    def __init__(self, vault: Vault):
        self.vault = vault

    def create_checkin(self, message: str) -> dict:
        """
        Creates a new unread check-in notification.
        """
        return self.vault.create_checkin(message)

    def get_pending_checkins(self) -> list[dict]:
        """
        Retrieves all unread check-in notifications.
        """
        return self.vault.list_pending_checkins()

    def mark_as_read(self, checkin_id: str) -> bool:
        """
        Marks a specific check-in as read.
        """
        return self.vault.mark_checkin_as_read(checkin_id)
