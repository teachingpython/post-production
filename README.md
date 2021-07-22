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
- AssemblyAI transcription
    - Speaker labeling
    - Word boosting
    - Job status polling
## Planned Features
- S3-compatible storage
- Local transcoding using ffmpeg to mp3 format
- Webhook callbacks to avoid job status polling

## Example
![](docs/images/tty.gif)
## Installation
Note: This project uses poetry and assumes you have it installed. [Directions](https://python-poetry.org/docs/#installation)

1. Clone or download the project from the repository
1. `poetry install`
1. `poetry run tppp INPUTFILE`
## Configuration
### Dolby.io API key
This project requires a [Dolby.io](https://dolby.io/) API key. You can get one for free from [here](https://dolby.io/signup). As of July 2021, they are offering 200 free minutes of media processing per month.

You can set your API key as an environment variable ('DOLBY_API_KEY') or in a .env file at the root of the project.
### AssemblyAI API key
This project requires an [AssemblyAI](https://app.assembly.ai) API key. You can get one for free from [here](https://app.assemblyai.com/login/). As of July 2021, they are offering the first 5 hours of transcription for free.

You can set your API key as an environment variable ('DOLBY_API_KEY') or in a .env file at the root of the project.