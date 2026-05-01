# SLyK-View

**Executive Security Dashboard for NIST 800-53 Compliance**

SLyK-View is a modern, shareable React dashboard that provides a visual interface for the SLyK-53 Bedrock Agent. It's designed to be deployed across multiple AWS tenants, allowing ISSOs to share the same security tooling.

![SLyK-View Dashboard](./docs/dashboard-preview.png)

## Features

### 🎯 Dashboard
- Real-time compliance score gauge with animated visualization
- Compliance trend charts (7-day history)
- Control status cards with pass/fail/warning indicators
- Live alerts feed with severity badges

### 🛡️ Security Controls
- Detailed view for each NIST 800-53 control:
  - **AC-2**: Account Management
  - **AU-6**: Audit Review & Analysis
  - **CM-6**: Configuration Settings
  - **SI-2**: Flaw Remediation
  - **RA-5**: Vulnerability Scanning
- One-click assessment execution
- Remediation playbook generation

### 💬 Ask SLyK
- Embedded chat interface with the Bedrock Agent
- Suggested prompts for common tasks
- Markdown rendering for formatted responses
- Typing indicators and message history

### 📊 Resource Inventory
- AWS resource inventory with security posture
- Filter by resource type (EC2, S3, IAM, RDS)
- Compliance status per resource
- Search and filter capabilities

### 📄 Reports
- Generate compliance reports on-demand
- Schedule automated daily/weekly reports
- Export to PDF
- Email delivery via SNS

### ⚙️ Settings
- Multi-tenant configuration
- Shareable config for other ISSOs
- Notification preferences
- Bedrock Agent connection settings

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   CloudFront    │────▶│    S3 Bucket    │     │    Cognito      │
│   Distribution  │     │  (Static Host)  │     │   User Pool     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                                               │
         │                                               ▼
         │                                      ┌─────────────────┐
         │                                      │    Cognito      │
         │                                      │  Identity Pool  │
         │                                      └─────────────────┘
         │                                               │
         ▼                                               ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React App     │────▶│  Bedrock Agent  │────▶│     Lambda      │
│   (Browser)     │     │   (SLyK-53)     │     │   Functions     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Deployment

### Prerequisites
- AWS Account with admin access
- Node.js 18+
- Python 3.9+
- AWS CLI configured

### Quick Deploy (CloudShell)

```bash
# Clone the repo
git clone https://github.com/iperry5224/TestZippr.git
cd TestZippr/slyk-view

# Deploy infrastructure
python3 deploy_slyk_view.py

# Build React app
npm install
npm run build

# Upload to S3
aws s3 sync dist/ s3://slyk-view-ACCOUNT_ID-REGION/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id DIST_ID --paths "/*"
```

### Manual Deployment

1. **Deploy Infrastructure**
   ```bash
   python3 deploy_slyk_view.py
   ```

2. **Configure React App**
   Update `src/aws-config.json` with your values:
   ```json
   {
     "region": "us-east-1",
     "userPoolId": "us-east-1_XXXXXXX",
     "userPoolClientId": "XXXXXXXXXXXXXXXX",
     "identityPoolId": "us-east-1:XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
     "agentId": "XXXXXXXXXX",
     "agentAliasId": "XXXXXXXXXX"
   }
   ```

3. **Build and Deploy**
   ```bash
   npm install
   npm run build
   aws s3 sync dist/ s3://YOUR_BUCKET/ --delete
   ```

## Sharing with Other ISSOs

SLyK-View is designed to be deployed in multiple AWS tenants:

1. **Share the Code**
   - Share this repository or the `slyk-view` folder

2. **Each ISSO Deploys Their Own**
   - Run `deploy_slyk_view.py` in their AWS account
   - Run `deploy_slyk.py` to create their Bedrock Agent
   - Update Settings with their Agent ID

3. **Configuration Export**
   - Use Settings → "Copy Config" to export tenant configuration
   - Share with team members for consistent setup

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **Recharts** - Data visualization
- **Lucide React** - Icons
- **AWS SDK v3** - AWS integration

## Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Security

- **Authentication**: AWS Cognito User Pools
- **Authorization**: Cognito Identity Pools with IAM roles
- **Transport**: HTTPS via CloudFront
- **Storage**: S3 with blocked public access

## Cost Estimate

| Service | Monthly Cost |
|---------|-------------|
| CloudFront | ~$1-5 (depending on traffic) |
| S3 | ~$0.50 |
| Cognito | Free tier (50,000 MAU) |
| **Total** | **~$2-6/month** |

## License

Internal use only - NOAA NESDIS

## Support

Contact: ira.perry@noaa.gov

---

**Part of the GRCP Platform**
- SAELAR-53: Security Assessment
- SOPRA: Security Operations
- SLyK-53: AI Security Assistant
- **SLyK-View**: Security Dashboard
