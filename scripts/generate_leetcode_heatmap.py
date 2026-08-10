import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

USERNAME = "AadiCodes6386"
OUTPUT = "leetcode-heatmap.svg"

GRAPHQL_URL = "https://leetcode.com/graphql"

GREEN = "#22c55e"
WHITE = "#ffffff"
BORDER = "#d1d5db"
TEXT = "#374151"

CELL_SIZE = 12
GAP = 4
STEP = CELL_SIZE + GAP

WEEKS = 53
DAYS = 7


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
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")

        print(f"LeetCode returned HTTP {error.code}")
        print(body)

        raise RuntimeError(
            "LeetCode blocked or rejected the GraphQL request."
        )

    except Exception as error:
        raise RuntimeError(
            f"Could not connect to LeetCode: {error}"
        )

    if "errors" in result:
        print(json.dumps(result["errors"], indent=2))

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
        print(json.dumps(result, indent=2))

        raise RuntimeError(
            "Could not find submissionCalendar in LeetCode response."
        )

    return json.loads(calendar_string)


def convert_calendar(calendar):
    daily_activity = {}

    for timestamp, count in calendar.items():

        timestamp = int(timestamp)

        # LeetCode timestamps are normally seconds.
        if timestamp > 10_000_000_000:
            timestamp //= 1000

        date = datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc
        ).date()

        daily_activity[date] = int(count)

    return daily_activity


def get_start_date():
    today = datetime.now(timezone.utc).date()

    # Python:
    # Monday = 0
    # Sunday = 6

    days_since_sunday = (today.weekday() + 1) % 7

    current_week_sunday = (
        today - timedelta(days=days_since_sunday)
    )

    return current_week_sunday - timedelta(
        weeks=WEEKS - 1
    )


def generate_svg(activity):
    start_date = get_start_date()

    width = (
        24 +
        WEEKS * STEP
    )

    height = (
        72 +
        DAYS * STEP
    )

    svg = []

    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" '
        f'height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )

    # White background
    svg.append(
        f'<rect width="100%" height="100%" '
        f'fill="{WHITE}" rx="12"/>'
    )

    # Title
    svg.append(
        f'<text x="12" y="20" '
        f'font-family="Arial, Helvetica, sans-serif" '
        f'font-size="14" '
        f'font-weight="600" '
        f'fill="{TEXT}">'
        f'LeetCode Contributions'
        f'</text>'
    )

    # Day labels
    labels = {
        1: "Mon",
        3: "Wed",
        5: "Fri"
    }

    for day, label in labels.items():

        y = 42 + day * STEP

        svg.append(
            f'<text x="0" y="{y}" '
            f'font-family="Arial, Helvetica, sans-serif" '
            f'font-size="8" '
            f'fill="{TEXT}">'
            f'{label}'
            f'</text>'
        )

    # Contribution squares
    for week in range(WEEKS):

        for day in range(DAYS):

            date = start_date + timedelta(
                weeks=week,
                days=day
            )

            count = activity.get(date, 0)

            x = 24 + week * STEP
            y = 30 + day * STEP

            # EXACTLY TWO COLORS
            color = GREEN if count > 0 else WHITE

            svg.append(
                f'<rect '
                f'x="{x}" '
                f'y="{y}" '
                f'width="{CELL_SIZE}" '
                f'height="{CELL_SIZE}" '
                f'rx="2" '
                f'fill="{color}" '
                f'stroke="{BORDER}" '
                f'stroke-width="0.7">'
                f'<title>{date}: {count} submission(s)</title>'
                f'</rect>'
            )

    # Legend
    legend_y = height - 16

    svg.append(
        f'<text x="{width - 120}" '
        f'y="{legend_y}" '
        f'font-family="Arial, Helvetica, sans-serif" '
        f'font-size="9" '
        f'fill="{TEXT}">'
        f'Less'
        f'</text>'
    )

    # White
    svg.append(
        f'<rect '
        f'x="{width - 85}" '
        f'y="{legend_y - 10}" '
        f'width="12" '
        f'height="12" '
        f'rx="2" '
        f'fill="{WHITE}" '
        f'stroke="{BORDER}"/>'
    )

    # Green
    svg.append(
        f'<rect '
        f'x="{width - 65}" '
        f'y="{legend_y - 10}" '
        f'width="12" '
        f'height="12" '
        f'rx="2" '
        f'fill="{GREEN}"/>'
    )

    svg.append(
        f'<text x="{width - 48}" '
        f'y="{legend_y}" '
        f'font-family="Arial, Helvetica, sans-serif" '
        f'font-size="9" '
        f'fill="{TEXT}">'
        f'More'
        f'</text>'
    )

    svg.append("</svg>")

    return "\n".join(svg)


def main():

    calendar = fetch_calendar()

    activity = convert_calendar(calendar)

    svg = generate_svg(activity)

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
