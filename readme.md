# BFS自动签到脚本

## Power by God

![我的头像](https://avatars.githubusercontent.com/u/63219645?s=96&v=4)

## 前期准备

1. python版本为3.9
2. 执行以下命令安装支持环境

    pip install -r requirement.txt

## 更新日志

V1.0

## 消息类型说明

| 编号 | 类型          |   说明    | 发送消息                   | 回复消息                                                                                                         | 备注                      |
|----|-------------|:-------:|------------------------|--------------------------------------------------------------------------------------------------------------|-------------------------|
| 1  | server_time | 获取服务器时间 | {"type": "systemTime"} | {"type": "systemTime", "error": "", "from": "system", "to": "zhanghaoran", "message": "2023-05-23 16:20:38"} |                         |
| 2  | sign_in     |   签入    | {"type":"signIn"}      | {"type": "signIn", "error": "", "from": "system", "to": "zhanghaoran", "message": {"result": true}}          | 如果未签出就签入，会直接成功，需要主动判断！  |
| 3  | sign_out    |   签出    | {"type":"signOut"}     | {"type": "signOut", "error": "", "from": "system", "to": "zhanghaoran", "message": {"result": true}}         | 晚上8点之后签出需要先填写日报（服务器端判断） |
|    |             |         |                        |                                                                                                              |                         |
|    |             |         |                        |                                                                                                              |                         |

