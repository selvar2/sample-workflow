# Setting Up GitHub Codespaces Secrets

To ensure your dev container has access to ServiceNow and AWS credentials, you need to set up GitHub Codespaces secrets.

## Step 1: Access Repository Settings

1. Go to your GitHub repository: `https://github.com/selvar2/sample-workflow`
2. Click on **Settings** (top menu)
3. In the left sidebar, scroll down to **Secrets and variables**
4. Click on **Codespaces**

## Step 2: Add Secrets

Click **New repository secret** and add the following secrets:

### ServiceNow Secrets

1. **SERVICENOW_INSTANCE_URL**
   - Value: `https://dev282453.service-now.com` (your instance URL)

2. **SERVICENOW_USERNAME**
   - Value: `admin` (your ServiceNow username)

3. **SERVICENOW_PASSWORD**
   - Value: Your ServiceNow password

### AWS Secrets

4. **AWS_ACCESS_KEY_ID**
   - Value: Your AWS access key ID

5. **AWS_SECRET_ACCESS_KEY**
   - Value: Your AWS secret access key

## Step 3: Rebuild Your Codespace

After adding the secrets:

1. **If you already have a codespace open:**
   - Press `F1` or `Cmd/Ctrl + Shift + P`
   - Type: "Codespaces: Rebuild Container"
   - Press Enter

2. **If creating a new codespace:**
   - The secrets will be automatically available
   - Just create the codespace normally

## Step 4: Verify Setup

Once your codespace is ready:

```bash
# Check that environment variables are set
echo $SERVICENOW_INSTANCE_URL
echo $SERVICENOW_USERNAME
echo $AWS_DEFAULT_REGION

# Check AWS credentials
aws configure list

# Activate the environment
activate-sn

# Test ServiceNow connection
python create_incident.py
```

## Security Notes

- ✅ Secrets are encrypted and only accessible to your codespaces
- ✅ Secrets are not visible in logs or terminal output
- ✅ Each secret is stored securely by GitHub
- ⚠️ Never commit credentials to your repository
- ⚠️ Use `.env` files only for local development (not committed to git)

## Alternative: Using .env File (Local Only)

If you're running locally (not in Codespaces), you can use a `.env` file:

```bash
cd /workspaces/sample-workflow/servicenow-mcp
cat > .env << EOF
SERVICENOW_INSTANCE_URL=https://dev282453.service-now.com
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=your-password
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=us-east-1
EOF
```

**Important:** Never commit the `.env` file to git! It's already in `.gitignore`.

## Troubleshooting

### Secrets Not Available
- Make sure you've added them in **Codespaces** section, not **Actions** secrets
- Rebuild the container after adding secrets

### AWS Credentials Not Working
- Verify the access key and secret key are correct
- Check that your AWS user has the necessary permissions for Redshift

### ServiceNow Connection Fails
- Verify the instance URL is correct (include `https://`)
- Check that your username and password are correct
- Ensure your ServiceNow instance is accessible
