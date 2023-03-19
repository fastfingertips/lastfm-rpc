## Last.fm RPC

Last.fm RPC is a Python script that allows you to display your currently playing track on Last.fm as your Discord Rich Presence status. It uses the Last.fm API and the pypresence library to update your status in real time, providing a seamless integration between Last.fm and Discord.

## Installation

To use Last.fm RPC, you will need to have Python 3.x installed on your computer. You can download the latest version of Python from the official website.

Once you have Python installed, you can download the Last.fm RPC script from this repository. You will also need to install the `pylast` and `pypresence` libraries. You can do this by running the following command in your terminal or command prompt:

```
pip install pylast pypresence
```

## Usage

To use Last.fm RPC, you will need to edit the `config.yaml` file with your Last.fm API key and secret, as well as your Discord application ID. You can find instructions for obtaining these values in the comments at the top of the `config.yaml` file.

Once you have edited the `config.yaml` file, you can run the script by opening a terminal or command prompt in the same directory as the script and running the following command:

The script will start running and will automatically update your Discord Rich Presence status whenever you start playing a new track on Last.fm.

## Contributing

If you would like to contribute to Last.fm RPC, you are welcome to submit pull requests or open issues on the GitHub repository. Please be sure to read the contributing guidelines before making any contributions.

## License

Last.fm RPC is licensed under the MIT License. See the LICENSE file for more information.
