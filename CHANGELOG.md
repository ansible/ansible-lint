# 3.5.1

Use `yaml.safe_load` for loading the configuration fil
# 3.5.0

* New ids and tags, add doc generator. Old tag names remain backwardly compatible (awcrosby)
* Add more package formats to PackageIsNotLatestRule (simon04)
* Improve handling of meta/main.yml dependencies (MatrixCrawler)
* Correctly handle role argument trailing slash (zoredache)
* Handle `include_task` and `import_task` (zeot)
* Add a new rule to detect jinja in when clauses (greg-hellings)
* Suggest `replace` as another alternative to `sed` (inponomarev)
* YAML syntax highlighting for false positives (gundalow)

# 3.4.23

Fix bug with using comma-separated `skip_list` arguments

# 3.4.22

* Allow `include_role` and `import_role` (willthames)
* Support arbitrary number of exclude flags (KellerFuchs)
* Fix task has name check for empty name fields (ekeih)
* Allow vault encrypted variables in YAML files (mozz)
* Octal permission check improvements - readability, test
  coverage and bug fixes (willthames)
* Fix very weird bug with line numbers in some test environments (kouk)
* Python 3 fixes for octal literals in tests (willthames)
