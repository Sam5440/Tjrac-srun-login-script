from BitSrunLogin.LoginManager import LoginManager

# load json from local config.json
import json

with open("config.json", "r") as f:
    config = json.load(f)
# print(config)
lm = LoginManager(
    username=config["username"],
    password=config["password"],
    # url=config["url"],

)
# lm.logout()
lm.login()
# lm.show_ip()
lm.online_staute_check()


# lm.logout()
