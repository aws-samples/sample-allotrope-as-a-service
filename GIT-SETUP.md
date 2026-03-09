# Git Setup Guide for GitLab

## Initial Setup (First Time)

```bash
cd c:\app\asm2agent

# Initialize git if not already done
git init

# Add GitLab remote
git remote add origin git@ssh.gitlab.aws.dev:allotrope-as-a-service/asm-converter.git

# Check remote is set correctly
git remote -v
```

## Prepare Files for Commit

### 1. Check what will be committed
```bash
git status
```

### 2. Review .gitignore
Make sure sensitive files are excluded:
- demo-outputs/
- output/
- *.pem, *.key
- .aws/
- node_modules/
- cdk.out/

### 3. Stage files
```bash
# Add all files (respects .gitignore)
git add .

# Or add specific directories
git add services/
git add dashboard/
git add docs/
git add README.md
git add MEMORY.md
git add .gitignore
```

## Commit and Push

```bash
# Create initial commit
git commit -m "Initial commit: ASM Transformation Service

- ATaaS: AI-powered conversion with Bedrock Claude
- DVaaS: Validation and certification service
- Multi-Instrument: 31+ instruments via allotropy
- Unified Converter: Intelligent routing
- Dashboard: React UI with AWS Cloudscape
- Documentation: Manifest schema, validation analysis"

# Push to GitLab
git push -u origin main

# Or if using master branch
git push -u origin master
```

## Verify Push

```bash
# Check remote status
git remote show origin

# View commit history
git log --oneline
```

## Monorepo Structure

Your repo will have:
```
asm-converter/
├── services/              # Backend services (Lambda)
├── dashboard/             # Frontend (React)
├── docs/                  # Documentation
├── demo-samples/          # Sample files
├── README.md             # Main readme
├── MEMORY.md             # Project history
└── .gitignore            # Git ignore rules
```

## Branch Strategy (Optional)

```bash
# Create development branch
git checkout -b develop

# Create feature branches
git checkout -b feature/new-instrument-support

# Merge back to main
git checkout main
git merge develop
```

## Common Issues

### Issue: Permission denied (publickey)
**Solution**: Check SSH key is added to GitLab
```bash
ssh -T git@ssh.gitlab.aws.dev
```

### Issue: Remote already exists
**Solution**: Update remote URL
```bash
git remote set-url origin git@ssh.gitlab.aws.dev:allotrope-as-a-service/asm-converter.git
```

### Issue: Large files
**Solution**: Check .gitignore excludes output directories
```bash
git rm --cached -r demo-outputs/
git rm --cached -r output/
```

## Next Steps After Push

1. ✅ Verify files on GitLab web interface
2. ✅ Add README badges (build status, license)
3. ✅ Set up CI/CD pipeline (optional)
4. ✅ Add collaborators
5. ✅ Create issues/milestones
6. ✅ Add LICENSE file
