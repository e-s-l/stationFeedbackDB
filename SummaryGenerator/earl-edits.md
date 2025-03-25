# Earl Edits

## The plan:
- the modify the summary generator to:
    - connect to the database as remote
        - using a config file
        - this is for testing
    - construct the summary as a json to be printed
        - simple to pass to the producer
        - since, at heart, json is for objects, this suggests we should have
        StationSummary object...?
    - print via a html/css or latex template
        - easier to format than the raw pdf

## TODO
- create requirements to run in a venv
- use a proper logger

- extract core info from strings (and put the strings into the templates)
- performace metric, is used vs recovered or not?


## What have I done?
- moved the report creation into a seperate file
- 
