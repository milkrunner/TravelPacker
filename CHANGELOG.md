# Changelog

All notable changes to NikNotes will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- CI/CD pipeline with GitHub Actions for automated testing and linting
- CONTRIBUTING.md with development setup and guidelines
- CODE_OF_CONDUCT.md (Contributor Covenant)
- This CHANGELOG file
- Accessibility improvements: ARIA attributes, roles, skip navigation, focus management
- Loading spinner component for async operations
- Packing history tracking: mark items as actually packed after a trip

### Improved
- Responsive design for mobile devices (hamburger menu, touch targets)
- Semantic HTML structure across all templates

## [0.1.0] - 2025-10-22

### Added
- Initial release of NikNotes
- AI-powered packing suggestions via Google Gemini
- Redis caching for AI responses (10-50ms cached responses)
- PostgreSQL database with connection pooling and performance indexes
- Trip management (create, view, delete)
- Traveler profiles (adult, child, infant)
- Packing list with categories, progress tracking, drag-and-drop reorder
- Trip templates for recurring travel patterns
- PDF export of packing lists
- Dark mode with persistent preference
- Weather integration for destination-based suggestions
- Google OAuth 2.0 sign-in
- Enterprise security: CSRF, CSP, rate limiting, input sanitization, audit logging
- Docker deployment with multi-stage builds
- Comprehensive documentation (51 pages)
