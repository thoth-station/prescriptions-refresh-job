Thoth's prescriptions-refresh-job
---------------------------------

A job that keeps `Thoth's prescriptions
<https://github.com/thoth-station/prescriptions>`__ up to date.

Environment variables available to run and test the job:
========================================================

- **APP_SCRIPT**
    Path to `app.sh` script.
- **GITHUB_APP_ID**
    GitHub Application id for GitHub integration.
- **GITHUB_PRIVATE_KEY_PATH**
    GitHub API secret for GitHub integration.
- **GIT_SSH_COMMAND**
    Helps the server bypass the Host key checking while connecting to github.
- **GOOGLE_APPLICATION_CREDENTIALS**
    Credentials to access BigQuery.
- **KNOWLEDGE_GRAPH_DATABASE**
    Database name.
- **KNOWLEDGE_GRAPH_HOST**
    Database host.
- **KNOWLEDGE_GRAPH_PASSWORD**
    Database password.
- **KNOWLEDGE_GRAPH_PORT**
    Database port.
- **KNOWLEDGE_GRAPH_SSL_DISABLED**
    Set this environment variable to 1 to disable SSL encryption for database connections.
- **KNOWLEDGE_GRAPH_USER**
    Database username.
- **PROMETHEUS_PUSHGATEWAY_HOST**
- **PROMETHEUS_PUSHGATEWAY_PORT**
- **SENTRY_DSN**
    A DSN to a Sentry instance to log to.
- **THOTH_DEPLOYMENT_NAME**
    Thoth's deployment name.
- **THOTH_LOGGING_NO_JSON**
- **THOTH_PRESCRIPTIONS_REFRESH_CONFIGURED_IMAGES**
- **THOTH_PRESCRIPTIONS_REFRESH_DEBUG**
    Set this environment variable to 1 to print logs from the job.
- **THOTH_PRESCRIPTIONS_REFRESH_GITHUB_LABELS**
    Default GitHub labels for automatically generated prescriptions.
- **THOTH_PRESCRIPTIONS_REFRESH_GITHUB_TOKEN**
    GitHub token.
- **THOTH_PRESCRIPTIONS_REFRESH_QUAY_TOKEN**
    Token taken in quay settings from robot accounts.
- **THOTH_PRESCRIPTIONS_REFRESH_RANDOMIZE**
- **THOTH_PRESCRIPTIONS_REFRESH_REPO**
    Prescriptions repository URL.
- **THOTH_PRESCRIPTIONS_REFRESH_SUBCOMMAND**
    Command options for prescriptions-refresh-job CLI.
- **THOTH_USER_API_HOST**
    Thoth USER_API host.
- **THOTH_PRESCRIPTIONS_REFRESH_ML_PACKAGES**
    Representative packages for Machine Learning (ML).
- **THOTH_PRESCRIPTIONS_REFRESH_NLP_PACKAGES**
    Representative packages for Natural Language Processing (NLP).
- **THOTH_PRESCRIPTIONS_REFRESH_CV_PACKAGES**
    Representative packages for Computer Vision (CV).
- **THOTH_PRESCRIPTIONS_DRY_RUN**
    If enabled, prescriptions won't be created but only printed in logs.


Running the job locally
=======================

To experiment with changes, it is possible to run the job locally:

.. code-block:: console

  # Install requirements:
  pipenv install --dev

  # To run handlers that reach out to Quay.io:
  export THOTH_PRESCRIPTIONS_REFRESH_QUAY_TOKEN=<quay-token>

  # To open pull-requests or run handlers that reach out to GitHub API:
  export THOTH_PRESCRIPTIONS_REFRESH_GITHUB_TOKEN=<github-token>

  # To run handlers that work with BigQuery
  GOOGLE_APPLICATION_CREDENTIALS=<bigquery.json>

  PYTHONPATH=. pipenv run python3 ./thoth-prescriptions-refresh --help

The job automatically uses Git SSH keys configured, so you need to have proper
Git+SSH setup on your machine.

GitHub token can be obtained in `Personal access token
<https://github.com/settings/tokens>`__ section of your Developer settings.

See `Create OAuth access token
<https://docs.projectquay.io/use_quay.html#_create_oauth_access_token>`__ to
obtain token used for Quay API.

Follow `Authorizing API requests
<https://cloud.google.com/bigquery/docs/authorization>`__ section of BigQuery
docs to obtain BigQuery JSON file with the application credentials.

If the handler that you want to run requires Thoth's database, follow
instructions in `thoth-station/storages
<https://github.com/thoth-station/storages>`__ repository that will guide you
on how to setup a local database. The job, by default, connects to a local
database instance so no changes or environment variables are needed to use the
local database.
