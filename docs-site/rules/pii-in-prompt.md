# `pii-in-prompt` — PII Detection

**Severity:** CRITICAL · **Auto-fix:** No · **Category:** 🔒 Security

## What It Does

Detects Personally Identifiable Information (PII) hardcoded in the prompt text. Even prompts that are never deliberately logged can leak PII through model completions, error messages, or injection attacks that exfiltrate context.

## Detected PII Types

| Type | Config key | Pattern matched | Example |
|------|:----------:|-----------------|---------|
| Email address | `check_email` | RFC 5322 format | `user@example.com` |
| Phone number | `check_phone` | US and international formats | `+1 (555) 867-5309` |
| SSN | `check_ssn` | `\d{3}[-. ]\d{2}[-. ]\d{4}` | `123-45-6789` |
| Credit card (Visa) | `check_credit_card` | 13–16 digit Visa pattern | `4111111111111111` |
| Credit card (Mastercard) | `check_credit_card` | 16 digit MC pattern | `5200828282828210` |
| IP address | `check_ip` | IPv4 dotted-decimal | `192.168.1.100` |

::: warning Credit card caveat
Only **Visa** (starting with 4) and **Mastercard** (starting with 51–55) patterns are detected. American Express, Discover, and other card networks are not currently matched. No Luhn checksum validation is performed — any number matching the length/prefix pattern will trigger the rule.
:::

::: warning IP address caveat
This rule flags any valid IPv4 address, including private/loopback ranges (`127.0.0.1`, `192.168.x.x`, `10.x.x.x`). If your prompt legitimately references an internal IP for technical context, disable `check_ip` or use a hostname alias instead.
:::

## Example

**Prompt:**
```
The customer John Smith (john.smith@acme.com, SSN: 123-45-6789) is requesting
a refund. His card 4111111111111111 was charged $299. He's at 192.168.1.42.
```

**Findings:**
```
[ CRITICAL ] pii-in-prompt (line 1)
  Email address detected: jo**@acme.com

[ CRITICAL ] pii-in-prompt (line 1)
  SSN pattern detected: ***-**-6789

[ CRITICAL ] pii-in-prompt (line 2)
  Visa card number pattern detected: 41**-****-****-1111

[ CRITICAL ] pii-in-prompt (line 2)
  IP address detected: 192.168.1.42
```

Note: detected values are **redacted in output** to avoid double-logging PII in CI logs.

## How to Fix

Replace PII with ID references or template placeholders:

::: danger Never do this
```
Look up john.smith@acme.com and issue a refund for card 4111111111111111.
The server is at 192.168.1.100.
```
:::

::: tip Do this instead
```
Look up customer {{CUSTOMER_EMAIL}} and issue a refund for card {{CARD_TOKEN}}.
The server is at {{INTERNAL_HOST}}.
```
:::

In code, inject at runtime:

```python
import os

prompt = (template
    .replace("{{CUSTOMER_EMAIL}}", lookup_email(customer_id))
    .replace("{{CARD_TOKEN}}", vault.get_token(card_id))
    .replace("{{INTERNAL_HOST}}", os.environ["DB_HOST"]))
```

## Configuration

All checks are enabled by default. Disable selectively:

```yaml
rules:
  pii_in_prompt:
    enabled: true
    check_email: true
    check_phone: true
    check_ssn: true
    check_credit_card: true
    check_ip: false   # disable if your prompts legitimately use internal IPs
```

Disable the entire rule:
```yaml
rules:
  pii_in_prompt: false
```

## Legal Considerations

Depending on your jurisdiction, processing PII in AI prompts may require:

- **GDPR** (EU): Data processing agreements with your AI provider; right to erasure may apply to prompt logs
- **CCPA** (California): Disclosure of personal data shared with third parties
- **HIPAA** (US): BAA with your AI provider if health data is involved
- **PCI-DSS**: Cardholder data must not be sent to third-party AI services without explicit scope compliance

This rule helps identify where PII is embedded *before* it reaches your AI provider.
