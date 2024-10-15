import requests
import time
import re

from ._decorators import *

from .encryption.srun_md5 import *
from .encryption.srun_sha1 import *
from .encryption.srun_base64 import *
from .encryption.srun_xencode import *

header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36"
}


class LoginManager:
    def __init__(
        self,
        username,
        password,
        url="http://59.67.168.218/",
        path_dict={
            "path_login_page": "/srun_portal_pc?ac_id=8&theme=bit",
            "path_get_challenge_api": "/cgi-bin/get_challenge",
            "path_login_api": "/cgi-bin/srun_portal",
            "path_get_rad_user_info": "/cgi-bin/rad_user_info",
        },
        n="200",
        vtype="1",
        acid="1",
        enc="srun_bx1",
    ):
        self.username = username
        self.password = password
        # urls
        self.url = url.rstrip("/")
        self.path_dict = path_dict
        self.refreash_urls()
        # other static parameters
        self.n = n
        self.vtype = vtype
        self.ac_id = acid
        self.enc = enc
        self.ip = None
        self.client_ip, self.online_ip = None, None

    def login(self,ip=None):
        print(f"login user:{self.username} password:'*'({len(self.password)})")
        self.get_ip(ip)
        if self.online_staute_check():
            print("You are already online.Skipping login.")
            return
        self.get_token()
        self.get_login_responce()

    def logout(self):
        self.get_ip()
        self.online_staute_check()
        params = {
            "callback": "js",
            "action": "logout",
            "username": self.username,
            "ip": self.online_ip,
            "ac_id": self.ac_id,
            "_": int(time.time()),
        }
        r = requests.get(url=self.url_login_api, params=params, headers=header)
        r.encoding = "utf-8"
        error_msg = re.search(r'"error_msg":"([^"]*)"', r.text).group(1)
        if error_msg == "ok":
            print("Logout successfully.")
        else:
            print(f"Logout failed.(error_msg:{error_msg})")

    def get_114(self):
        # r.request
        pass
    def online_staute_check(self):
        #TODO 未实装,待加入检查网络连接状态检测
        if not self.client_ip and self.online_ip:
            print("[online_staute_check]: you are online")
            return True

        if self.client_ip and self.client_ip:
            print("[online_staute_check]: you are online")
            return False
        
        if not self.client_ip and not self.online_ip:
            print("[online_staute_check]: you are not in school network")
            return True


    def refreash_urls(self, url=None):
        if url:
            self.url = url.rstrip("/")
        # 重新构建URL
        self.url_login_page = f"{self.url}{self.path_dict['path_login_page']}"
        self.url_get_challenge_api = (
            f"{self.url}{self.path_dict['path_get_challenge_api']}"
        )
        self.url_login_api = f"{self.url}{self.path_dict['path_login_api']}"
        self.url_get_rad_user_info = (
            f"{self.url}{self.path_dict['path_get_rad_user_info']}"
        )

    def get_ip(self, ip=None):
        print("Step1: Get local ip returned from srun server.")
        self._get_login_page()
        if ip:
            self.ip = ip
            print(f"ip has been define to {ip}.")
        else:
            self._get_ip_from_rad_user_info()
        print("----------------")

    def get_token(self):
        print("Step2: Get token by resolving challenge result.")
        self._get_challenge()
        self._resolve_token_from_challenge_response()
        print("----------------")

    def get_login_responce(self):
        print("Step3: Loggin and resolve response.")
        self._generate_encrypted_login_info()
        self._send_login_info()
        self._resolve_login_responce()
        print("The loggin result is: " + self._login_result)
        print("----------------")

    def _is_defined(self, varname):
        """
        Check whether variable is defined in the object
        """
        allvars = vars(self)
        return varname in allvars

    @infomanage(
        callinfo="Getting login page",
        successinfo="Successfully get login page",
        errorinfo="Failed to get login page, maybe the login page url is not correct",
    )
    def _get_login_page(self):
        # Step1: Get login page
        self._page_response = requests.get(self.url_login_page, headers=header)

    @checkvars(
        varlist="_page_response",
        errorinfo="Lack of login page html. Need to run '_get_login_page' in advance to get it",
    )
    @infomanage(
        callinfo="Resolving IP from login page html",
        successinfo="Successfully resolve IP",
        errorinfo="Failed to resolve IP",
    )
    def _resolve_ip_from_login_pages(self):
        """ """
        self.ip = re.search(
            'id="user_ip" value="(.*?)"', self._page_response.text
        ).group(1)

    def _get_ip_from_rad_user_info(self):
        # if self.ip:
        #     print("IP is already defined to({}).".format(self.ip))
        # else:
        params = {
            "callback": "jsonp1583251661368",  # any str is ok,but can't absent
        }
        response = requests.get(
            self.url_get_rad_user_info,
            params=params,
            headers=header,
            verify=False,
        )
        client_ip_match = re.search(r'"client_ip":"([^"]+)"', response.text)
        online_ip_match = re.search(r'"online_ip":"([^"]+)"', response.text)
        if online_ip_match:
            self.online_ip = online_ip_match.group(1)
            print("Online_ip is {}".format(self.online_ip))

        if client_ip_match:
            self.client_ip = client_ip_match.group(1)
            self.ip = self.client_ip
            print(f"IP has defined to client_ip({self.client_ip}) by get rad info.")

    def show_ip(self):
        self._get_ip_from_rad_user_info()
        cip = self.client_ip if self.client_ip else "Not Found"
        oip = self.online_ip if self.online_ip else "Not Found"
        print(f"Login ip is {self.ip}\nClient ip is {cip} \nOline ip is {oip}")

    @checkip
    @infomanage(
        callinfo="Begin getting challenge",
        successinfo="Challenge response successfully received",
        errorinfo="Failed to get challenge response, maybe the url_get_challenge_api is not correct."
        "Else check params_get_challenge",
    )
    def _get_challenge(self):
        """
        The 'get_challenge' request aims to ask the server to generate a token
        """
        params_get_challenge = {
            "callback": "jsonp1583251661368",  # This value can be any string, but cannot be absent
            "username": self.username,
            "ip": self.ip,
        }

        self._challenge_response = requests.get(
            self.url_get_challenge_api, params=params_get_challenge, headers=header
        )

    @checkvars(
        varlist="_challenge_response",
        errorinfo="Lack of challenge response. Need to run '_get_challenge' in advance",
    )
    @infomanage(
        callinfo="Resolving token from challenge response",
        successinfo="Successfully resolve token",
        errorinfo="Failed to resolve token",
    )
    def _resolve_token_from_challenge_response(self):
        self.token = re.search(
            '"challenge":"(.*?)"', self._challenge_response.text
        ).group(1)

    @checkip
    def _generate_info(self):
        info_params = {
            "username": self.username,
            "password": self.password,
            "ip": self.ip,
            "acid": self.ac_id,
            "enc_ver": self.enc,
        }
        info = re.sub("'", '"', str(info_params))
        self.info = re.sub(" ", "", info)

    @checkinfo
    @checktoken
    def _encrypt_info(self):
        self.encrypted_info = "{SRBX1}" + get_base64(get_xencode(self.info, self.token))

    @checktoken
    def _generate_md5(self):
        self.md5 = get_md5("", self.token)

    @checkmd5
    def _encrypt_md5(self):
        self.encrypted_md5 = "{MD5}" + self.md5

    @checktoken
    @checkip
    @checkencryptedinfo
    def _generate_chksum(self):
        self.chkstr = self.token + self.username
        self.chkstr += self.token + self.md5
        self.chkstr += self.token + self.ac_id
        self.chkstr += self.token + self.ip
        self.chkstr += self.token + self.n
        self.chkstr += self.token + self.vtype
        self.chkstr += self.token + self.encrypted_info

    @checkchkstr
    def _encrypt_chksum(self):
        self.encrypted_chkstr = get_sha1(self.chkstr)

    def _generate_encrypted_login_info(self):
        self._generate_info()
        self._encrypt_info()
        self._generate_md5()
        self._encrypt_md5()

        self._generate_chksum()
        self._encrypt_chksum()

    @checkip
    @checkencryptedmd5
    @checkencryptedinfo
    @checkencryptedchkstr
    @infomanage(
        callinfo="Begin to send login info",
        successinfo="Login info send successfully",
        errorinfo="Failed to send login info",
    )
    def _send_login_info(self):
        login_info_params = {
            "callback": "jsonp1583251661368",  # This value can be any string, but cannot be absent
            "action": "login",
            "username": self.username,
            "password": self.encrypted_md5,
            "ac_id": self.ac_id,
            "ip": self.ip,
            "info": self.encrypted_info,
            "chksum": self.encrypted_chkstr,
            "n": self.n,
            "type": self.vtype,
        }
        self._login_responce = requests.get(
            self.url_login_api, params=login_info_params, headers=header
        )

    def _send_info_logout_info(self):
        login_info_params = {
            "callback": "jsonp1583251661368",  # This value can be any string, but cannot be absent
            "action": "logout",
            "username": self.username,
            "password": self.encrypted_md5,
            "ac_id": self.ac_id,
            "ip": self.ip,
            "info": self.encrypted_info,
            "chksum": self.encrypted_chkstr,
            "n": self.n,
            "type": self.vtype,
        }
        self._login_responce = requests.get(
            self.url_login_api, params=login_info_params, headers=header
        )

    @checkvars(
        varlist="_login_responce",
        errorinfo="Need _login_responce. Run _send_login_info in advance",
    )
    @infomanage(
        callinfo="Resolving login result",
        successinfo="Login result successfully resolved",
        errorinfo="Cannot resolve login result. Maybe the srun response format is changed",
    )
    def _resolve_login_responce(self):
        self._login_result = re.search(
            '"suc_msg":"(.*?)"', self._login_responce.text
        ).group(1)
