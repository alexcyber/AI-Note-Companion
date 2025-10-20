import os
from dotenv import dotenv_values

def load_env():
    dotenv_values()
    return dotenv_values(".env")

if __name__ == "__main__":
    env_vars = load_env()
    print("Enviornment variables")
    for key, value in env_vars.items():
        print(f"{key} = {value}")