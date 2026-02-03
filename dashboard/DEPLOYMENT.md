# ASM Dashboard Deployment Guide

Deploy the combined ASM Dashboard (Use Case 1 + Use Case 2) to AWS S3 as a static website.

## Prerequisites

1. **AWS CLI** configured with credentials
2. **AWS CDK** installed: `npm install -g aws-cdk`
3. **Node.js 18+**
4. **Python 3.9+** (for CDK)

## Quick Deploy

### Option 1: Automated (Recommended)

**Windows**:
```bash
cd dashboard
npm install
deploy.bat
```

**Mac/Linux**:
```bash
cd dashboard
npm install
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Manual Steps

```bash
# 1. Install dependencies
cd dashboard
npm install

# 2. Build dashboard
npm run build

# 3. Bootstrap CDK (first time only)
cdk bootstrap

# 4. Deploy
cdk deploy --require-approval never
```

## What Gets Deployed

- **S3 Bucket**: `asm-dashboard-website`
- **CloudFront Distribution**: CDN for global access
- **Static Website**: React dashboard with both use cases

## Dashboard Features

### Use Case 2: Validation & Certification (Default Tab)
- Upload instrument files (CSV, XML, JSON)
- Convert to ASM via API
- Compare AWS ASM vs Customer ASM
- Download PDF certification reports
- Show validation improvements

### Use Case 1: Multi-Instrument Visualization
- View data from multiple instruments
- pH trends chart
- Metabolite levels chart
- Sortable data table
- Validation status badges

## Configuration

### Update API Endpoints

The dashboard uses a local proxy for development. For production:

**Edit `src/ValidationApp.jsx`**:
```javascript
const ENDPOINTS = {
  convert: 'https://your-api-gateway-url/convert',
  validate: 'https://your-api-gateway-url/validate',
  customerASM: 'https://your-s3-bucket/customer-asm.json'
}
```

### Without Proxy (Direct API Calls)

If your APIs have CORS enabled, you can call them directly:

```javascript
const ENDPOINTS = {
  convert: 'https://tqzatn5bse.execute-api.us-east-1.amazonaws.com/prod/convert',
  validate: 'https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/validate'
}
```

## Deployment Outputs

After deployment, you'll see:

```
Outputs:
ASMDashboardStack.WebsiteURL = http://asm-dashboard-website.s3-website-us-east-1.amazonaws.com
ASMDashboardStack.CloudFrontURL = https://d1234567890.cloudfront.net
ASMDashboardStack.BucketName = asm-dashboard-website
```

**Use the CloudFront URL** for production (HTTPS, global CDN).

## Update Deployment

To update the dashboard after changes:

```bash
npm run build
cdk deploy
```

Or use the deploy script again.

## Cleanup

To remove all resources:

```bash
cdk destroy
```

## Sharing with Colleagues

### 1. Share This Repository

```bash
git clone <your-repo>
cd dashboard
npm install
deploy.bat  # or deploy.sh
```

### 2. Share CloudFront URL

After deployment, share the CloudFront URL:
```
https://d1234567890.cloudfront.net
```

No authentication required - public website.

### 3. Custom Domain (Optional)

To use a custom domain:

1. Register domain in Route 53
2. Create SSL certificate in ACM
3. Update CDK stack:

```python
distribution = cloudfront.Distribution(
    self, "DashboardDistribution",
    domain_names=["dashboard.yourcompany.com"],
    certificate=certificate
)
```

## Troubleshooting

### Build Fails

```bash
# Clear cache and rebuild
rm -rf node_modules dist
npm install
npm run build
```

### Deployment Fails

```bash
# Check AWS credentials
aws sts get-caller-identity

# Bootstrap CDK (if not done)
cdk bootstrap

# Try again
cdk deploy
```

### CORS Errors

If you see CORS errors in browser console:

1. **Option A**: Use the proxy (development)
   ```bash
   python proxy.py  # Terminal 1
   npm run dev      # Terminal 2
   ```

2. **Option B**: Enable CORS on API Gateway (production)
   - Add CORS headers to Lambda responses
   - Enable CORS in API Gateway settings

### Dashboard Shows Old Version

CloudFront caches content. Invalidate cache:

```bash
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

Or wait 24 hours for cache to expire.

## Architecture

```
User Browser
    ↓
CloudFront (CDN)
    ↓
S3 Bucket (Static Website)
    ↓
React Dashboard
    ↓
API Gateway (Unified Converter, DVaaS)
    ↓
Lambda Functions
```

## Cost Estimate

- **S3**: ~$0.023/GB/month (storage) + $0.09/GB (data transfer)
- **CloudFront**: ~$0.085/GB (data transfer)
- **Estimated**: <$5/month for typical usage

## Security

- **Public Website**: No authentication required
- **API Keys**: Not exposed (server-side only)
- **HTTPS**: Enforced via CloudFront
- **CORS**: Configured for API access

## Support

For issues or questions:
1. Check CloudWatch Logs for API errors
2. Check browser console for frontend errors
3. Review CDK deployment logs
4. Contact: your-team@company.com

## Next Steps

1. ✅ Deploy dashboard
2. ✅ Share CloudFront URL with team
3. ⏳ Add authentication (AWS Cognito)
4. ⏳ Connect to real LIMS data
5. ⏳ Add custom domain
