# ShadowrocketConfig

A repository for shadowrocket

## 1.配置说明

```markdown
[General]

# 旁路系统。如果禁用此选项，可能会导致一些系统问题，如推送通知延迟。

bypass-system = true

# 跳过代理。此选项强制这些域名或 IP 的连接范围由 Shadowrocket TUN 接口来处理，而不是 Shadowrocket 代理服务器。此选项用于解决一些应用程序的一些兼容性问题。

skip-proxy = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, localhost, _.local, captive.apple.com,_.ccb.com,_.abchina.com.cn,_.psbc.com

# TUN 旁路路由。Shadowrocket TUN 接口只能处理 TCP 协议。使用此选项可以绕过指定的 IP 范围，让其他协议通过。

tun-excluded-routes = 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.0.0.0/24, 192.0.2.0/24, 192.88.99.0/24, 192.168.0.0/16, 198.51.100.0/24, 203.0.113.0/24, 224.0.0.0/4, 255.255.255.255/32, 239.255.255.250/32

# DNS 覆写。使用普通 DNS 或加密 DNS（如 doh、doq、dot 等）覆盖默认的系统 DNS。有些 dns over https 支持 http3，所以尝试查询，如果支持就切换到 http3。可在 doh 链接后面加上#no-h3 关闭。

dns-server = https://doh.pub/dns-query,https://dns.alidns.com/dns-query,223.5.5.5,119.29.29.29

# 备用 DNS。当覆写的 DNS 解析失败后回退备用 DNS，如需指定多个 DNS，可用逗号分隔。system 表示回退到系统 DNS。

fallback-dns-server = system

# 启用 IPv6 支持。false 表示不启用，true 表示启用。

ipv6 = false

# 首选 IPv6。优先向 IPv6 的 DNS 服务器查询 AAAA 记录，优先使用 AAAA 记录。false 表示不启用。

prefer-ipv6 = false

# 域名直接使用系统 DNS 进行解析。false 表示不启用。

dns-direct-system = false

# ping 数据包自动回复。

icmp-auto-reply = true

# 不开启时，REJECT 策略默认只有在配置模式下生效。开启后，可以令该策略在其他全局路由模式下都生效。

always-reject-url-rewrite = false

# 私有 IP 应答。如果不启用该选项，域名解析返回私有 IP，Shadowrocket 会认为该域名被劫持而强制使用代理。

private-ip-answer = true

# 直连域名解析失败后使用代理。false 表示不启用。

dns-direct-fallback-proxy = false

# 当 UDP 流量匹配到规则里不支持 UDP 转发的节点策略时重新选择回退行为，可选行为包括 DIRECT、REJECT。DIRECT 表示直连转发 UDP 流量，REJECT 表示拒绝转发 UDP 流量。

udp-policy-not-supported-behaviour = REJECT

# 包含配置。如“include=a.conf”表示当前配置包含另一个配置 a.conf 的内容，当前配置的优先级高于 a.conf。该选项是对配置建立包含关系，以满足同时使用多个配置的需求。

include =

[Proxy]

# 添加本地节点。

# Shadowsocks 类型：

# 节点名称=ss,地址,端口,password=密码,其他参数(如 method=aes-256-cfb,obfs=websocket,plugin=none)

# Vmess 类型：

# 节点名称=vmess,地址,端口,password=密码,其他参数(如 alterId=0,method=auto,obfs=websocket,tfo=1)

# VLESS 类型：

# 节点名称=vless,地址,端口,password=密码,tls=true,其他参数(如 obfs=websocket,peer=example.com)

# HTTP/HTTPS/Socks5/Socks5 Over TLS 等类型：

# 节点名称=http,地址,端口,用户,密码

# 节点名称=https,地址,端口,用户,密码

# 节点名称=socks5,地址,端口,用户,密码

# 节点名称=socks5-tls,地址,端口,用户,密码,skip-common-name-verify=true

# Trojan 类型：

# 节点名称=trojan,地址,端口,password=密码,其他参数(如 allowInsecure=1,peer=example.com)

[Proxy Group]

# 代理分组类型：

# select:手动选择节点。

# url-test:自动选择延迟最低节点。

# fallback:节点挂掉时自动切换其他可用节点。

# load-balance:不同规则的请求使用分组里的不同节点进行连接。

# random:随机使用分组里的不同节点进行连接。

# ----------

# policy-regex-filter 表示正则式或关键词筛选，常用写法：

# 筛选保留节点名称含有关键词 A 和 B 的节点:

# (?=._(A))^(?=._(B))^.\*$

# 筛选保留节点名称含有关键词 A 或 B 的节点:

# A|B

# 筛选排除节点名称含有关键词 A 或 B 的节点:

# ^((?!(A|B)).)\*$

# 筛选保留节点名称含有关键词 A 并排除含有关键词 B 的节点:

# (?=._(A).)^((?!(B)).)_$

# ----------

# 代理分组其他设置参数：

# interval:指定间隔多长时间后需要重新发起测试。

# timeout:如果测试在超时前未完成，放弃测试。

# tolerance:只有当新优胜者的分数高于旧优胜者的分数加上公差时，才会进行线路更换。

# url:指定要测试的 URL。

# ----------

# 不含正则筛选的代理分组，示例：

# 名称=类型(如 select,url-test,fallback,load-balance,random),策略(如 direct,proxy,订阅名称,代理分组,节点),interval=测试周期,timeout=超时时间,tolerance=公差,select=默认策略(0 表示第一个策略,1 表示第二个策略,2 表示第三个策略……),url=测试地址

# 含正则筛选的代理分组，示例：

# 名称=类型(如 select,url-test,fallback,load-balance,random),policy-regex-filter=正则式或关键词筛选,interval=测试周期,timeout=超时时间,tolerance=公差,select=默认策略(0 表示第一个策略,1 表示第二个策略,2 表示第三个策略……),url=测试地址

# ----------

[Rule]

# 规则类型：

# DOMAIN-SUFFIX：匹配请求域名的后缀。如“DOMAIN-SUFFIX,example.com,DIRECT”可以匹配到“a.example.com、a.b.example.com”。

# DOMAIN-KEYWORD：匹配请求域名的关键词。如“DOMAIN-KEYWORD,exa,DIRECT”可以匹配到“a.example.com、a.b.example.com”。

# DOMAIN：匹配请求的完整域名。如“DOMAIN,www.example.com,DIRECT”只能匹配到“www.example.com”。

# USER-AGENT：匹配用户代理字符串，支持使用通配符“_”。如“USER-AGENT,MicroMessenger_,DIRECT”可以匹配到“MicroMessenger Client”。

# URL-REGEX：匹配 URL 正则式。如“URL-REGEX,^https?://.+/item.+,REJECT”可以匹配到“https://www.example.com/item/abc/123”。

# IP-CIDR：匹配 IPv4 或 IPv6 地址。如“IP-CIDR,192.168.1.0/24,DIRECT,no-resolve”可以匹配到 IP 段“192.168.1.1 ～ 192.168.1.254”。规则加 no-resolve 时，IP 请求会匹配到这条规则，而域名请求不会用解析出来的 IP 去匹配这条规则。规则不加 no-resolve 时，则 IP 请求可匹配，域名解析后的 IP 也可匹配。

# IP-ASN：匹配 IP 地址隶属的 ASN 编号。如“IP-ASN,56040,DIRECT”可以匹配到微信的相关 IP 请求。

# RULE-SET：匹配规则集内容。规则集的组成部分需包含规则类型。

# DOMAIN-SET：匹配域名集内容。域名集的组成部分不包含规则类型。

# SCRIPT：匹配脚本名称。

# DST-PORT：匹配目标主机名的端口号。如“DST-PORT,443,DIRECT”可以匹配到 443 目标端口。

# GEOIP：匹配 IP 数据库。如“GEOIP,CN,DIRECT”可以匹配到归属地为 CN 的 IP 地址。

# FINAL：兜底策略。如“FINAL,PROXY”表示当其他所有规则都匹配不到时才使用 FINAL 规则的策略。

# AND：逻辑规则，与规则。如“AND,((DOMAIN,www.example.com),(DST-PORT,123)),DIRECT”可以匹配到“www.example.com:123”。

# NOT：逻辑规则，非规则。如“NOT,((DST-PORT,123)),DIRECT”可以匹配到除了“123”端口的其他所有请求。

# OR：逻辑规则，或规则。如“OR,((DST-PORT,123),(DST-PORT,456)),DIRECT”可以匹配到“123”或“456”端口的所有请求。

# ----------

# 规则策略：

# PROXY：代理。通过首页正在使用的代理服务器转发流量。

# DIRECT：直连。连接不经过任何代理服务器。

# REJECT：拒绝。返回 HTTP 状态码 404，没有内容。

# REJECT-DICT：拒绝。返回 HTTP 状态码 200，内容为空的 JSON 对象。

# REJECT-ARRAY：拒绝。返回 HTTP 状态码 200，内容为空的 JSON 数组。

# REJECT-200：拒绝。返回 HTTP 状态码 200，没有内容。

# REJECT-IMG：拒绝。返回 HTTP 状态码 200，内容为 1 像素 GIF。

# REJECT-TINYGIF：拒绝。返回 HTTP 状态码 200，内容为 1 像素 GIF。

# REJECT-DROP：拒绝。丢弃 IP 包。

# REJECT-NO-DROP：拒绝。返回 ICMP 端口不可达。

# 除此之外，规则策略还可以选择「代理分组」、「订阅名称」、「分组」、「节点」。

# ----------

# 规则匹配的优先级：

# 1.规则从上到下依次匹配。

# 2.域名规则优先于 IP 规则。

# ----------

# 关于屏蔽 443 端口的 UDP 流量的解释内容：HTTP3/QUIC 协议开始流行，但是国内 ISP 和国际出口的 UDP 优先级都很低，表现很差，屏蔽掉以强制回退 HTTP2/HTTP1.1。（如需启用该逻辑规则，请删除 AND 前面的注释符号#）

# AND,((PROTOCOL,UDP),(DST-PORT,443)),REJECT-NO-DROP

# ----------

# 直连策略的修正规则集。

RULE-SET,https://url/add_rule/main/direct-amend.list,DIRECT

# 代理策略的修正规则集。

RULE-SET,https://url/add_rule/main/proxy-amend.list,PROXY

# 国外常用 app 单独分流：YouTube，Netflix，Disney+，HBO，Spotify，Telegram，PayPal，Twitter，Facebook，Google，TikTok，GitHub，Speedtest。

# 国内常用 app 单独分流：苹果服务，微软服务，哔哩哔哩，网易云音乐，游戏平台，亚马逊，百度，豆瓣，微信，抖音，微博，知乎，小红书。

RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Apple/Apple.list,DIRECT
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/BiliBili/BiliBili.list,DIRECT
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/NetEaseMusic/NetEaseMusic.list,DIRECT
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Baidu/Baidu.list,DIRECT
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/DouBan/DouBan.list,DIRECT
RULE-SET,https://url/ios_rule_script/master/rule/QuantumultX/WeChat/WeChat.list,DIRECT
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/DouYin/DouYin.list,DIRECT
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Weibo/Weibo.list,DIRECT
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Zhihu/Zhihu.list,DIRECT
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/XiaoHongShu/XiaoHongShu.list,DIRECT
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/YouTube/YouTube.list,PROXY
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Netflix/Netflix.list,PROXY
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Disney/Disney.list,PROXY
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/HBO/HBO.list,PROXY
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Spotify/Spotify.list,PROXY
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Telegram/Telegram.list,PROXY
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/PayPal/PayPal.list,PROXY
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Twitter/Twitter.list,PROXY
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Facebook/Facebook.list,PROXY
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Amazon/Amazon.list,PROXY
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Sony/Sony.list,DIRECT
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Nintendo/Nintendo.list,DIRECT
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Epic/Epic.list,DIRECT
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/SteamCN/SteamCN.list,DIRECT
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Steam/Steam.list,DIRECT
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Game/Game.list,DIRECT
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Microsoft/Microsoft.list,DIRECT
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Google/Google.list,PROXY
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/TikTok/TikTok.list,PROXY
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/GitHub/GitHub.list,PROXY
RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Speedtest/Speedtest.list,PROXY
RULE-SET,https://url/ios_rule_script/master/rule/QuantumultX/Global/Global.list,PROXY
RULE-SET,https://url/ios_rule_script/master/rule/QuantumultX/China/China.list,DIRECT

# 本地局域网地址的规则集。

RULE-SET,https://url/ios_rule_script/master/rule/Shadowrocket/Lan/Lan.list,DIRECT

# 表示 CN 地区的 IP 分流走直连，GEOIP 数据库用来判断 IP 是否属于 CN 地区。默认使用 Shadowrocket 自带的 GEOIP 数据库，如果您想替换其他数据库，可在 设置 - GeoLite2 数据库 里添加和修改。

GEOIP,CN,DIRECT

# 表示当其他所有规则都匹配不到时才使用 FINAL 规则的策略。

FINAL,PROXY

[Host]

# 域名指定本地值：

# example.com=1.2.3.4

# 域名指定 DNS 服务器：

# example.com=server:1.2.3.4

# wifi 名称指定 DNS 服务器，如需指定多个 DNS，可用逗号分隔：

# ssid:wifi 名称=server:1.2.3.4

localhost = 127.0.0.1

[URL Rewrite]

# Google 搜索引擎防跳转的重写。

^https?://(www.)?g.cn https://www.google.com 302
^https?://(www.)?google.cn https://www.google.com 302

[Script]

# BoxJs 安装脚本。

Rewrite: BoxJs = type=http-request,pattern=https?:\/\/boxjs\.(com|net),script-path=https://url/scripts/master/box/chavy.boxjs.js, requires-body=true, timeout=120

[MITM]

# Shadowrocket 打开 HTTPS 解密方法：

# 1.点击配置文件后面 ⓘ - HTTPS 解密 - 证书 - 生成新的 CA 证书 - 安装证书。

# 2.手机设置 - 已下载描述文件 - 安装。

# 3.手机设置 - 通用 - 关于本机 - 证书信任设置 - 开启对应 Shadowrocket 证书信任。

# Shadowrocket 仅会解密 hostname 指定的域名的请求，可以使用通配符。也可以使用前缀 - 排除特定主机名，如 -_.example.com。iOS 系统和某些应用有严格的安全策略，仅信任某些特定的证书，对这些域名启动解密可能导致问题，如 _.apple.com，\*.icloud.com。

hostname = www.google.cn`
```

## 2.占位符说明

```conf
# 占位符说明
## {custom-direct} 自定义直连规则
## {direct} 直连规则
## {custom-proxy} 自定义代理规则
## {proxy} 代理规则
## {custom-reject} 自定义拦截规则
## {reject} 拦截规则
## {proxy-accelerate} 加速代理规则
## {direct-accelerate} 加速直连规则
```

> 感谢[ACL4SSR](https://github.com/ACL4SSR/ACL4SSR/tree/master),[shadowrocket-rules](https://github.com/GMOogway/shadowrocket-rules)和[ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)提供的规则集
