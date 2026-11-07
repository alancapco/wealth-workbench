"""
HubSpot CRM Integration Service
Syncs RM Workbench client data with HubSpot contacts
"""
from typing import Dict, List, Optional
from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInput, ApiException
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class CRMService:
    def __init__(self):
        self.client = HubSpot(access_token=settings.HUBSPOT_ACCESS_TOKEN)
        logger.info("HubSpot CRM service initialized")

    async def find_contact_by_email(self, email: str) -> Optional[Dict]:
        """Find a contact by email address"""
        try:
            search_request = {
                "filterGroups": [{
                    "filters": [{
                        "propertyName": "email",
                        "operator": "EQ",
                        "value": email
                    }]
                }],
                "properties": ["firstname", "lastname", "email", "phone"],
                "limit": 1
            }

            response = self.client.crm.contacts.search_api.do_search(
                public_object_search_request=search_request
            )

            if response.results:
                return {
                    "id": response.results[0].id,
                    "properties": response.results[0].properties
                }
            return None

        except Exception as e:
            logger.error(f"Error searching contact: {e}")
            return None

    async def create_contact(self, properties: Dict) -> Dict:
        """Create a new contact in HubSpot"""
        try:
            simple_public_object_input = SimplePublicObjectInput(properties=properties)

            response = self.client.crm.contacts.basic_api.create(
                simple_public_object_input=simple_public_object_input
            )

            return {
                "id": response.id,
                "properties": response.properties
            }

        except ApiException as e:
            logger.error(f"Error creating contact: {e}")
            raise

    async def update_contact(self, contact_id: str, properties: Dict) -> Dict:
        """Update an existing contact"""
        try:
            simple_public_object_input = SimplePublicObjectInput(properties=properties)

            response = self.client.crm.contacts.basic_api.update(
                contact_id=contact_id,
                simple_public_object_input=simple_public_object_input
            )

            return {
                "id": response.id,
                "properties": response.properties
            }

        except ApiException as e:
            logger.error(f"Error updating contact: {e}")
            raise

    async def get_contact(self, contact_id: str) -> Optional[Dict]:
        """Get a contact by ID"""
        try:
            response = self.client.crm.contacts.basic_api.get_by_id(
                contact_id=contact_id,
                properties=["firstname", "lastname", "email", "phone", "rm_aum", "rm_currency"]
            )

            return {
                "id": response.id,
                "properties": response.properties
            }

        except ApiException as e:
            logger.error(f"Error getting contact: {e}")
            return None

    async def fetch_contacts_from_hubspot(self, limit: int = 100) -> List[Dict]:
        """
        Fetch contacts from HubSpot CRM
        Returns list of contacts with relevant fields
        """
        try:
            # Use search API to get contacts
            search_request = {
                "filterGroups": [],
                "properties": [
                    "firstname", "lastname", "email", "phone",
                    "rm_aum", "rm_currency", "rm_client_type",
                    "rm_region", "rm_risk_profile", "rm_external_id"
                ],
                "limit": limit
            }

            response = self.client.crm.contacts.search_api.do_search(
                public_object_search_request=search_request
            )

            contacts = []
            for result in response.results:
                contacts.append({
                    "hubspot_id": result.id,
                    "properties": result.properties
                })

            logger.info(f"Fetched {len(contacts)} contacts from HubSpot")
            return contacts

        except Exception as e:
            logger.error(f"Error fetching contacts from HubSpot: {e}")
            return []

    async def sync_client_to_hubspot(self, client_data: Dict) -> Dict:
        """
        Sync a single client to HubSpot
        Returns: { "action": "created" | "updated", "hubspot_id": "...", "diff": {...} }
        """
        try:
            # Check if contact exists
            existing = await self.find_contact_by_email(client_data['email'])

            # Prepare HubSpot properties
            properties = {
                'firstname': client_data.get('firstname', ''),
                'lastname': client_data.get('lastname', ''),
                'email': client_data['email'],
                'phone': client_data.get('phone', ''),
                'company': client_data.get('client_type', ''),
                'city': client_data.get('region', ''),
                # Custom properties (need to be created in HubSpot first)
                'rm_external_id': client_data.get('external_id', ''),
                'rm_aum': str(client_data.get('aum', 0)),
                'rm_currency': client_data.get('currency', 'USD'),
                'rm_risk_profile': client_data.get('risk_profile', ''),
                'rm_shariah_compliant': 'Yes' if client_data.get('shariah_compliant') else 'No',
                'rm_is_family_office': 'Yes' if client_data.get('is_family_office') else 'No'
            }

            if existing:
                # Show diff
                diff = self._calculate_diff(existing['properties'], properties)

                # Update existing
                result = await self.update_contact(existing['id'], properties)

                return {
                    "action": "updated",
                    "hubspot_id": existing['id'],
                    "diff": diff
                }
            else:
                # Create new
                result = await self.create_contact(properties)

                return {
                    "action": "created",
                    "hubspot_id": result['id'],
                    "diff": {"new_contact": properties}
                }

        except Exception as e:
            logger.error(f"Error syncing client: {e}")
            raise

    def _calculate_diff(self, old_props: Dict, new_props: Dict) -> Dict:
        """Calculate what changed between old and new properties"""
        diff = {}

        for key, new_value in new_props.items():
            old_value = old_props.get(key, '')
            if str(old_value) != str(new_value):
                diff[key] = {
                    "old": old_value,
                    "new": new_value
                }

        return diff

# Singleton instance
crm_service = CRMService()
