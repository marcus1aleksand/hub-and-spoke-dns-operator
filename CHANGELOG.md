# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

## [0.4.0] - 2026-01-01

### Added
- Initial release of hub-and-spoke-dns-operator
- Azure DNS provider support
- GCP Cloud DNS provider support
- AWS Route53 provider support
- Ingress annotation parsing for DNS record management

[0.4.8]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/compare/v0.4.0...v0.4.8
[0.4.0]: https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/releases/tag/v0.4.0
