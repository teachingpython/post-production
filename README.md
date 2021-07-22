# Teaching Python Post-production CLI

This program is an experiment to see if we can use 
Python to automate our post-production steps.

We are setting this up as a series of command-line programs, 
but eventually want to turn this into an automated pipeline of tasks.
## Current Features
- Dolby.io Client
    - Audio Enhancement
    - Audio and Speech Analysis
    - Job status polling

## Planned Features
- S3-compatible storage
- Local transcoding using ffmpeg to mp3 format
- AssemblyAI transcription
- Webhook callbacks to avoid job status polling

## Installation
Note: This project uses poetry and assumes you have it installed. [Directions](https://python-poetry.org/docs/#installation)

1. Clone or download the project from the repository
1. `poetry install`
1. `poetry run tppp INPUTFILE`

## Example
![](docs/images/tty.gif)

### Dolby.io API key
This project requires a [Dolby.io](https://dolby.io/) API key. You can get one for free from [here](https://dolby.io/signup). As of July 2021, they are offering 200 free minutes of media processing per month.

You can set your API key as an environment variable ('DOLBY_API_KEY') or in a .env file at the root of the project.
