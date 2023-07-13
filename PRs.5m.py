#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# <xbar.title>Github PRs</xbar.title>
# <xbar.desc>Shows a list of PRs you're part of</xbar.desc>
# <xbar.version>v0.1</xbar.version>
# <xbar.author>Bernard Mak</xbar.author>
# <xbar.author.github>BMak-theScore</xbar.author.github>
# <xbar.dependencies>python</xbar.dependencies>

# ----------------------
# ---  BEGIN CONFIG  ---
# ----------------------

# https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/
ACCESS_TOKEN = 'github_access_token'

GITHUB_LOGIN = 'github_login'

# (optional) PRs with this label (e.g 'in progress') will be grayed out on the list
WIP_LABEL = 'WIP'

# (optional) Filter the PRs by an organization, labels, etc. E.g 'org:YourOrg -label:dropped'
FILTERS = 'extra_filters'

# --------------------
# ---  END CONFIG  ---
# --------------------

import datetime
import json
import os
import sys

try:
    # For Python 3.x
    from urllib.request import Request, urlopen
except ImportError:
    # For Python 2.x
    from urllib2 import Request, urlopen


query = """{
  search(query: "%(search_query)s", type: ISSUE, first: 100) {
    issueCount
    edges {
      node {
        ... on PullRequest {
          repository {
            name
          }
          author {
            login
          }
          createdAt
          number
          url
          title
          labels(first:100) {
            nodes {
              name
            }
          }
        }
      }
    }
  }
}"""


colors = {
    "owned": "#1974D2",
    "reviewed": "#F8ED62",
    "subtitle": "#586069",
    "unreviewed": "#339933"
}


def execute_query(query):
    headers = {
        "Authorization": "bearer " + ACCESS_TOKEN,
        "Content-Type": "application/json",
    }
    data = json.dumps({"query": query}).encode("utf-8")
    req = Request("https://api.github.com/graphql", data=data, headers=headers)
    body = urlopen(req).read()
    return json.loads(body)


def repo_query_key(repo):
    return "repo:%(repo)s" % {"repo": repo}


def search_pull_requests_requested_review():
    search_query = f'type:pr state:open -author:@me review-requested:@me {FILTERS}'
    response = execute_query(query % {"search_query": search_query})
    return response["data"]["search"]


def search_pull_requests_reviewed_by():
    search_query = f'type:pr state:open -author:@me reviewed-by:@me {FILTERS}'
    response = execute_query(query % {"search_query": search_query})
    return response["data"]["search"]


def search_owned_pull_requests():
    search_query = f'type:pr state:open author:@me {FILTERS}'
    response = execute_query(query % {'search_query': search_query})
    return response['data']['search']


def parse_date(text):
    date_obj = datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
    return date_obj.strftime("%B %d, %Y")


def print_line(text, **kwargs):
    params = " ".join(["%s=%s" % (key, value) for key, value in kwargs.items()])
    print("%s | %s" % (text, params) if kwargs.items() else text)


def sanitize_title(text):
    sanitized = text.replace("|", "_")
    return sanitized

def output_edges(edges, colour):
    for pr in [r["node"] for r in edges]:
        display_name = pr["repository"]["name"]
        title = "%s - %s" % (display_name, pr["title"])
        subtitle = "#%s opened on %s by @%s" % (
            pr["number"],
            parse_date(pr["createdAt"]),
            pr["author"]["login"],
        )
        print_line(
            sanitize_title(title),
            size=16,
            color=colors.get(colour),
            href=pr["url"]
        )
        print_line(sanitize_title(subtitle), size=12, color="subtitle")
        print_line("---")



if __name__ == "__main__":
    if not all([ACCESS_TOKEN, GITHUB_LOGIN]):
        print_line("⚠ Github review requests", color="red")
        print_line("---")
        print_line("ACCESS_TOKEN and GITHUB_LOGIN cannot be empty")
        sys.exit(0)

    prs_requested_reviews = search_pull_requests_requested_review()
    prs_reviewed_by = search_pull_requests_reviewed_by()
    prs_owned = search_owned_pull_requests()
    print_line("Requested #%s" % prs_requested_reviews["issueCount"])
    print_line("Opened #%s" % prs_owned["issueCount"])
    print_line("Reviewed #%s" % prs_reviewed_by["issueCount"])
    print_line("---")

    output_edges(prs_requested_reviews["edges"], "unreviewed")
    output_edges(prs_owned["edges"], "owned")
    output_edges(prs_reviewed_by["edges"], "reviewed")
