# BuyBuddy

![Screenshot of the BuyBuddy app](https://github.com/BustosAndrew/buybuddyapp/blob/main/buybuddy.png)

## Overview

This is a python web app using Streamlit, Google OAuth, and ChatGPT API to facilitate realistic product recommendations from Amazon.

## Installation

1. Clone the repository

```bash
git clone https://github.com/BustosAndrew/buybuddyapp.git
```

2. Create a `.env` file based on the `.env.example` file inside the `src` directory and add your `OPENAI_API_KEY`

```bash
OPENAI_API_KEY=yourapikey
```

3. Create and activate a new virtual environment

```bash
python -m venv env
source env/bin/activate
```

4. Move to project directory

```bash
cd buybuddyapp
```

5. Install the required packages

```bash
pip install -r requirements.txt
```

6. Run the Streamlit application

```bash
streamlit run src/main.py
```

## Usage

Once the application is running, you can interact with it by following the on-screen instructions at `http://localhost:8080`

## My Code

https://github.com/BustosAndrew/buybuddyapp/blob/a9c94da4cd32b0ab11b6b48a8220f188311ae5ab/functions/amazon.py#L1-L134

https://github.com/BustosAndrew/buybuddyapp/blob/a9c94da4cd32b0ab11b6b48a8220f188311ae5ab/main.py#L1-L257

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License
