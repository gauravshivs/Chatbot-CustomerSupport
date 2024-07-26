## Overview

This project provides a pipeline to ingest data, serve it using FastAPI, run tests with Pytest, document and test the API using Swagger, and finally, present results with Streamlit.

## Table of Contents
1. [Setup and Installation](#setup-and-installation)
2. [Using AWS Bedrock](#using-aws-bedrock)
2. [Ingestion](#ingestion)
3. [Starting the FastAPI Server](#starting-the-fastapi-server)
4. [Running Tests with Pytest](#running-tests-with-pytest)
5. [API Documentation and Testing with Swagger](#api-documentation-and-testing-with-swagger)
6. [Visualizing with Streamlit](#visualizing-with-streamlit)


## Setup and Installation

1. **Clone the repository** (if applicable) or download the script.

2. **Create and Activate a Virtual Environment**:
   Creating a virtual environment is a best practice to manage dependencies and isolate your project environment.

   - **For Windows**:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```

   - **For macOS and Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

   This will create a virtual environment named `venv` and activate it. Once activated, your command prompt will change to show the name of the environment.

3. **Dependencies**
Install the necessary dependencies listed in `requirements.txt`.

```bash
pip install -r requirements.txt
```

## Using AWS Bedrock

AWS Bedrock is a service for deploying and managing machine learning models. To use AWS Bedrock:

1. **Set Up AWS CLI:**
   - If you haven't set up the AWS CLI, follow the instructions in the [AWS CLI User Guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html).

2. **Authenticate with AWS:**
   - Run `aws configure` and enter your AWS credentials (Access Key, Secret Key, region, etc.).

3. **Deploy and Manage Models:**
   - Use the AWS Bedrock CLI commands to deploy and manage your machine learning models. For detailed instructions, refer to the [AWS Bedrock documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html)

## Ingestion

The ingestion process is handled by the script `ingest.py`. This script reads data from the provided sources and processes it for further use.

### Running the Ingestion Script

To run the ingestion script execute:

```bash
python src/ingest.py /path/to/file1.pdf /path/to/file2.txt /path/to/file3.pdf
```

Parameters:

	•	Replace /path/to/file1.pdf, /path/to/file2.txt, etc., with the actual paths to your PDF and TXT files.

Ensure all necessary data sources are accessible and properly configured in the script.


## Starting the FastAPI Server

The API is powered by FastAPI, which is a modern, fast (high-performance) web framework for building APIs with Python.

### Running the FastAPI Server

To start the FastAPI server, execute the following command in the `src` directory:

```bash
uvicorn main:app --reload
```

The server will start on `http://127.0.0.1:8000`. The `--reload` flag is useful during development as it reloads the server upon changes.

## Running Tests with Pytest

Testing is an integral part of the development process. We use Pytest to ensure our API and data processing scripts work correctly.

### Running the Tests

To run the test, use the following command:

```bash
pytest pytest_fastapi.py
```

This command will discover and run all the unit test cases.

## API Documentation and Testing with Swagger

FastAPI automatically generates interactive API documentation with Swagger UI, which is accessible when the server is running.

### Accessing Swagger UI

To view the Swagger UI, navigate to `http://127.0.0.1:8000/docs` in your web browser. This interface allows you to test the API endpoints directly from your browser.

## Visualizing with Streamlit

Streamlit is used for interactive visualizations and data presentation. To run the Streamlit app:

### Running Streamlit

1. Ensure the FastAPI server is running.
2. Navigate to the directory containing the Streamlit script (`app.py` in your project structure).
3. Run the following command:

```bash
streamlit run app.py
```

The Streamlit app will be accessible at `http://localhost:8501`.




## Conclusion

This project demonstrates a full pipeline from data ingestion to chat. Each component can be developed and tested independently, ensuring a modular and scalable approach to building data-driven applications.

For any further questions or issues, please consult the individual documentation for FastAPI, Pytest, Streamlit, and AWS services.
