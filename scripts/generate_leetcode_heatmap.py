import json
import os
import urllib.request
from datetime import datetime, timezone

USERNAME = "AadiCodes6386"

# API base is split so this file doesn't depend on a README image service.
API_BASE = "https://" + "leetcode-api-pied.vercel.app"

OUTPUT = "leetcode-heatmap.svg"

GREEN = "#22c55e"
WHITE = "#ffffff"
BORDER = "#e5e7eb"
TEXT = "#374151"

CELL = 12
GAP = 4
STEP = CELL + GAP

WEEKS = 53
DAYS = 7

def fetch_calendar():
    url = f"{API_BASE}/user/{USERNAME}/calendar"

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def extract_calendar(data):
    """
    Supports common calendar response formats.
    """

    if isinstance(data, dict):

        # Direct dictionary of timestamps -> counts
        if all(str(k).isdigit() for k in data.keys()):
            return data

        # Common nested formats
        for key in [
            "submissionCalendar",
            "calendar",
            "data",
            "submissions"
        ]:
            if key in data:

                value = data[key]

                if isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        continue

                if isinstance(value, dict):
                    return value

                if isinstance(value, list):
                    result = {}

                    for item in value:
                        if not isinstance(item, dict):
                            continue

                        timestamp = (
                            item.get("timestamp")
                            or item.get("time")
                            or item.get("date")
                        )

                        count = (
                            item.get("count")
                            or item.get("submissions")
                            or item.get("value")
                            or 0
                        )

                        if timestamp is not None:
                            result[str(timestamp)] = int(count)

                    return result

    raise ValueError("Could not find calendar data in API response.")


def normalize_timestamp(value):
    timestamp = int(value)

    # Convert milliseconds to seconds if necessary
    if timestamp > 10_000_000_000:
        timestamp //= 1000

    return datetime.fromtimestamp(
        timestamp,
        tz=timezone.utc
    ).date()


def build_daily_data(calendar):
    daily = {}

    for timestamp, count in calendar.items():
        try:
            date = normalize_timestamp(timestamp)
            daily[date] = int(count)
        except Exception:
            pass

    return daily


def color_for_count(count):
    # EXACTLY TWO COLORS:
    # white = no activity
    # green = activity
    return GREEN if count > 0 else WHITE


def generate_svg(daily):
    today = datetime.now(timezone.utc).date()

    # Start from the Sunday 52 weeks ago.
    start = today

    while start.weekday() != 6:
        from datetime import timedelta
        start -= timedelta(days=1)

    start -= __import__("datetime").timedelta(weeks=WEEKS - 1)

    width = WEEKS * STEP + 24
    height = DAYS * STEP + 70

    parts = []

    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )

    parts.append(
        f'<rect width="100%" height="100%" '
        f'fill="{WHITE}" rx="12"/>'
    )

    parts.append(
        f'<text x="12" y="22" '
        f'font-family="Arial, Helvetica, sans-serif" '
        f'font-size="14" font-weight="600" fill="{TEXT}">'
        f'LeetCode Contributions'
        f'</text>'
    )

    # Day labels
    labels = {
        1: "Mon",
        3: "Wed",
        5: "Fri"
    }

    for day_index, label in labels.items():
        y = 43 + day_index * STEP

        parts.append(
            f'<text x="0" y="{y}" '
            f'font-family="Arial, Helvetica, sans-serif" '
            f'font-size="8" fill="{TEXT}">'
            f'{label}'
            f'</text>'
        )

    # Contribution squares
    for week in range(WEEKS):
        for day in range(DAYS):

            from datetime import timedelta

            date = start + timedelta(
                weeks=week,
                days=day
            )

            count = daily.get(date, 0)

            x = 24 + week * STEP
            y = 32 + day * STEP

            color = color_for_count(count)

            parts.append(
                f'<rect x="{x}" y="{y}" '
                f'width="{CELL}" height="{CELL}" '
                f'rx="2" fill="{color}" '
                f'stroke="{BORDER}" stroke-width="0.7">'
                f'<title>{date}: {count} submission(s)</title>'
                f'</rect>'
            )

    # Legend
    legend_y = height - 20

    parts.append(
        f'<text x="{width - 120}" y="{legend_y}" '
        f'font-family="Arial, Helvetica, sans-serif" '
        f'font-size="9" fill="{TEXT}">'
        f'Less'
        f'</text>'
    )

    parts.append(
        f'<rect x="{width - 85}" y="{legend_y - 10}" '
        f'width="12" height="12" rx="2" '
        f'fill="{WHITE}" stroke="{BORDER}"/>'
    )

    parts.append(
        f'<rect x="{width - 65}" y="{legend_y - 10}" '
        f'width="12" height="12" rx="2" '
        f'fill="{GREEN}"/>'
    )

    parts.append(
        f'<text x="{width - 48}" y="{legend_y}" '
        f'font-family="Arial, Helvetica, sans-serif" '
        f'font-size="9" fill="{TEXT}">'
        f'More'
        f'</text>'
    )

    parts.append("</svg>")

    return "\n".join(parts)


def main():
    print(f"Fetching LeetCode calendar for {USERNAME}...")

    data = fetch_calendar()

    calendar = extract_calendar(data)

    daily = build_daily_data(calendar)

    svg = generate_svg(daily)

    with open(OUTPUT, "w", encoding="utf-8") as file:
        file.write(svg)

    print(f"Generated {OUTPUT}")


if __name__ == "__main__":
    main()
