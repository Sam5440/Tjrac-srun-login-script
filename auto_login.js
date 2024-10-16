// ios快捷

var result = [];

var username = 'demo'; // 改成你的username
var password = 'qwe123'; // 改成你的password

// 填写用户名和密码
var usernameInput = document.getElementById('username'); // 注意和网页的标签名保持一致
var passwordInput = document.getElementById('password');

usernameInput.value = username;
passwordInput.value = password;

// 点击登陆
var loginButton = document.getElementById('login-account'); // 注意和网页的button名保持一致
loginButton.click();


completion(result);