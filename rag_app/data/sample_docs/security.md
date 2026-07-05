# Nimbus Cloud Storage — Security

## Encryption

All files are encrypted at rest using AES-256. Files in transit are protected using TLS 1.3. Encryption keys are managed by Nimbus and rotated automatically every 90 days.

## Authentication

Free and Pro plans support email/password login and optional TOTP-based two-factor authentication. Business plans additionally support SAML-based single sign-on (SSO), allowing companies to enforce login through their own identity provider (e.g., Okta, Azure AD).

## Data residency

By default, all customer data is stored in US-based data centers. Business plan customers can request EU-only data residency at no additional cost, but this must be configured before any files are uploaded — Nimbus does not currently support migrating existing data between regions.

## Compliance

Nimbus is SOC 2 Type II certified. Business plans with EU data residency additionally meet GDPR data processing requirements. Nimbus is not currently HIPAA-compliant and should not be used to store protected health information on any plan.

## Incident response

In the event of a confirmed data breach affecting customer files, Nimbus commits to notifying affected Business plan admins within 72 hours of confirmation. Free and Pro plan users are notified via the email on file, with no specific SLA on notification time.
