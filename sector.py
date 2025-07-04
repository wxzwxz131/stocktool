# 行业配置 (包含A股和港股)
SECTORS = {
    "AR代工": ['歌尔股份', '立讯精密', '新旺达', '闻泰科技', '工业富联'],
    "果链":['立讯精密', '蓝思科技', '歌尔股份', '鹏鼎控股', '水晶光电', '领益智造', '东山精密', '高伟电子', '舜宇光学科技', '瑞声科技'],
    "服务器链": ['华勤技术', '胜宏科技', '沪电股份', '景旺电子', '生益电子', '深南电路', '生益科技', '工业富联', '江海股份'],
    "英伟达链": ['麦格米特', '胜宏科技', '新易盛', '中际旭创', '天孚通信'],
    "汽车汽配": ['塞力斯', '比亚迪', '悦达投资', '北特科技', '雪龙集团', '万安科技', '恒勃股份', '隆盛科技'],
    "核聚变": ['尚纬股份', '哈焊华通', '辰光医疗', '雪人股份', '融发核电', '国光电气', '东方钽业'],
    "医药": ['众生药业', '海森药业', '海翔药业', '多瑞医药', '海晨药业', '科源制药', '新天地', '贝瑞基因'],
    "港股科技": ['小米集团', '美团', '腾讯控股', '阿里巴巴', '快手', '京东', '百度', '网易', '拼多多', '哔哩哔哩'],
    "港股金融": ['汇丰控股', '中国平安', '友邦保险', '中国人寿', '新华保险', '中国太保', '招商银行', '建设银行', '工商银行', '中国银行'],
    "港股地产": ['碧桂园', '恒大地产', '万科企业', '融创中国', '中国海外发展', '华润置地', '龙湖集团', '世茂集团'],
    "港股消费": ['海底捞', '颐海国际', '蒙牛乳业', '中国飞鹤', '李宁', '安踏体育', '特步国际', '申洲国际'],
    "AR整机厂商": ['TCL', '小米', '佳禾智能', '创维数字'],
    "AR芯片": ['瑞芯微', '芯原股份', '国科微', '全志科技', '北京君正'],
    "AR交互": ['科大讯飞', '联创电子', '欧菲光', '韦尔股份', '睿创微纳', '蓝思科技', '国光电器', '瑞声科技'],
    "AR显示器": ['京东方', '深天马A', '维信诺', '三安光电', '华灿光电', '友达光电'],
    "AR光学模组": ['水晶光电', '苏大维格', '舜宇光学'],
    "谷子经济": ['泡泡玛特', '布鲁可', '奥飞娱乐', '曼卡龙', '创源股份', '高乐股份', '壹网壹创', '柏星龙', '广博股份', '实丰文化', '京华激光', '金运激光'],
    "美容美妆": ['珀莱雅', '上海家化', '丸美生物', '登康口腔', '锦波生物', '拉芳家化'],
    "珠宝钻石": ['老铺黄金', '潮宏基', '莱绅通灵', '莱百股份', '迪阿股份', '惠丰钻石', '力量钻石', '黄河旋风', '豫园股份'],
    "宠物经济": ['中宠股份', '乖宝宠物', '源飞宠物', '可靠股份', '依依股份', '佩蒂股份'],
    "餐饮零食": ['卫龙美味', '三只松鼠', '盐津铺子', '万辰集团', '百龙创园', '同庆楼', '西安饮食', '九毛九', '蜜雪集团', '百胜中国', '古茗', '茶百道'],
    "新兴家电": ['九号公司-WD', '石头科技', '科沃斯', '极米科技', '安克创新', '北鼎股份'],
    "纺织服装": ['安踏体育', '特步国际', '罗莱生活', '水星家纺', '海澜之家', '江南布衣'],
    "上海算力": ['数据港', '科泰电源', '城地香江', '安诺其', '云赛智联', '恒为科技', '网宿科技', '汇纳科技'],
    "浙江算力": ['杭钢股份', '海南华铁', '浙数文化', '宁波建工', '平治信息', '纵横通信', '众合科技', '浙大网新', '浙文互联', '顺网科技', '中恒电气', '华塑科技'],
    "广东算力": ['天威视讯', '朗科科技', '科士达', '奥飞数据', '顺钠股份', '欧陆通', '群兴玩具', '南兴股份', '深桑达A', '南凌科技', '超讯通信', '大位科技'],
    "北京算力": ['铜牛信息', '首都在线', '东土科技', '亚康股份', '真视通', '直真科技', '东方国信', '动力源', '恒华科技'],
    "河北算力": ['常山北明', '润泽科技', '同飞股份'],
    "甘肃算力": ['甘肃能源', '众合科技', '亿田智能', '亚康股份', '甘咨询', '甘肃能化', '弘信电子', '超讯通信'],
    "湖北算力": ['中贝通信', '烽火通信', '信科移动', '盛天网络'],
    "宁夏算力": ['宁夏建材', '美利云', '凯添燃气'],
    "四川算力": ['广安爱众', '依米康', '华体科技', '川润股份'],
    "贵州算力": ['贵广网络'],
    "山东算力": ['浪潮信息', '汉鑫科技'],
    "福建算力": ['科华数据', '鸿博股份', '星网锐捷', '锐捷网络'],
    "deepseek": ['华勤技术', '浙大网新', '海南华铁', '杭钢股份', '梦网科技', '拓维信息', '美格智能', '航锦科技', '华胜天成'],
    "军工": ['成飞集成', '天箭科技'],
    "外骨骼机器人": ['中超控股'],
    "AI基础设施-半导体": ['中芯国际', '中微公司', '北方华创', '立讯精密', '生益科技', '臻鼎科技', '盛美', '精密温控', '致茂电子', '华大九天', '浪潮信息', '工业富联', '澜起科技', '联发科技', '祥硕科技', '联想集团'],
    "AI基础设施-IDC": ['万国数据', '独立通讯'],
    "AI基础设施-电力": ['英维克', '潍柴动力'],
    "AI平台": ['阿里巴巴', '百度', '腾讯控股', '科大讯飞'],
    "AI应用-互联网": ['美团', '美图公司', '快手', '金蝶国际', '携程网', '网易', '贝壳', '拼多多', '京东', 'BOSS直聘', '金山办公'],
    "AI应用-自动驾驶": ['地平线机器人', '比亚迪', '蔚来', '小鹏汽车', '理想汽车', '极氪'],
    "AI医疗": ['阿里健康', '固生堂', '迈瑞医疗', '迪安诊断', '腾讯视频', '复星医药', '联影医疗'],
    "AI消费": ['海尔智家', '泡泡玛特', '巨子生物', '美的集团', '百胜中国', '石头科技', '科沃斯'],
    "AI物流": ['顺丰控股'],
    "AI教育": ['好未来'],
    "AI财务": ['百融云'],
    "AI电子": ['小米集团', '涂鸦智能'],
    "海思": ['深圳华强', '力源信息', '世纪鼎利'],
    "昇腾": ['泰嘉股份', '川润股份', '拓维信息', '华丰股份'],
    "S机器人": ['豪能股份', '隆盛科技', '蓝黛科技', '美湖股份', '富临精工', '长源东谷'],
    "Optimus机器人":["五洲新春", "金沃股份", "恒立液压", "福达股份", "北特科技"],
    "宇树机器人":["凌云光", "奥比中光", "中大力德", "长盛轴承", "华锐精密", "双林股份"],
    "十巨头":["阿里巴巴", "腾讯控股", "小米", "比亚迪", "美团", "网易", "美的", "恒瑞医药", "携程", "安踏"],
    "创新药":["​​百济神州​​", "​​恒瑞医药​", "​荣昌生物​", "​华东医药​", "​​三生制药", "​​科伦药业", "​​信达生物​​"],

    "养老机器人":['美湖股份', '豪能股份', '精工科技', '欧圣电气', '新华锦', '亿嘉和'],
    #  波长光电（现价推）/茂莱光学/福晶科技/汇成真空/彤程新材/艾森股份/飞凯材料/华特气体（现价推）/凯美特气/冠石科技（现价推）/龙图光罩/路维光电/清溢光电
    "光刻机":["波长光电", "茂莱光学", "福晶科技", "汇成真空", "彤程新材", "艾森股份", "飞凯材料", "华特气体", "凯美特气", "冠石科技", "龙图光罩", "路维光电", "清溢光电"],

}

# 港股股票名称映射 (一些港股可能有不同的中文名称)
HK_STOCK_NAME_MAPPING = {
    '小米集团': '小米集团-W',
    '美团': '美团-W',
    '阿里巴巴': '阿里巴巴-SW',
    '快手': '快手-W',
    '京东': '京东集团-SW',
    '百度': '百度集团-SW',
    '拼多多': 'PDD Holdings',
    '哔哩哔哩': '哔哩哔哩-W'
}


