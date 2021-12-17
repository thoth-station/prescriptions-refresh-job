Thoth's prescriptions-refresh-job
---------------------------------

A job that keeps `Thoth's prescriptions <https://github.com/thoth-station/prescriptions>`__ up to date.

Environment variables available to run and test the job:
========================================================
- **APP_SCRIPT**
    Path to `app.sh` script
- **GITHUB_APP_ID**
    GitHub Application id for GitHub integration.
- **GITHUB_PRIVATE_KEY_PATH**
    GitHub API secret for GitHub integration.
- **GIT_SSH_COMMAND**
    Helps the server bypass the Host key checking while connecting to github.
- **GOOGLE_APPLICATION_CREDENTIALS**
    Credentials to access BigQuery
- **KNOWLEDGE_GRAPH_DATABASE**
    Database name
- **KNOWLEDGE_GRAPH_HOST**
    Database host
- **KNOWLEDGE_GRAPH_PASSWORD**
    Database password
- **KNOWLEDGE_GRAPH_PORT**
    Database port
- **KNOWLEDGE_GRAPH_SSL_DISABLED**
    Set this environment variable to 1 to disable SSL encryption for database connections
- **KNOWLEDGE_GRAPH_USER**
    Database username
- **PROMETHEUS_PUSHGATEWAY_HOST**
- **PROMETHEUS_PUSHGATEWAY_PORT**
- **SENTRY_DSN**
    A DSN to a Sentry instance to log to.
- **THOTH_DEPLOYMENT_NAME**
    Thoth's deployment name
- **THOTH_LOGGING_NO_JSON**
- **THOTH_PRESCRIPTIONS_REFRESH_CONFIGURED_IMAGES**
- **THOTH_PRESCRIPTIONS_REFRESH_DEBUG**
    Set this environment variable to 1 to print logs from the job
- **THOTH_PRESCRIPTIONS_REFRESH_GITHUB_LABELS**
    Default GitHub labels for automatically generated prescriptions
- **THOTH_PRESCRIPTIONS_REFRESH_GITHUB_TOKEN**
    GitHub token
- **THOTH_PRESCRIPTIONS_REFRESH_QUAY_TOKEN**
    Token taken in quay settings from robot accounts
- **THOTH_PRESCRIPTIONS_REFRESH_RANDOMIZE**
- **THOTH_PRESCRIPTIONS_REFRESH_REPO**
    Prescriptions repository URL
- **THOTH_PRESCRIPTIONS_REFRESH_SUBCOMMAND**
    Command options for prescriptions-refresh-job CLI
