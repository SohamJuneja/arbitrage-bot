# AI-Powered DeFi Arbitrage Bot

## Overview
Welcome to the AI-Powered DeFi Arbitrage Bot, designed to operate seamlessly on the Injective Chain. This bot leverages AI to analyze data, predict trends, and execute arbitrage trades, providing a powerful tool for DeFi enthusiasts.

## Key Features
- **Real-time data analysis**: Stay informed with immediate insights.
- **Predictive analytics**: Utilize machine learning for accurate forecasting.
- **Automated trade execution**: Act on decisions without delay on the Injective Chain.
- **Flexible configurations**: Customize settings to suit various trading scenarios.
- **Simple setup**: Minimal dependencies for a quick and hassle-free start.

## Requirements
Ensure you have Python 3.12+ installed. All required packages are listed in `requirements.txt`.

## Installation

### Option 1: Local Installation
1. Clone this repository and navigate into it:
    ```sh
    git clone https://github.com/InjectiveLabs/iAgent.git
    cd iAgent
    ```
2. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```
3. Setup OpenAI API Key:
    ```sh
    export OPENAI_API_KEY="your_openai_api_key_here"
    ```

### Option 2: Docker Installation
1. Clone the repository:
    ```sh
    git clone https://github.com/InjectiveLabs/iAgent.git
    cd iAgent
    ```
2. Build the Docker image:
    ```sh
    docker build -t injective-agent .
    ```
3. Run the container:
    ```sh
    docker run -d \
      -p 5000:5000 \
      -e OPENAI_API_KEY="<YOUR_OPENAI_API_KEY_GOES_HERE>" \
      --name injective-agent \
      injective-agent
    ```

## Running the Bot
To start the backend on a specified port (default is 5000), run:
```sh
python agent_server.py --port 5000
```
Once the bot is running, you can use `quickstart.py` to connect to it and interact with it via URL:
```sh
python quickstart.py --url http://0.0.0.0:5000
```

## AI Agent Usage Guide
This guide will help you get started with the AI Agent, including how to use commands, switch networks, and manage agents. New agents can be saved and updated in the `agents_config.yaml` file.

### Commands Overview
The AI Agent supports several commands categorized into general actions, network configurations, and agent management.

#### General Commands
| Command | Description |
|---------|-------------|
| `quit`  | Exit the agent session. |
| `clear` | Clear the current session output. |
| `help`  | Display help information. |
| `history` | Show command history in the session. |
| `ping` | Check the agent's status. |
| `debug` | Toggle debugging mode. |
| `session` | Display current session details. |

#### Network Commands
| Command | Description |
|---------|-------------|
| `switch_network` | Switch between mainnet and testnet environments. |

#### Agent Management Commands
| Command | Description |
|---------|-------------|
| `create_agent` | Create a new AI agent. |
| `delete_agent` | Delete an existing AI agent. |
| `switch_agent` | Switch to a different AI agent. |
| `list_agents` | Display a list of available agents. |

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request.