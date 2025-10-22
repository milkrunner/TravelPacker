# Reports Directory

Generated reports including security scans, test coverage, and analysis results.

## Structure

```
reports/
├── security/          # Security scan reports
│   └── scan-report-YYYY-MM-DD.txt
└── coverage/          # Test coverage reports
    └── htmlcov/       # HTML coverage reports
```

## .gitignore

Report files are excluded from version control (structure preserved):
```
reports/**/*.txt
reports/**/*.html
reports/**/*.xml
!reports/**/.gitkeep
```

## Report Types

### Security Reports
- Dependency vulnerability scans (`pip-audit`)
- Container security scans
- Static analysis results

### Coverage Reports
- pytest coverage reports
- HTML coverage visualization

## Generating Reports

See `scripts/security/` for security scan scripts.
