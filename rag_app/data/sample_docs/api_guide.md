# Nimbus Cloud Storage — API Guide

## Authentication

All API requests require a bearer token in the `Authorization` header. Tokens are generated from the account settings page and do not expire, but can be revoked at any time. There is currently no OAuth flow — API access is only available via long-lived personal access tokens.

## Rate limits

The API enforces a rate limit of 100 requests per minute per token on the Pro plan, and 500 requests per minute per token on the Business plan. The Free plan does not have API access at all. Exceeding the rate limit returns an HTTP 429 response with a `Retry-After` header indicating the number of seconds to wait.

## Uploading files

Files are uploaded via a POST request to `/v1/files` with the file content as multipart form data. The maximum single-file upload size via the API is 5 GB. For larger files, Nimbus requires the chunked upload endpoint at `/v1/files/chunked`, which supports files up to the plan's total storage limit.

## Webhooks

Business plan customers can register webhooks that fire on file upload, file deletion, and share-link creation. Webhook payloads are signed with an HMAC-SHA256 signature in the `X-Nimbus-Signature` header so customers can verify authenticity. Webhooks are not available on Free or Pro plans.

## Deprecation policy

Nimbus commits to a minimum 6-month deprecation notice for any breaking API change, announced via the developer changelog and email to all registered API token holders.
