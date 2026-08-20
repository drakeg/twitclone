# Creator Pro analytics

Creator Pro reports only activity Ripple has explicitly measured. It does not infer or fabricate reach, views, or historical traffic that predates analytics collection.

## Reporting ranges

The dashboard supports 7-, 30-, and 90-day windows. An invalid or missing range defaults to 30 days.

When the available measured history does not extend back to the start of the selected window, the dashboard labels the range as **Partial history**. Previous-period comparisons are withheld until Ripple has enough measured history to cover the complete prior window.

## Metrics

- **Impressions**: daily-unique post impressions collected by `PostImpression`. The tracking layer records at most one impression per post/viewer/day and excludes an author's own views.
- **Profile visits**: daily-unique visits collected by `ProfileVisit`, excluding self-visits.
- **Engagements**: reposts plus non-removed quotes created during the selected window.
- **Engagement rate**: engagements during the selected window divided by measured impressions during that window, expressed as a percentage. If there are no measured impressions, the rate is 0 rather than an invented percentage.
- **Follower growth**: change between the best available follower-count baseline and the most recent snapshot in the selected window. If no snapshot exists before the range begins, the UI labels the value as beginning with the first observed snapshot rather than claiming a complete range.

## Post and hashtag performance

Post performance combines impressions, reposts, and quotes recorded during the selected window. A post may therefore appear even if it was published before the selected range; its displayed performance reflects only activity inside the range.

Hashtag performance aggregates those same selected-window measurements across the user's posts containing each hashtag. Hashtag matching is case-insensitive.

## Privacy and deduplication

Anonymous viewers are represented by opaque session tokens created by the analytics tracking layer. Ripple does not store IP addresses or browser fingerprints for these measurements.
