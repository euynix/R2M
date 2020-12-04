# R2M - Scoring System for Marketing Papers

## Anatomy
* `api` - contains back-end models and front-end scripts.
* `nginx` -  popular webserver platform. 
	* Gunicorn is a popular WSGI that works seamlessly with Flask. Flask needs a Web Server Gateway Interface (WSGI) to talk to a web server. Flask's built-in WSGI is not capable of handling production APIs, because it lacks security features and can only run one worker. Gunicorn sets up multiple workers/threads.
* Docker:
    * Docker and docker-compose allow apps to be easily launched in development. 
    * Using docker, we containerize our app to work independently of the environment - specifically, we have 2 separate containers -  `api`, `nginx`

## How to run
* Install `docker` and `docker-compose` for your specific platform (you can easily find instructions on Google)
* Start the app using the following commands inside the root directory:
    ```
    docker-compose build
    docker-compose up
    ```
    * Building the container for the first time will take a while, as it needs to install all requirements.