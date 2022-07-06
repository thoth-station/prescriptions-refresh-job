# Changelog for Thoth's prescriptions refresh job

## Release 0.7.2 (2022-07-06T08:48:33)
* bc4db48 Replace sub-query by ORDER/LIMIT in bigquery job
* cc5d2a7 Add labels to BigQuery queries
* c0ad994 :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* 156b513 Remove destination table from BigQuery config
* d3ee756 :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment

## Release 0.7.1 (2022-06-08T08:14:54)
* 61fa915 Fix pre-commit
* 8300304 Add units
* 1997574 Configure scorecard freshness via env variable
* 99ec726 Select only scorecards updated recently
* c5d56f9 :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment

## Release 0.7.0 (2022-05-23T15:02:20)
* d6b54ca Remove pacospace :(
* d946359 Fix username in maintainers
* d4f7af7 :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* 4a2431a :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* 9217283 Fix duplicate prescription names and pre-commit
* 7356dab :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* 13e9d13 Revert "Fix organization names to string in prescription template"
* 05a85d2 :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* 684ab10 :ship: Bump up base image initialized in CI.
* dd80f1a Fix organization names to string in prescription template
* 474da2a Update security scorecards handler according to new schema
* 55faa72 Get link key and specify default link shortcut
* cc7b625 Default CVE link to no_cve_link_provided justification
* a93da9a :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* 846265b Fix pre-commit
* 62bafce Provide default link for quay clair vulnerabilities
* abcf487 Fix exit code
* 48008aa Handle too many requests error (429) in gh handlers
* a8fd553 :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* 9816428 Fix pre-commit config
* bcd69f2 Remove maintainers section from .thoth.yaml
* 809580a :ship: Bump up base image initialized in CI.
* 63145b2 Update PR template
* 5a613ae Fix container images information handler
* 05b2c05 :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* 02b3056 :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment

## Release 0.6.0 (2022-02-28T22:07:18)
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* Follow redirects for GitHub repos that were transferred (#119)
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* Fix incomplete PR body
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* Fix recommendations for base container images
* Scheme protocol is only for user-API
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* Fix api calls and add PROTOCOL_SCHEMA env variable
* fix README not rendering
* Missed commit suggestion
* Provide representative packages from env variables
* Add chck on env variable
* expose status code in logs
* use quay namespace name env variable
* make env variable optional
* remove recommendation type
* Add also index
* Add warning if no representative packages are identified
* Reuse existing method for generating prescription name
* Update thoth/prescriptions_refresh/handlers/image_analysis.py
* Update thoth/prescriptions_refresh/handlers/image_analysis.py
* Update thoth/prescriptions_refresh/handlers/image_analysis.py
* Update thoth/prescriptions_refresh/cli.py
* Add representative packages
* Finalize logic for new handler
* Add request to User-API
* Add handler for thoth image analysis command
* Fix README formatting
* Add missing Thoth GitHub templates
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* Make justifications for vulnerabilities short
* Document how to run the job locally
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* Fix typos in variables description
* Add descriptions to environment variables
* Fixes for pre-commit
* Describe environment variables used to run the job

## Release 0.5.0 (2021-12-15T16:50:52)
* Apply solver rules to package versions used to generate prescriptions
* Put character between version numbers in pipeline unit names to avoid conflicts
* Propagate information about container images from Quay
* Avoid empty line in prescriptions computing container image alternatives
* Do not quote index_url as pre-commit complains about it
* Fix version range specifier for matching Python versions
* Be consistent with quoting names and versions
* Artifact size is computed per package version
* Introduce handler for computing PyPI artifact size
* Parametrize message with constant supplied
* Relock after rebase
* Update thoth/prescriptions_refresh/handlers/pypi_release.py
* Update thoth/prescriptions_refresh/handlers/pypi_release.py
* Warn if a package has no recent releases
* Fix docstring
* Fix typo in /pypi_maintainers.py
* Fix typo in /pypi_maintainers.py
* Fix typo in /pypi_maintainers.py
* Fix typo in /pypi_maintainers.py
* Compute prescriptions that check maintainers on PyPI
* Add pypi_downloads to __init__.py
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* Fix max dictionary value
* Add dashes to prescription messages
* Fix errors in pre-commit for pypi_downloads.py
* Do a local import for matplotlib
* Minor fix in typing (#70)
* Add a handler for package downloads information (#65)
* Add Maya to OWNERS
* Fix obtaining prescription name
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* Add a general method to Prescriptions to generate prescription names
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* Add Pep to OWNERS file
* Do not fail if Quay returns status code other than 200
* Add also tag part to prescription name in Quay security
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* Use double quotes to make pre-commit happy

## Release 0.4.0 (2021-11-22T19:00:52)
* Compute alternatives to container images with vulnerabilities
* :bomb: use https based url in the pre-commit
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* Keep datetime in the Quay security timestamp boot in metadata
* Sort response from Quay API to keep prescription changes consistent
* Add handler computing Thoth statistics

## Release 0.3.0 (2021-11-08T19:58:45)
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* Create boot for gating CVE issues in the runtime environment
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* Make the message multi-line to conform yamllint
* Correctly escape backslash before serializing to YAML
* Features can be null
* Use generators instead of loading all the container images at once

## Release 0.2.0 (2021-10-25T21:06:16)
* Add handler for security information from Quay on predictable stacks
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* Introduce a task that flags projects with a lot of CVE vulnerabilities

## Release 0.1.0 (2021-10-20T02:36:37)
* Query only GitHub repos in Scorecards BigQuery
* Use BigQuery to obtain prescriptions
* Add prescriptions related to Security Scorecards

## Release 0.0.3 (2021-10-11T20:17:01)
### Features
* Adjust help message to respect implementation
* Remove unused ignore comments reported by mypy
* Create a pool of tokens that can be used to obtain data from GitHub API
* Randomize prescriptions walk if configured so
* :arrow_up: Automatic update of dependencies by Kebechet for the ubi8 environment
* Implement handlers used to aggregate projects stats from GitHub

## Release 0.0.2 (2021-09-12T20:07:18)
### Features
* Add missing continue causing misleading info message printed
* Fixes to conform yamllint setup in the prescriptions repository
* Fixes to conform yamllint setup in the prescriptions repository

## Release 0.0.1 (2021-08-27T11:17:48)
### Features
* Initial project import
* Initial project implementation

## [0.0.0] - 2021-Aug-31 - fridex

### Added

* initial project import
