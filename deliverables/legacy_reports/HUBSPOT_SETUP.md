# HubSpot App Setup Instructions

## Prerequisites
You need a HubSpot developer account with API access.

## Setup Steps

### 1. Authenticate with HubSpot CLI
```bash
cd hubspot-app
hs auth
```

This will open your browser to authenticate with HubSpot.

### 2. Create the CapcoDemo App
```bash
hs create app CapcoDemo
```

Select options:
- **App type**: Private app (for development)
- **Scopes needed**:
  - `crm.objects.contacts.read`
  - `crm.objects.contacts.write`
  - `crm.schemas.contacts.read`

### 3. Get Your Access Token
1. Log into HubSpot: https://app.hubspot.com/
2. Go to Settings → Integrations → Private Apps
3. Find "CapcoDemo"
4. Copy the access token
5. Update `.env` file:
   ```bash
   HUBSPOT_ACCESS_TOKEN=your_token_here
   ```

### 4. Create App Extensions (Optional)

#### Create a CRM Card
```bash
hs create card
```

Options:
- **Card name**: Client Insights Card
- **Card type**: Contact card
- **Data fetch URL**: http://localhost:8000/api/v1/hubspot/contact-card

#### Create Custom Properties
```bash
hs create property
```

Add custom properties:
- **RM Priority Score** (number)
- **Last Rebalancing Date** (date)
- **Risk Profile** (dropdown: Conservative, Moderate, Aggressive)
- **Shariah Compliant** (boolean)

### 5. Deploy to HubSpot
```bash
cd hubspot-app
hs project upload
```

## Project Structure

```
hubspot-app/
├── src/
│   └── app/
│       ├── app.json          # App configuration
│       └── extensions/
│           └── client-insights-card.json
```

## Testing

Once configured, test the integration:

```bash
# In RM Workbench backend
curl http://localhost:8000/api/v1/clients/sync-to-hubspot
```

## Development Workflow

1. Make changes to HubSpot app code
2. Test locally: `hs project dev`
3. Deploy: `hs project upload`
4. View in HubSpot portal

## Useful Commands

```bash
# View current authentication
hs accounts list

# Switch accounts
hs accounts use

# View logs
hs logs

# Create webhook
hs create webhook

# List your apps
hs list apps
```

## Integration Points

The RM Workbench backend integrates with HubSpot via:

1. **CRM Sync** - `POST /api/v1/clients/sync-to-hubspot`
   - Syncs client data with HubSpot contacts
   - Shows old → new diff before applying

2. **Custom Cards** - Display in HubSpot contact records
   - Client priority score
   - Recent interactions
   - Portfolio summary

3. **Webhooks** - Receive updates from HubSpot
   - Contact property changes
   - New contact created
   - Update RM Workbench data

## Next Steps

After authentication:
1. Run `hs get-started` to create CapcoDemo app
2. Configure scopes and permissions
3. Copy access token to `.env`
4. Test integration with RM Workbench

## Documentation

- HubSpot CLI: https://developers.hubspot.com/docs/platform/working-with-the-cli
- Private Apps: https://developers.hubspot.com/docs/api/private-apps
- CRM Cards: https://developers.hubspot.com/docs/platform/crm-cards
- Custom Objects: https://developers.hubspot.com/docs/api/crm/crm-custom-objects
