# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest release | Yes |
| Older releases | No |

Only the latest release on the main branch receives security updates.

## Reporting a Vulnerability

If you discover a security vulnerability, please report it through [GitHub's private vulnerability reporting](https://github.com/turqoisehex/hushtype/security/advisories/new).

**Please do not open a public issue for security vulnerabilities.**

## What to Expect

This is a side project maintained in spare time. Critical vulnerabilities will be prioritized, but please be patient with response times.

- **Acknowledgment**: Best effort, typically within a few days
- **Resolution**: Depends on severity and complexity
- **Disclosure**: Coordinated disclosure after a fix is available

## Scope

hushtype runs entirely locally -- no network services, no user accounts, no data storage beyond local config. The primary attack surface is:

- PyInstaller executable integrity
- Clipboard handling (temporary clipboard access during paste operations)
- Whisper model download (first run only, from HuggingFace)

## Out of Scope

- Social engineering attacks
- Attacks requiring physical access to the machine
- Issues in upstream dependencies (report those to the respective projects)
