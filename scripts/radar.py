#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
import os
import urllib.error
import urllib.request
from pathlib import Path


THEMES = {
    "dark": {
        "grid": "#30363d",
        "spoke": "#21262d",
        "label": "#c9d1d9",
        "value": "#8b949e",
        "title": "#e6edf3",
        "fill": "#39d353",
        "stroke": "#3fb950",
        "vertex": "#7ee787",
    },
    "light": {
        "grid": "#d0d7de",
        "spoke": "#e6eaef",
        "label": "#1f2328",
        "value": "#57606a",
        "title": "#1f2328",
        "fill": "#2da44e",
        "stroke": "#1a7f37",
        "vertex": "#116329",
    },
}

USER_AGENT = {
    "User-Agent": "Aadi6386-profile-radar"
}


def github_request(url, token):

    request = urllib.request.Request(
        url,
        headers=USER_AGENT,
    )

    if token:
        request.add_header(
            "Authorization",
            f"Bearer {token}",
        )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:

        return json.loads(
            response.read().decode()
        )


def get_languages(username, token):

    totals = {}
    page = 1

    while True:

        url = (
            f"https://api.github.com/users/{username}/repos"
            f"?per_page=100&page={page}&type=owner"
        )

        repos = github_request(
            url,
            token,
        )

        if not repos:
            break

        for repo in repos:

            if repo.get("fork"):
                continue

            if repo.get("archived"):
                continue

            try:

                languages = github_request(
                    repo["languages_url"],
                    token,
                )

            except urllib.error.HTTPError:

                continue

            for language, bytes_count in languages.items():

                if language.lower() in {
                    "shell",
                    "makefile",
                    "dockerfile",
                    "batchfile",
                    "procfile",
                }:

                    continue

                totals[language] = (
                    totals.get(language, 0)
                    + bytes_count
                )

        if len(repos) < 100:
            break

        page += 1

    return totals


def radar_points(radius, count):

    points = []

    for index in range(count):

        angle = (
            -math.pi / 2
            + index * 2 * math.pi / count
        )

        points.append(
            (
                radius * math.cos(angle),
                radius * math.sin(angle),
            )
        )

    return points


def escape(text):

    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render(
    username,
    axes,
    theme,
    size=440,
):

    colors = THEMES[theme]

    count = len(axes)

    radius = size / 2 - 50

    outer = radar_points(
        radius,
        count,
    )

    svg = []

    svg.append(
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}" '
        'role="img">'
    )

    svg.append(
        '<style>'
        'text{font-family:-apple-system,BlinkMacSystemFont,'
        '"Segoe UI",Helvetica,Arial,sans-serif}'
        '</style>'
    )

    svg.append(
        f'<text x="{size / 2}" y="24" '
        'text-anchor="middle" '
        'font-size="15" '
        'font-weight="700" '
        f'fill="{colors["title"]}">'
        f'{escape(username)} · language mix'
        '</text>'
    )

    # Rings
    for ring in range(1, 5):

        ring_radius = (
            radius * ring / 4
        )

        points = radar_points(
            ring_radius,
            count,
        )

        point_string = " ".join(
            f"{x + size / 2:.1f},"
            f"{y + size / 2 + 10:.1f}"
            for x, y in points
        )

        svg.append(
            f'<polygon points="{point_string}" '
            'fill="none" '
            f'stroke="{colors["grid"]}" '
            'stroke-width="1"/>'
        )

    # Spokes
    center_y = size / 2 + 10

    for x, y in outer:

        svg.append(
            f'<line x1="{size / 2}" '
            f'y1="{center_y}" '
            f'x2="{x + size / 2:.1f}" '
            f'y2="{y + center_y:.1f}" '
            f'stroke="{colors["spoke"]}" '
            'stroke-width="1"/>'
        )

    # Data shape
    data_points = []

    for (language, value), (x, y) in zip(
        axes,
        outer,
    ):

        scaled = value / 100

        data_points.append(
            (
                x * scaled
                + size / 2,
                y * scaled
                + center_y,
            )
        )

    data_string = " ".join(
        f"{x:.1f},{y:.1f}"
        for x, y in data_points
    )

    svg.append(
        f'<polygon points="{data_string}" '
        f'fill="{colors["fill"]}" '
        'fill-opacity="0.22" '
        f'stroke="{colors["stroke"]}" '
        'stroke-width="2.5" '
        'stroke-linejoin="round"/>'
    )

    # Vertices
    for x, y in data_points:

        svg.append(
            f'<circle cx="{x:.1f}" '
            f'cy="{y:.1f}" '
            'r="3.5" '
            f'fill="{colors["vertex"]}"/>'
        )

    # Labels
    for index, (language, value) in enumerate(axes):

        x, y = outer[index]

        label_x = x + size / 2
        label_y = y + center_y

        if x > 15:
            anchor = "start"
            label_x += 8

        elif x < -15:
            anchor = "end"
            label_x -= 8

        else:
            anchor = "middle"

        if y < -15:
            label_y -= 5

        elif y > 15:
            label_y += 17

        svg.append(
            f'<text x="{label_x:.1f}" '
            f'y="{label_y:.1f}" '
            f'text-anchor="{anchor}" '
            'font-size="13" '
            'font-weight="600" '
            f'fill="{colors["label"]}">'
            f'{escape(language)}'
            '</text>'
        )

        svg.append(
            f'<text x="{label_x:.1f}" '
            f'y="{label_y + 14:.1f}" '
            f'text-anchor="{anchor}" '
            'font-size="11" '
            f'fill="{colors["value"]}">'
            f'{value:g}'
            '</text>'
        )

    svg.append("</svg>")

    return "".join(svg)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--github",
        required=True,
    )

    parser.add_argument(
        "-o",
        "--out",
        default="assets/radar-langs",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=7,
    )

    args = parser.parse_args()

    token = (
        os.environ.get("GITHUB_TOKEN")
        or os.environ.get("GH_TOKEN")
    )

    totals = get_languages(
        args.github,
        token,
    )

    if not totals:

        raise SystemExit(
            "No GitHub language data found."
        )

    languages = sorted(
        totals.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:args.limit]

    maximum = languages[0][1]

    axes = []

    for language, value in languages:

        normalized = (
            value / maximum
        ) ** 0.4 * 100

        axes.append(
            (
                language,
                round(normalized, 1),
            )
        )

    output = Path(args.out)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    for theme in (
        "dark",
        "light",
    ):

        svg = render(
            args.github,
            axes,
            theme,
        )

        filename = output.with_name(
            f"{output.name}-{theme}.svg"
        )

        filename.write_text(
            svg,
            encoding="utf-8",
        )

        print(
            f"Generated {filename}"
        )


if __name__ == "__main__":
    main()
