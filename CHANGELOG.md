# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.5] - 2026-03-19

### Fixed
- Fix failing Lint & Security Scan CI (#74)
- Use Python 3.13 instead of unreleased 3.14 in Dockerfile
- Extend bandit scan to entire operator/ directory
- Expand pre-commit hook deduplication to Azure error Helm docs

### Changed
- Pin yaml-update-action to v0.12.2 instead of @main
- Update Helm Chart version to 0.4.5
- Update all dependencies

## [0.4.4] - 2026-03-18

### Changed
- Update Helm Chart version to 0.4.4

## [0.4.3] - 2026-03-17

### Changed
- Update Helm Chart version to 0.4.3
- Align OPERATOR_VERSION default with chart version (0.4.3)
- Fix update helm-docs rev and OPERATOR_VERSION fallback

## [0.4.2] - 2026-03-16

### Changed
- Update Helm Chart version to 0.4.2

## [0.4.1] - 2026-03-16

### Changed
- Update Helm Chart version to 0.4.1
- Fix tests to support CNAME record type

## [0.4.0] - 2026-03-15

### Added
- **CNAME record support** - Major feature addition
  - Add RecordType enum and DNSRecord dataclass to base provider
  - Add is_hostname() method for auto-detection (hostname vs IP)
  - Update Azure, GCP, AWS providers to support CNAME records
  - Add annotation parsing in annotations.py module
  - New annotations: hub-dns-operator.io/record-type, hub-dns-operator.io/target-hostname
  - Comprehensive CNAME-specific unit tests (19 tests)
  - Documentation for CNAME feature

### Changed
- Update Helm Chart version to 0.4.0

## [0.3.3] - 2026-02-15

### Fixed
- Various dependency updates and bug fixes

## [0.3.2] - 2026-01-20

### Changed
- Dependency updates

## [0.3.1] - 2025-12-10

### Changed
- Dependency updates

## [0.3.0] - 2025-11-05

### Added
- Initial release with multi-cloud DNS support

[Unreleased]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.4.5...HEAD
[0.4.5]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.4.4...v0.4.5
[0.4.4]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.4.3...v0.4.4
[0.4.3]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.3.3...v0.4.0
[0.3.3]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.2.0...v0.3.0
