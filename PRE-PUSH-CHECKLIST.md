# Pre-Push Checklist

## ✅ Files to Include

### Core Services
- [ ] `services/ataas/` - AI-powered transformation
- [ ] `services/dvaas/` - Validation service
- [ ] `services/multi-instrument/` - Allotropy converters
- [ ] `services/unified-converter/` - Intelligent routing
- [ ] `services/deploy_services.py` - CDK deployment
- [ ] `services/cdk.json` - CDK config
- [ ] `services/requirements.txt` - Python dependencies

### Dashboard (Optional)
- [ ] `dashboard/src/` - React components
- [ ] `dashboard/public/` - Static assets
- [ ] `dashboard/deploy-stack.py` - Dashboard CDK
- [ ] `dashboard/package.json` - Node dependencies
- [ ] `dashboard/vite.config.js` - Build config

### Documentation
- [ ] `README.md` - Main project readme
- [ ] `MEMORY.md` - Project history
- [ ] `docs/MANIFEST-SCHEMA.md` - Manifest specification
- [ ] `docs/CUSTOMER-VALIDATION-ANALYSIS.md` - Validation analysis
- [ ] `docs/SUPPORTED-INSTRUMENTS.md` - Instrument list
- [ ] `.gitignore` - Git ignore rules
- [ ] `GIT-SETUP.md` - This checklist

### Sample Files (Optional)
- [ ] `demo-samples/SampleResults2025-November.csv` - Sample CSV
- [ ] `demo-samples/SampleResults2025-November-1.json` - Sample ASM
- [ ] `nova_flex2_converter.py` - Standalone converter example

## ❌ Files to EXCLUDE

### Sensitive Data
- [ ] ❌ AWS credentials (*.pem, *.key)
- [ ] ❌ `.aws/` directory
- [ ] ❌ Environment variables with secrets

### Build Artifacts
- [ ] ❌ `cdk.out/` - CDK build output
- [ ] ❌ `node_modules/` - Node dependencies
- [ ] ❌ `__pycache__/` - Python cache
- [ ] ❌ `dist/` - Build output

### Output Files
- [ ] ❌ `demo-outputs/` - Generated files
- [ ] ❌ `output/` - Test outputs
- [ ] ❌ `tmp/` - Temporary files
- [ ] ❌ `*.log` - Log files

## 🔍 Pre-Push Checks

### 1. Security Check
```bash
# Search for potential secrets
grep -r "aws_access_key" .
grep -r "aws_secret" .
grep -r "password" .
```

### 2. File Size Check
```bash
# Check for large files (>10MB)
find . -type f -size +10M
```

### 3. Test .gitignore
```bash
# Verify excluded files
git status --ignored
```

### 4. Verify Structure
```bash
# List directory structure
tree -L 2 -I 'node_modules|cdk.out|__pycache__|dist'
```

## 📝 Commit Message Template

```
[Type]: Brief description

- Detailed change 1
- Detailed change 2
- Detailed change 3

[Type] can be:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- refactor: Code refactoring
- test: Tests
- chore: Maintenance
```

## 🚀 Ready to Push?

Once all checks pass:

```bash
git add .
git commit -m "Initial commit: ASM Transformation Service"
git push -u origin main
```

## ✅ Post-Push Verification

1. [ ] Visit GitLab repo URL
2. [ ] Verify all files are present
3. [ ] Check README renders correctly
4. [ ] Verify no sensitive data visible
5. [ ] Test clone from GitLab
6. [ ] Update repo description on GitLab
7. [ ] Add topics/tags on GitLab
8. [ ] Set repo visibility (private/internal/public)

## 📧 Share with Team

After successful push:
- [ ] Share GitLab URL with team
- [ ] Add collaborators
- [ ] Create initial issues/milestones
- [ ] Set up branch protection rules
- [ ] Configure CI/CD (if needed)
