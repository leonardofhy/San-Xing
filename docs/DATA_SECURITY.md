# 🔒 Data Security & Privacy Protection

This document outlines the measures in place to prevent accidental upload of personal data to GitHub.

## 🛡️ Protection Mechanisms

### 1. Comprehensive .gitignore Rules
The repository includes extensive `.gitignore` patterns to prevent data leakage:

#### Data Directories
```bash
data/                    # Main data directory  
**/data/                # Data directories anywhere
data-*/                 # Timestamped data dirs
backup-*/              # Backup directories  
export-*/              # Export directories
```

#### File Extensions
```bash
*.csv *.xlsx *.xls      # Spreadsheet formats
*.parquet *.arrow       # Columnar data formats
*.pkl *.pickle          # Python serialized data
*.db *.sqlite*          # Database files
```

#### Specific Data Files
```bash
**/snapshot*.json       # Data snapshots
**/entries*.json        # Personal entries
**/insights*.json       # Analysis results
**/processed*.json      # Processed data
raw_data.*             # Raw data files
```

#### HuggingFace Exports
```bash
**/hf-dataset/         # HF dataset directories
**/dataset/            # Generic dataset dirs
*.hf                   # HF format files
```

#### Google Sheets Downloads
```bash
*sheets_data*          # Sheet data files
*google_sheets*        # Google Sheets exports
*download_*.csv        # Downloaded CSV files
*export_*.xlsx         # Exported Excel files
```

### 2. Configuration Security
```bash
config.local.toml      # Local configurations
secrets/               # Service account keys
*.secret.json          # Secret files
.env*                  # Environment variables
```

### 3. Generated Files Protection
```bash
visualization/*.png    # Generated plots
*.log                  # Log files
temp_data_*           # Temporary files
*_cache/              # Cache directories
```

## ✅ Testing Data Security

### Check if Files Are Ignored
```bash
# Test data files (should return file path = ignored)
git check-ignore data/raw/snapshot_latest.json

# Test legitimate files (should return error = not ignored)
git check-ignore pyproject.toml
```

### Verify Git Status
```bash
# Should show no data files
git status --porcelain
```

### List Ignored Files
```bash
# See all ignored files in data directory
git status --ignored data/
```

## 🚨 Emergency Data Leak Response

If personal data is accidentally committed:

### 1. Immediate Actions
```bash
# Remove from staging (if not yet committed)
git reset HEAD sensitive_file.csv

# Remove from latest commit (if just committed)
git reset --soft HEAD~1
git reset HEAD sensitive_file.csv
rm sensitive_file.csv
git commit -m "Remove sensitive data"
```

### 2. If Already Pushed to Remote
```bash
# Remove from history (DESTRUCTIVE - coordinate with team)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch sensitive_file.csv' \
  --prune-empty --tag-name-filter cat -- --all

# Force push (requires admin rights)
git push --force --all
```

### 3. Professional Response
1. **Rotate Credentials**: Change any API keys or credentials in the data
2. **Audit Impact**: Check what personal data was exposed
3. **Document Incident**: Record what happened and how it was resolved
4. **Review Process**: Improve security measures to prevent recurrence

## 📋 Developer Checklist

Before committing, always verify:

- [ ] `git status` shows no data files
- [ ] Personal information is not in code comments
- [ ] API keys are in `config.local.toml` (ignored)
- [ ] Service accounts are in `secrets/` (ignored)
- [ ] Generated plots are not committed

## 🔍 Data File Patterns to Watch

### Common Risky Filenames
```
diary_2024.csv
my_sleep_data.xlsx  
personal_analysis.json
google_sheets_export.csv
user_data_backup.sqlite
mood_tracking.parquet
```

### Safe Patterns
```
config.example.toml     # Template configs
README.md              # Documentation
*.py                   # Source code
test_data_synthetic.json # Synthetic test data
```

## 🎯 Best Practices

### For Data Processing
1. **Keep data local**: Never commit real personal data
2. **Use synthetic data**: Create fake data for testing
3. **Document data flows**: Clearly mark where sensitive data moves
4. **Regular audits**: Periodically check git history for leaks

### For Development
1. **Test with samples**: Use small, anonymized datasets for development
2. **Environment separation**: Keep dev/test/prod data completely separate
3. **Code reviews**: Always review commits for sensitive data
4. **CI/CD checks**: Set up automated scanning for sensitive patterns

## 📞 Support

If you discover a potential data leak or have questions about data security:

1. **Stop immediately**: Don't make additional commits
2. **Check this guide**: Follow the emergency response steps
3. **Document the issue**: Note what was exposed and when
4. **Review and improve**: Update security measures based on lessons learned

Remember: **Data security is everyone's responsibility** in personal analytics projects.