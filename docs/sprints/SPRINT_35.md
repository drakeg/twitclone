# Sprint 35 — Space calendar portability

**Status:** In progress.

## Goal

Make Space events portable to members' existing calendar workflows without requiring Ripple to operate an external calendar service or expose attendee identity/private member data.

## Story 35.1 — Member-only iCalendar export

**Status:** Implemented; validation in progress.

Add a downloadable iCalendar (.ics) attachment containing upcoming active Space events.

### Acceptance criteria

- Only current Space members can download a Space calendar export.
- Export includes upcoming non-canceled events only, ordered chronologically and capped at 100 events.
- Event times are emitted as UTC iCalendar timestamps.
- Calendar text fields correctly escape backslash, comma, semicolon, and newlines.
- Physical iCalendar lines are folded to at most 75 UTF-8 octets.
- Stable event UIDs are derived from persistent event IDs.
- Export contains event title, description, optional location, start time, and calendar name only; it excludes member emails, attendee identities, RSVP state, ranking, reputation, verification, and paid-status data.
- Response is an attachment with stable filename, private/no-store cache policy, and MIME sniffing disabled.
- Archived Spaces remain exportable because calendar download is read-only.
- No external calendar provider, credentials, background sync, or infrastructure spend is introduced.

## Story 35.2 — Individual event calendar download

**Status:** Implemented; validation in progress.

Add a member-only single-event iCalendar download using the same renderer and
privacy boundaries as the full Space calendar.

### Acceptance criteria

- Current Space members can download one upcoming active event; nonmembers
  cannot.
- Canceled and past events are not exportable individually.
- Single-event and full-calendar exports share UID, UTC time, text escaping, line
  folding, cache/privacy, and no-private-data behavior.
- Event detail exposes an Add to calendar control for active upcoming events.
- Stable filename includes the Space slug and persistent event ID.
- No external calendar provider, background sync, attendee identity, or RSVP
  state is included.

## Story 35.3 — Calendar regression hardening

**Status:** Ready after Story 35.2 validation.

Close the sprint with escaping, line-folding, bounds, authorization, archived Space, canceled-event, UTF-8, and no-private-data regression coverage.
