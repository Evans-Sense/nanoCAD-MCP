# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in nanoCAD MCP Server, please follow these steps:

1. **Do NOT** open a public GitHub issue
2. Email the maintainers at the address listed in the repository's GitHub profile
3. Provide a clear description of the vulnerability
4. Include steps to reproduce the issue
5. If possible, suggest a fix or mitigation

You should receive a response within 48 hours. If not, please follow up.

## What to Report

- Path traversal or unauthorized file access
- Command injection via CAD commands
- Authentication or authorization bypass
- Exposure of sensitive information (tokens, credentials)
- Remote code execution vectors
- Dependency vulnerabilities with known CVEs

## What to Expect

- Acknowledgment of receipt within 48 hours
- Validation and reproduction of the issue
- A timeline for the fix (typically within 14 days for confirmed issues)
- Credit in release notes upon fix publication

## Scope

The following are considered in scope:
- The Python MCP server (`server/`)
- The .NET engine plugin (`engine/`)
- Build and deployment scripts
- CI/CD configuration files

The following are out of scope:
- nanoCAD itself (report to NTCAD)
- Third-party dependencies (report to their respective maintainers)
