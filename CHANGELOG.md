# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.9] - 2026-06-01

### Changed
- Updated Helm chart to v0.4.9

## [0.4.8] - 2026-02-24

### Added
- CNAME record support for all DNS providers (Azure DNS, GCP Cloud DNS, AWS Route53)
- Annotation-based record type selection (`hub-dns-operator.io/record-type: CNAME`)
- Auto-detection: if target is hostname → create CNAME, if IP → create A record

### Changed
- Updated base provider to support both A and CNAME record types
- Updated Azure DNS provider for CNAME support
- Updated GCP Cloud DNS provider for CNAME support
- Updated AWS Route53 provider for CNAME support

### Fixed
- Azure provider hardcoded A-record type issue
- Bandit scan extended to full operator/ directory
- Python version aligned (3.13 in Dockerfile, tests, and default)

### Dependencies
- Updated kubernetes client to v36
- Updated Python to 3.13

## [0.4.7] - 2026-03-20

### Fixed
- Fix failing Lint & Security Scan CI (#74)
- Use Python 3.13 instead of unreleased 3.14 in Dockerfile
- Extend bandit scan to entire operator/ directory
- Expand pre-commit hook deduplication to Azure error Helm docs

### Changed
- Pin yaml-update-action to v0.12.2 instead of @main
- Update Helm Chart version to 0.4.7
- Update all dependencies

## [0.4.6] - 2026-03-19

### Changed
- Update Helm Chart version to 0.4.6

## [0.4.5] - 2026-03-18

### Changed
- Update Helm Chart version to 0.4.5

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

## [0.4.0] - 2026-01-01

### Added
- Initial release of hub-and-spoke-dns-operator
- Azure DNS provider support
- GCP Cloud DNS provider support
- AWS Route53 provider support
- Ingress annotation parsing for DNS record management

[Unreleased]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.4.9...HEAD
[0.4.9]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.4.8...v0.4.9
[0.4.8]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.4.7...v0.4.8
[0.4.7]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.4.6...v0.4.7
[0.4.6]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.4.5...v0.4.6
[0.4.5]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.4.4...v0.4.5
[0.4.4]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.4.3...v0.4.4
[0.4.3]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/releases/tag/v0.4.0
