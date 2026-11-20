# SMB member-community pilot validation

This playbook turns Ripple's current operator-dashboard MVP into a repeatable
customer-discovery and pilot process. It does not claim product-market fit,
customer demand, or willingness to pay.

## Demo setup

Use the existing local Docker Compose environment:

```bash
docker compose up -d --build
docker compose exec web flask --app application seed-demo-content
```

The application binds to `0.0.0.0` by default, so it can be demonstrated from
another device on the same LAN using the Docker host's IP address.

Demo operator account:

- email: `campfirecode@example.test`
- password: `Passw0rd!`
- Space: `/spaces/roadside-creators-club`
- Operator dashboard: `/spaces/roadside-creators-club/operator`

The seeded demo includes members, an owner, a moderator, recent Space activity,
and one pending moderation appeal.

## Ideal prospect hypothesis

Prioritize organizations with roughly 25–500 members where one or a few people
handle community/member administration and currently rely on multiple tools,
manual lists, or repetitive copy/paste work.

Examples to test:

- local professional associations;
- hobby or enthusiast clubs;
- nonprofit member communities;
- coaching/mastermind communities;
- alumni or volunteer groups;
- small trade/member organizations.

This segment definition is a hypothesis until interviews confirm it.

## Qualification questions

Before a demo, determine:

1. How many members do you manage?
2. Who administers the community and how much time do they spend each month?
3. Which tools currently hold member, discussion, moderation, and resource data?
4. Where are spreadsheets, manual reminders, duplicate entry, or copy/paste still required?
5. What does the organization currently pay for community/membership software?
6. What would make changing tools too risky or inconvenient?

A prospect is stronger when there is a current, repeated administrative problem
with measurable time/cost impact.

## Demo sequence

Keep the demo under 15 minutes unless the prospect asks to go deeper.

1. Open the sample Space and explain owner/moderator/member roles.
2. Open the operator dashboard.
3. Show member/new-member counts and recent activity without presenting them as
   engagement scores.
4. Open the pending appeal and moderation history.
5. Show existing role management, conversations, resources, and messaging.
6. Ask which part maps to work they currently do manually.
7. Do not demo unrelated Ripple features unless they solve a stated pain.

## Interview questions

Ask after showing the workflow:

- Which part would save you the most time?
- What important operator task is still missing?
- What would you need before trusting this with real members?
- What data would need to be imported?
- Which integrations are mandatory versus nice to have?
- Would you try a small hosted pilot?
- Would `$49–$79/month` be obviously too low, reasonable, or too high for the
  problem solved?
- If not, what would make the offer worth paying for?

Avoid asking only whether they "like" the product. Seek current behavior,
specific pain, budget, decision process, and willingness to take a next step.

## Evidence record

For each real prospect, record outside public source control:

- organization/type;
- approximate member count;
- current tools and monthly cost when voluntarily shared;
- administrative hours/pain described by the prospect;
- exact workflow they want improved;
- must-have blockers;
- price reaction;
- agreed next step;
- whether they accepted a pilot, declined, or need follow-up.

Do not record private customer information in this public repository.

## Pilot offer hypothesis

Initial test offer:

- hosted Ripple member community;
- operator dashboard and existing community/member capabilities;
- basic onboarding/configuration;
- `$49–$79/month` hypothesis;
- optional setup/migration fee only when real migration work exists.

Do not add custom features or integrations to win a prospect until the requested
work is evaluated against repeatability and the broader SMB target.

## Validation thresholds

The next product investment should be evidence-driven. A useful initial gate is:

- at least 5 qualified discovery conversations;
- at least 3 prospects confirm the same or closely related administrative pain;
- at least 1 prospect agrees to a concrete pilot or paid next step.

These are internal decision thresholds, not claims that the market is validated.

If the pattern is weak, revise the buyer/pain hypothesis before building more
features. If a repeated blocker emerges, promote that blocker into BACKLOG.md
with acceptance criteria and evidence reference.
