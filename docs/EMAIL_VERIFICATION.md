# Email ownership verification

Ripple verifies ownership of newly registered email addresses without blocking normal community participation while verification is pending.

## Account behavior

- New registrations create an explicit unverified email-status record and send an expiring signed verification link.
- Existing accounts are backfilled as verified by migration `20260826_0016`; this avoids unexpectedly locking established users out of existing workflows.
- Unverified users may still log in, post, follow, message, and use account recovery.
- The user's own profile shows the pending state and a resend control.
- Identity-verification applications require a verified email address because that workflow asserts account ownership/identity.
- A successful verification link records the verification timestamp and is safe to revisit.

## Token security

Email-verification links are signed with the application `SECRET_KEY`, use a salt distinct from password-reset tokens, and expire according to `EMAIL_VERIFICATION_MAX_AGE_SECONDS` (24 hours by default).

The token also includes a fingerprint of the user's current password hash. A password change therefore invalidates previously issued verification links. The user can log in and request a fresh link afterward.

## Local development

Mail delivery remains suppressed by default outside production. With `MAIL_SUPPRESS_SEND=true`, Ripple logs the generated verification URL rather than contacting an SMTP server. This makes the complete flow testable in local containers at no external-service cost.

To exercise the flow locally:

1. Register a new account.
2. Find the `email_verification_email_suppressed` log entry in the web-container output.
3. Open the logged `verification_url` in the browser.
4. Confirm that the profile displays `Email verified` and no longer offers a resend action.

## Production

Production already requires `MAIL_SUPPRESS_SEND=false`. Configure the same SMTP settings used by account recovery. No separate mail provider or paid service is required by the application contract.
