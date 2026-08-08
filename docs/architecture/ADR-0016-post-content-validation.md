# ADR-0016: Central post-content validation

- Status: Accepted
- Date: 2026-08-07
- Sprint: 3
- Story: 3.1

## Context

Tweet and quote routes previously checked only whether submitted content exceeded
144 characters. Missing form fields raised a request error, while empty and
whitespace-only content was stored. The tweet route also processed uploads and
schedule fields before rejecting overlength content.

Browser `maxlength` attributes are useful guidance but do not protect direct HTTP
requests. Both workflows need one server-side definition of valid post content.

## Decision

Add a timeline validation module with a shared 144-character limit and content
validator. Tweets and quotes now:

- reject missing, empty, and whitespace-only content;
- accept content containing 1 through 144 characters;
- reject content exceeding 144 characters;
- preserve accepted content exactly rather than trimming it; and
- validate before upload processing, schedule parsing, or database writes.

Keep the existing redirect behavior for invalid tweets and template-rendering
behavior for invalid quotes. Add `required` to the existing textareas while
retaining their `maxlength="144"` hints.

## Consequences

### Positive

- Direct requests and browser submissions follow the same content rules.
- Missing fields no longer produce an unhandled request error.
- Invalid tweets cannot leave uploaded files behind.
- Tweet and quote length behavior cannot drift independently.

### Negative

- Requests that previously created blank posts are now rejected.
- The legacy `/dm` command still shares the tweet content field and requires
  separate messaging validation later.

## Guardrails

- Media validation, schedule validation, pagination, ordering, and ownership are
  separate Sprint 3 or later stories.
- Changing the 144-character product limit requires a coordinated model,
  template, validation, and migration review.
