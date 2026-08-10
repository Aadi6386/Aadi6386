```python
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

USERNAME = "AadiCodes6386"
OUTPUT = "leetcode-heatmap.svg"

GRAPHQL_URL = "https://leetcode.com/graphql"

# ─────────────────────────────────────────────
# COLORS
# ─────────────────────────────────────────────

GREEN = "#40c463"       # GitHub-style contribution green
WHITE = "#ffffff"       # No activity
BORDER = "#e5e7eb"      # Card border
GRID_BORDER = "#d9dee3" # Subtle inactive square border
TEXT = "#24292f"        # GitHub-style dark text
MUTED = "#57606a"       # Secondary text

# ─────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────

CELL_SIZE = 13
GAP = 4
STEP = CELL_SIZE + GAP

WEEKS = 53
DAYS = 7

LEFT_LABEL = 30
TOP_SPACE = 48
BOTTOM_SPACE = 42

CARD_PADDING = 18

WIDTH = (
    CARD_PADDING * 2
    + LEFT_LABEL
    + WEEKS * STEP
)

HEIGHT = (
    CARD_PADDING * 2
    + TOP_SPACE
    + DAYS * STEP
    + BOTTOM_SPACE
)

# ─────────────────────────────────────────────
# LEETCODE GRAPHQL
# ─────────────────────────────────────────────

QUERY = """
query userProfileCalendar($username: String!, $year: Int) {
  matchedUser(username: $username) {
    userCalendar(year: $year) {
      activeYears
      streak
      totalActiveDays
      submissionCalendar
    }
  }
}
"""


def fetch_calendar():

    payload = {
        "query": QUERY,
        "variables": {
            "username": USERNAME
        },
        "operationName": "userProfileCalendar"
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        GRAPHQL_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://leetcode.com",
            "Referer": "https://leetcode.com/",
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131.0 Safari/537.36"
            )
        },
        method="POST"
    )

    print(f"Fetching LeetCode calendar for {USERNAME}...")

    try:

        with urllib.request.urlopen(
            request,
            timeout=60
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as error:

        body = error.read().decode(
            "utf-8",
            errors="replace"
        )

        print(
            f"LeetCode returned HTTP {error.code}"
        )

        print(body)

        raise RuntimeError(
            "LeetCode rejected the GraphQL request."
        )

    except Exception as error:

        raise RuntimeError(
            f"Could not connect to LeetCode: {error}"
        )

    if "errors" in result:

        print(
            json.dumps(
                result["errors"],
                indent=2
            )
        )

        raise RuntimeError(
            "LeetCode GraphQL returned an error."
        )

    try:

        calendar_string = (
            result["data"]
            ["matchedUser"]
            ["userCalendar"]
            ["submissionCalendar"]
        )

    except (KeyError, TypeError):

        print(
            json.dumps(
                result,
                indent=2
            )
        )

        raise RuntimeError(
            "Could not find submissionCalendar."
        )

    return json.loads(calendar_string)


# ─────────────────────────────────────────────
# CONVERT LEETCODE DATA
# ─────────────────────────────────────────────

def convert_calendar(calendar):

    daily_activity = {}

    for timestamp, count in calendar.items():

        timestamp = int(timestamp)

        # Handle milliseconds if returned
        if timestamp > 10_000_000_000:
            timestamp //= 1000

        date = datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc
        ).date()

        daily_activity[date] = int(count)

    return daily_activity


# ─────────────────────────────────────────────
# CALENDAR START DATE
# ─────────────────────────────────────────────

def get_start_date():

    today = datetime.now(
        timezone.utc
    ).date()

    # Sunday = 0
    days_since_sunday = (
        today.weekday() + 1
    ) % 7

    current_week_sunday = (
        today
        - timedelta(
            days=days_since_sunday
        )
    )

    return (
        current_week_sunday
        - timedelta(
            weeks=WEEKS - 1
        )
    )


# ─────────────────────────────────────────────
# SVG HELPERS
# ─────────────────────────────────────────────

def escape_xml(text):

    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def month_label_position(
    start_date,
    week
):

    date = (
        start_date
        + timedelta(weeks=week)
    )

    return date


# ─────────────────────────────────────────────
# GENERATE SVG
# ─────────────────────────────────────────────

def generate_svg(activity):

    start_date = get_start_date()

    today = datetime.now(
        timezone.utc
    ).date()

    total_submissions = sum(
        activity.values()
    )

    active_days = sum(
        1 for count in activity.values()
        if count > 0
    )

    current_year = today.year

    svg = []

    svg.append(
        f'''<svg
xmlns="http://www.w3.org/2000/svg"
width="{WIDTH}"
height="{HEIGHT}"
viewBox="0 0 {WIDTH} {HEIGHT}">
'''
    )

    # ─────────────────────────────────────
    # DEFINITIONS
    # ─────────────────────────────────────

    svg.append(
        f'''
<defs>

    <filter
        id="shadow"
        x="-20%"
        y="-20%"
        width="140%"
        height="140%">

        <feDropShadow
            dx="0"
            dy="2"
            stdDeviation="4"
            flood-color="#000000"
            flood-opacity="0.08"/>

    </filter>

</defs>
'''
    )

    # ─────────────────────────────────────
    # CARD
    # ─────────────────────────────────────

    svg.append(
        f'''
<rect
x="1"
y="1"
width="{WIDTH - 2}"
height="{HEIGHT - 2}"
rx="14"
fill="{WHITE}"
stroke="{BORDER}"
stroke-width="1"
filter="url(#shadow)"/>
'''
    )

    # ─────────────────────────────────────
    # HEADER
    # ─────────────────────────────────────

    svg.append(
        f'''
<text
x="{CARD_PADDING}"
y="{CARD_PADDING + 4}"
font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif"
font-size="16"
font-weight="700"
fill="{TEXT}">
🧠 LeetCode Activity
</text>
'''
    )

    svg.append(
        f'''
<text
x="{CARD_PADDING}"
y="{CARD_PADDING + 23}"
font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif"
font-size="10"
fill="{MUTED}">
{escape_xml(USERNAME)} · {current_year}
</text>
'''
    )

    # ─────────────────────────────────────
    # STATISTICS
    # ─────────────────────────────────────

    stats_x = WIDTH - 190

    svg.append(
        f'''
<text
x="{stats_x}"
y="{CARD_PADDING + 5}"
font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif"
font-size="11"
font-weight="600"
fill="{TEXT}">
{total_submissions}
</text>
'''
    )

    svg.append(
        f'''
<text
x="{stats_x}"
y="{CARD_PADDING + 19}"
font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif"
font-size="8"
fill="{MUTED}">
submissions
</text>
'''
    )

    svg.append(
        f'''
<text
x="{stats_x + 75}"
y="{CARD_PADDING + 5}"
font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif"
font-size="11"
font-weight="600"
fill="{TEXT}">
{active_days}
</text>
'''
    )

    svg.append(
        f'''
<text
x="{stats_x + 75}"
y="{CARD_PADDING + 19}"
font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif"
font-size="8"
fill="{MUTED}">
active days
</text>
'''
    )

    # ─────────────────────────────────────
    # MONTH LABELS
    # ─────────────────────────────────────

    previous_month = None

    for week in range(WEEKS):

        date = (
            start_date
            + timedelta(weeks=week)
        )

        month = date.month

        if month != previous_month:

            x = (
                CARD_PADDING
                + LEFT_LABEL
                + week * STEP
            )

            month_name = date.strftime(
                "%b"
            )

            svg.append(
                f'''
<text
x="{x}"
y="{CARD_PADDING + 40}"
font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif"
font-size="9"
fill="{MUTED}">
{month_name}
</text>
'''
            )

            previous_month = month

    # ─────────────────────────────────────
    # DAY LABELS
    # ─────────────────────────────────────

    day_labels = {
        1: "Mon",
        3: "Wed",
        5: "Fri"
    }

    for day, label in day_labels.items():

        y = (
            CARD_PADDING
            + TOP_SPACE
            + day * STEP
            + 9
        )

        svg.append(
            f'''
<text
x="{CARD_PADDING}"
y="{y}"
font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif"
font-size="8"
fill="{MUTED}">
{label}
</text>
'''
        )

    # ─────────────────────────────────────
    # CONTRIBUTION GRID
    # ─────────────────────────────────────

    for week in range(WEEKS):

        for day in range(DAYS):

            date = (
                start_date
                + timedelta(
                    weeks=week,
                    days=day
                )
            )

            count = activity.get(
                date,
                0
            )

            x = (
                CARD_PADDING
                + LEFT_LABEL
                + week * STEP
            )

            y = (
                CARD_PADDING
                + TOP_SPACE
                + day * STEP
            )

            # EXACTLY TWO COLORS
            if count > 0:
                color = GREEN
                stroke = GREEN
            else:
                color = WHITE
                stroke = GRID_BORDER

            date_text = date.strftime(
                "%b %d, %Y"
            )

            tooltip = (
                f"{date_text} · "
                f"{count} submission"
                f"{'s' if count != 1 else ''}"
            )

            svg.append(
                f'''
<rect
x="{x}"
y="{y}"
width="{CELL_SIZE}"
height="{CELL_SIZE}"
rx="3"
fill="{color}"
stroke="{stroke}"
stroke-width="0.8">

<title>
{escape_xml(tooltip)}
</title>

</rect>
'''
            )

    # ─────────────────────────────────────
    # FOOTER / LEGEND
    # ─────────────────────────────────────

    footer_y = (
        HEIGHT
        - CARD_PADDING
        - 8
    )

    legend_start = (
        WIDTH
        - 105
    )

    svg.append(
        f'''
<text
x="{CARD_PADDING}"
y="{footer_y}"
font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif"
font-size="8"
fill="{MUTED}">
Green = LeetCode activity
</text>
'''
    )

    svg.append(
        f'''
<text
x="{legend_start}"
y="{footer_y}"
font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif"
font-size="8"
fill="{MUTED}">
Less
</text>
'''
    )

    # White legend square
    svg.append(
        f'''
<rect
x="{legend_start + 25}"
y="{footer_y - 9}"
width="11"
height="11"
rx="3"
fill="{WHITE}"
stroke="{GRID_BORDER}"
stroke-width="0.8"/>
'''
    )

    # Green legend square
    svg.append(
        f'''
<rect
x="{legend_start + 42}"
y="{footer_y - 9}"
width="11"
height="11"
rx="3"
fill="{GREEN}"/>
'''
    )

    svg.append(
        f'''
<text
x="{legend_start + 59}"
y="{footer_y}"
font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif"
font-size="8"
fill="{MUTED}">
More
</text>
'''
    )

    svg.append(
        "</svg>"
    )

    return "\n".join(svg)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():

    print(
        f"Fetching LeetCode calendar for {USERNAME}..."
    )

    calendar = fetch_calendar()

    print(
        f"Received {len(calendar)} activity records."
    )

    activity = convert_calendar(
        calendar
    )

    print(
        f"Generating {OUTPUT}..."
    )

    svg = generate_svg(
        activity
    )

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(svg)

    print(
        f"Successfully generated {OUTPUT}"
    )


if __name__ == "__main__":
    main()
```
