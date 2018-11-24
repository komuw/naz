import naz
cli = naz.Client(
    ...
    log_metadata={
        "env": "prod", "release": "canary", "work": "jira-2345"
        }
)