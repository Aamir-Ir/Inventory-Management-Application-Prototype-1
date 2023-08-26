# Inventory-Management-Application-Prototype-1

# WebApp Deployment and Dependencies Documentation

This documentation provides a step-by-step guide on how to deploy the given web application on a server, along with the necessary dependencies and configurations.

## Table of Contents
1. [Introduction](#introduction)
2. [Dependencies](#dependencies)
3. [SQL Server Table Creation](#sql-server-setup)
4. [Deployment Steps](#deployment-steps)

## 1. Introduction<a name="introduction"></a>
This web application is built using Flask and relies on various libraries and dependencies to function properly. The application includes multiple files, including Flask code, SQL handling scripts, and HTML templates.

## 2. Python Dependencies<a name="dependencies"></a>
Before deploying the web application, make sure you have the following Python dependencies installed:

- [Flask](https://pypi.org/project/Flask/)
- [sqlite3](https://docs.python.org/3/library/sqlite3.html)
- [requests](https://pypi.org/project/requests/)
- [aspose.pdf](https://pypi.org/project/aspose-python/)
- [reportlab](https://pypi.org/project/reportlab/)
- [flask_session](https://pypi.org/project/Flask-Session/)

You can install these dependencies using the following command:

```bash
pip install Flask sqlite3 requests aspose-python reportlab Flask-Session


## 3. SQLite3 Table View<a name="sql-server-setup"></a>
When you run the program make sure to have the extenstions allowing you to see all the changes you made to the database.

## Tables Creation Taken Care of in Backend

## 4. Deployment Steps<a name="deployment-steps"></a>
Follow these steps to deploy the web application:

1. **Clone the Repository**: Clone the repository or transfer the necessary files to your server.

2. **Navigate to Root Directory**: Open a terminal on the server and navigate to the root directory of the web application.

3. **Install Dependencies**: Install the required dependencies as mentioned in the "Dependencies" section.

4. **Start the program**: While in the root directory of the web application run ```python app.py```
