"""
HubSpot CRM Integration Service
"""
from hubspot import HubSpot
from hubspot.crm.contacts import ApiException
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class CRMService:
    def __init__(self):
        self.client = HubSpot(access_token=settings.HUBSPOT_ACCESS_TOKEN)

    async def sync_client(self, client_data: dict) -> dict:
        """
        Sync client data to HubSpot
        Returns old -> new diff for review
        """
        try:
            # Search for existing contact
            email = client_data.get("email")
            if not email:
                return {"error": "Email required for CRM sync"}

            # Get existing contact
            try:
                existing = self.client.crm.contacts.basic_api.get_by_id(
                    contact_id=email,
                    properties=["firstname", "lastname", "email", "phone", "notes"]
                )
                old_values = existing.properties
            except ApiException:
                old_values = {}

            # Prepare update
            new_values = {
                "firstname": client_data.get("first_name", ""),
                "lastname": client_data.get("last_name", ""),
                "email": email,
                "phone": client_data.get("phone", ""),
            }

            # Add custom properties
            if "preferences" in client_data:
                new_values["rm_preferences"] = str(client_data["preferences"])

            # Generate diff
            diff = []
            for key, new_val in new_values.items():
                old_val = old_values.get(key, "")
                if old_val != new_val:
                    diff.append({
                        "field": key,
                        "old": old_val,
                        "new": new_val
                    })

            return {
                "diff": diff,
                "status": "pending_approval",
                "contact_id": email
            }

        except Exception as e:
            logger.error(f"Error syncing to HubSpot: {e}")
            return {"error": str(e)}

    async def execute_sync(self, contact_id: str, updates: dict) -> dict:
        """
        Execute approved CRM sync
        """
        try:
            # Update or create contact
            simple_public_object_input = {
                "properties": updates
            }

            try:
                result = self.client.crm.contacts.basic_api.update(
                    contact_id=contact_id,
                    simple_public_object_input=simple_public_object_input
                )
                status = "updated"
            except ApiException:
                result = self.client.crm.contacts.basic_api.create(
                    simple_public_object_input=simple_public_object_input
                )
                status = "created"

            logger.info(f"CRM sync {status} for {contact_id}")
            return {
                "status": status,
                "contact_id": contact_id,
                "timestamp": result.updated_at if hasattr(result, 'updated_at') else None
            }

        except Exception as e:
            logger.error(f"Error executing CRM sync: {e}")
            return {"status": "failed", "error": str(e)}

# Singleton instance
crm_service = CRMService()
