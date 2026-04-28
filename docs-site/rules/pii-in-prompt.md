# `pii-in-prompt` — PII Detection

**Severity:** CRITICAL · **Auto-fix:** No · **Category:** 🔒 Security

## What It Does

Detects Personally Identifiable Information (PII) hardcoded in the prompt — email addresses, phone numbers, SSNs, credit card numbers, and similar sensitive identifiers.

## Example

**Prompt:**
```
The customer John Smith (john.smith@acme.com, SSN: 123-45-6789) is requesting
a refund for order #98765. His card ending in 4242 was charged $299.
```

**Findings:**
```
[ CRITICAL ] pii-in-prompt (line 1)
  Email address detected: jo**@acme.com

[ CRITICAL ] pii-in-prompt (line 1)
  SSN pattern detected: ***-**-6789

[ CRITICAL ] pii-in-prompt (line 2)
  Credit card pattern detected: **** **** **** 4242
```

Note: Detected values are **redacted** in output to avoid double-logging PII.

## Detected PII Types

| Type | Example | Pattern |
|------|---------|---------|
| Email address | `user@example.com` | RFC 5322 format |
| Phone number | `+1 (555) 867-5309` | US/intl formats |
| SSN | `123-45-6789` | `\d{3}-\d{2}-\d{4}` |
| Credit card | `4111 1111 1111 1111` | Luhn-validated |

## Configuration

```yaml
rules:
  pii_in_prompt:
    enabled: true
    check_email: true
    check_phone: true
    check_ssn: true
    check_credit_card: true
```

Disable individual checks:

```yaml
rules:
  pii_in_prompt:
    enabled: true
    check_email: true
    check_phone: false   # phone numbers OK in your use case
    check_ssn: true
    check_credit_card: true
```

## How to Fix

Use ID references instead of PII:

::: danger Bad
```
Look up the account for john.smith@acme.com and issue a refund.
```
:::

::: tip Good
```
Look up the account for customer_id={{CUSTOMER_ID}} and issue a refund.
```
:::

## Legal Considerations

Depending on your jurisdiction, processing PII in AI prompts may require:
- GDPR data processing agreements
- CCPA disclosures
- HIPAA BAAs (for health data)

This rule helps identify where PII is inadvertently embedded before it reaches your AI provider.
