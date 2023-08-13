# Youtube to Article
Web App to automatic creation of a text publication based on a youtube video

## Features

* Backend API on Fast API
* The text from the video is obtained by subtitle extraction paths, or if there are none, by using the Whisper library deployed in a Docker container
* The gpt4free library is used to produce formatted text, and the neural network is used to process raw text
* Class based answer
* Screenshots from video created by  OpenCV labrary, may save on server or imgurAPI

## Usage

* 📌 Сlone repo
* 📎 Install requirements from `requirements.txt`
* Docker-composu build \ up for Whisper container
