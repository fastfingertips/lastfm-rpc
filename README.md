### Demo

https://github.com/user-attachments/assets/396ef42b-7929-4dac-b8d2-ce43172470f7

### Clone the Repository

To clone the repository, use the following command:

```bash
git clone https://github.com/fastfingertips/lastfm-rpc.git
```

### Install Dependencies

To install dependencies, use the `requirements.txt` file and run the following command:

```bash
pip install -r requirements.txt
```

### Create Last.fm API

To create an API, visit the following link:

[Create Last.fm API](https://www.last.fm/api/account/create)

To view the APIs you have created, visit:

[View Your APIs](https://www.last.fm/api/accounts)

Place the API key and secret key you created in the `config.yaml` file. Also, enter your username in the same file.

### Running the Application

To start the application, you can use one of the following batch files:

1. **start.bat**: This runs the application using `pythonw`, allowing you to close the terminal after starting the application.
2. **test_start.bat**: This runs the application using `python`, allowing you to see the output and logs in the terminal.

Navigate to the project directory and double-click the batch file of your choice:

- `start.bat` for running the application without a terminal.
- `test_start.bat` for running the application with terminal output.

This setup will allow you to display your current listening activity on Last.fm as your Discord status.