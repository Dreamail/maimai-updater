<div align="center">

# maimai-updater
[![Python3.9+](https://img.shields.io/badge/Python-3.9+-blue)](https://www.python.org)
[![nonebot2](https://img.shields.io/badge/NoneBot2-2.3.1+-red)](https://github.com/nonebot/nonebot2)

基于net友人对战的成绩更新

</div>

## 💿 安装

<details open>
<summary>使用git拉取至本地</summary>
在您本地目录下右键打开git bash, 输入以下指令即可拉取

    git clone https://github.com/Dreamail/maimai-updater.git

</details>

<details>
<summary>下载仓库压缩包</summary>
手动下载仓库压缩包放至本地自建文件夹

</details>

### 请手动添加插件至`bot.py`或`pyprojects.toml`激活插件

## ⚙️ 配置
以下操作请激活虚拟环境后进行（若有）

### 1.补全依赖

    pip install -r requirements.txt

### 2.安装go

前往 https://go.dev/dl/ 下载您对应平台的release文件

<details>
<summary>Linux</summary>

移除所有先前版本并解压您刚刚下载到`/usr/local`的压缩包

    rm -rf /usr/local/go && tar -C /usr/local -xzf go1.23.4.linux-amd64.tar.gz

添加`/usr/local/go/bin`到环境变量

    export PATH=$PATH:/usr/local/go/bin

</details>

<details>
<summary>Windows</summary>

运行您下载的`.msi`安装程序

添加`~/go/bin`至系统环境变量

</details>

### 3.安装gopy

    python3 -m pip install pybindgen
    go install golang.org/x/tools/cmd/goimports@latest
    go install github.com/go-python/gopy@latest

安装python依赖

    python3 -m pip install --upgrade setuptools wheel

### 4.编译pageparser

运行根目录的`build_go.sh`


## 🎉 使用

### 您需要提前准备：能正常访问net且开通微信支付的微信号 一台用于展示登陆二维码的设备

首次运行会私聊SUPERUSER发送模拟电脑登录二维码 请使用微信扫码同意登录

登陆后您的微信上下线、正常电脑登陆均不受影响

|       指令       | 权限 | 需要@ | 范围 |     说明      |
|:--------------:|:----:|:----:|:--:|:-----------:|
|      maip      | 群员 | 否 | 群聊 |   获取指令帮助    |
|      maib      | 群员 | 否 | 群聊 |    绑定账号     |
|      maiu      | 群员 | 否 | 群聊 |    更新成绩     |
| /debug retoken | SUPERUSER | 否 | 私聊 | 重新登录刷新token |

## ⌨  已知问题
### 无法正确获取sync状态

---
# Bilibili UP [さいば](https://t.bilibili.com/854067002885537792) Said:
> 我觉得我有必要反复强调这个办法即使我什么都不做也会失效，这不是我堵死后路的理由，因为他已经是死胡同了。也不要说我这有会加速灭亡，你无法论证我出教程之后腾讯出手的速度就变快了。gocq也活跃了三年，期间那么多教程，难道就能归咎到其中某一个教程的错吗？  
> 刚刚看到某教程网站发布了不要发布的通知。我必须声明这则通知是发布在我视频之后的，依照条文我已删除教程，但这并不是迫于评论区。另外我感到心寒，什么时候助人也成了罪过。也不知道什么时候使用bot也产生了阶级，不懂就不配使用。[干物妹！小埋_无语]  
> 并且，我所使用的插件是一个已经不维护的项目，即使我不做任何教程，他也会失效。  
> 评论区让我看到了人的自私和贪婪，往后我不再做任何教程和帮助，如有问题请自行解决。  
>
> 5.你觉得我没有参与过项目那就没有，因为在发布之前被掐断，不属于成品  
> 6.我在此向曾经不存在的勿传播通知致歉，我不该在你还没出生的时候出教程  
> 11.无论你认为我有什么问题，我都接受，能让你心情舒畅就好  
> ![106d0a856538aa3fd793722d38e90b36](https://github.com/Dreamail/maimai-updater/assets/46253320/e5e6b3db-0992-41a4-b97e-8f16a032392d)
>
> 另外，chro是chro，liteloader是ll，shamrock是shamrock，他们不是同一个东西，我希望某些人不要造谣，这三个东西原本与云崽是毫不相干的，我所提及的官网通知来源于云崽而不是这三者中任何一个。我也从未出过shamrock的任何教程，他们三个的实现环境也完全不一样，特此说明
>
> Oct 19 16:51 original post was deleted