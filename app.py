import random
import streamlit as st

st.set_page_config(page_title="美国诉讼模拟 Demo", page_icon="⚖️", layout="centered")

MAX_ROUNDS = 6

CLIENT_PROFILES = [
    {
        "name": "小卖家",
        "budget_range": (3000, 5000),
        "attitude": "怕冻结，怕拖，倾向尽快止损。",
        "goal": "优先避免链接和资金被冻结。",
    },
    {
        "name": "中型卖家",
        "budget_range": (5000, 9000),
        "attitude": "愿意打一打，但不能失控。",
        "goal": "争取更好的程序结果，同时控制总成本。",
    },
    {
        "name": "强势客户",
        "budget_range": (9000, 15000),
        "attitude": "不想示弱，愿意硬打。",
        "goal": "尽量压制原告，必要时正面应对禁令。",
    },
]

JUDGE_PROFILES = {
    "strict_procedure": {
        "name": "程序型法官",
        "mtd_bonus": 0.18,
        "inj_bonus": -0.05,
        "settle_bonus": 0.00,
        "description": "更看重程序门槛，对薄弱 forum linkage 更敏感。",
    },
    "rights_holder": {
        "name": "偏权利人法官",
        "mtd_bonus": -0.10,
        "inj_bonus": 0.12,
        "settle_bonus": 0.08,
        "description": "对原告的保护诉求更敏感，程序性动议更难打。",
    },
    "efficiency": {
        "name": "效率型法官",
        "mtd_bonus": 0.05,
        "inj_bonus": 0.00,
        "settle_bonus": 0.12,
        "description": "强调尽快收束争议，和解更容易推进。",
    },
}

OPPONENT_PROFILES = {
    "aggressive": {
        "name": "激进型对手",
        "risk_up_each_round": 9,
        "budget_range": (28000, 45000),
        "bluff_probability": 0.40,
        "description": "动作快，敢压强度，愿意把事情推到极限。",
    },
    "conservative": {
        "name": "保守型对手",
        "risk_up_each_round": 5,
        "budget_range": (18000, 28000),
        "bluff_probability": 0.10,
        "description": "节奏较慢，更在意成本控制。",
    },
    "gray": {
        "name": "灰色型对手",
        "risk_up_each_round": 7,
        "budget_range": (22000, 35000),
        "bluff_probability": 0.25,
        "description": "动作不一定快，但更可能包装材料或补奇怪证据。",
    },
}

CLAIM_TYPES = [
    {
        "key": "copyright",
        "name": "版权图片侵权",
        "opening": "原告诉称你的客户使用了其产品图片，并申请了 TRO。",
    }
]

FACT_TEMPLATES = {
    "sales_true": [
        "你调取平台订单导出记录，看到 3 笔 Illinois 收货地址订单，时间分布在近几个月。",
        "客户后台订单摘要中出现数笔 Illinois 地址交易，付款账户看上去彼此独立。",
        "平台销售报表里可以找到 Illinois 收货记录，数量不大，但并非为零。",
    ],
    "sales_false": [
        "你查看现有订单导出记录，暂未发现 Illinois 收货地址交易。",
        "客户提供的后台导出中，当前未出现 Illinois 地址订单。",
        "现有材料里没有检索到明确指向 Illinois 的订单记录。",
    ],
    "test_true_strong": [
        "原告附件中提到一次 Illinois 测购，并附有下单页面、收货信息和订单编号截图。",
        "response draft 中出现较完整的测购描述，包括下单时间、订单编号和 Illinois 收货地址。",
    ],
    "test_true_weak": [
        "原告材料提到“完成了本州测购”，但未附订单编号，只放了一张模糊截图。",
        "complaint 附件提到有 Illinois 测购，但时间、地址和交易凭证并不完整。",
    ],
    "test_false": [
        "现有材料未见明确测购痕迹，至少目前没有订单编号或收货材料。",
        "原告提交的文件中暂未看到完整的 Illinois 测购记录。",
    ],
    "evidence_issue_true": [
        "你比对时间线后发现，一份截图中的时间戳与 complaint 叙述前后不一致。",
        "你注意到原告某附件的文件生成时间与其声称的取证时间存在明显错位。",
        "你检查材料来源时发现，一张关键截图缺少原始来源链条，时间线也有跳跃。",
    ],
    "evidence_issue_false": [
        "你翻查现有材料，暂未发现明显的时间线错位或来源异常。",
        "至少从当前记录看，原告附件的时间和来源没有显著矛盾。",
    ],
    "pj_case_good": [
        "你查到本 circuit 对薄弱 forum linkage 并不宽容。若只是零星线上可达，未必足以支撑个人管辖。",
        "研究结果显示，本 circuit 对基于偶发线上销售建立个人管辖的态度较谨慎。",
    ],
    "pj_case_bad": [
        "你查到本 circuit 在部分案件中接受了较有限的本州联系，尤其是在有订单流入和定向销售迹象时。",
        "研究结果显示，若记录能显示本州订单或测购，个人管辖抗辩会明显变难。",
    ],
    "inj_case_good": [
        "你查到禁令阶段法院仍会关注证据可信度和紧急性，材料若有瑕疵，原告并非天然占优。",
        "本 circuit 的相关材料显示，紧急救济并不会自动跟着权利主张一起落下。",
    ],
    "inj_case_bad": [
        "你查到在平台冻结风险和持续销售被强调时，法院对原告紧急性论证可能更宽容。",
        "研究结果显示，若原告能把持续侵害和平台风险叙述得足够完整，禁令压力会上升。",
    ],
    "settlement_signal_low_budget": [
        "你从对方最近的推进节奏判断，其后续投入意愿似乎开始下降，补充材料频率也在变低。",
        "你注意到原告最近没有再追加新的支持材料，推进力度较之前减弱。",
    ],
    "settlement_signal_high_budget": [
        "对方近期仍保持较高频率推进，似乎没有表现出明显收缩预算的迹象。",
        "从对方补充材料和推进节奏看，其当前仍愿意继续投入资源。",
    ],
    "response_add_sales": [
        "对方 response 中补充了一份州内订单摘要，试图证明你客户并非与 Illinois 毫无联系。",
        "原告在 response 中强调若干本州交易记录，试图把零散订单组织成 forum contacts 叙事。",
    ],
    "response_add_testbuy": [
        "原告在 response 中补充称其完成过 Illinois 测购，并附上一份新的截图材料。",
        "response 新增一段测购叙述，核心意思是原告曾主动完成本州取证。",
    ],
    "response_emphasize_urgency": [
        "原告在 response 中反复强调平台风险、持续销售和紧急性，试图把争议拉回到禁令逻辑。",
        "对方 response 重点不在技术细节，而在不断放大持续侵害和紧急性。",
    ],
    "reply_attack_timeline": [
        "你在 reply 中集中攻击了原告材料的时间线和来源链条，要求法院降低其证明力。",
        "reply 把重点放在证据可采性和时间线矛盾上，试图削弱对方新增材料。",
    ],
    "reply_attack_pj": [
        "你在 reply 中收束论点，强调即便按对方说法，现有记录也不足以建立稳定的 forum linkage。",
        "reply 将争点压回个人管辖门槛，强调零散联系并不能自然转化为本州管辖。",
    ],
    "reply_narrow": [
        "你在 reply 中选择保守推进，只补最核心的一点，避免额外扩大战线。",
        "reply 较短，主要起到维持原有立场、避免新开战线的作用。",
    ],
    "work_origin_strong": [
        "你核查了客户的图片来源链条，发现其能提供供应商原始文件或设计稿，时间节点在原告声称创作时间之前。",
        "客户提供了完整的图片来源记录，包括供应商交付文件和内部使用记录，独立来源叙事可以成立。",
    ],
    "work_origin_weak": [
        "客户称图片来自供应商，但只能提供一份模糊的采购记录，无法完整还原来源链条。",
        "你查看了客户的图片来源材料，发现记录存在缺口，独立来源的可信度有限。",
    ],
    "work_origin_none": [
        "客户无法提供任何图片来源证明，既没有供应商文件，也没有内部设计或采购记录。",
        "你核查后发现客户对图片的来源完全无法说明，独立来源抗辩基础很薄弱。",
    ],
    "work_type_simple": [
        "你观察涉案图片，发现其构图简单、背景纯色、拍摄角度常见，属于典型的通用产品图风格。",
        "涉案图片系普通产品拍摄，没有特别的创意布置或独特视觉安排，与市面上大量同类图片高度雷同。",
    ],
    "work_type_styled": [
        "涉案图片有一定的布光和构图设计，并非最基础的白底产品图，但其整体风格仍属产品图常见范畴。",
        "你研究图片后发现其有一定视觉设计感，原告可能会主张这是有创意选择的作品，但整体保护空间仍有限。",
    ],
    "work_type_creative": [
        "涉案图片有明显的创意布置，包括独特构图、特殊场景搭配或精心设计的视觉元素，原告的版权主张基础相对扎实。",
        "你评估后认为该图片超出了普通产品图的范畴，具有可识别的创意表达，原告版权保护范围可能较宽。",
    ],
    "prior_market_dense": [
        "你在市场上检索到大量与原告图片风格、构图高度相似的在先产品图，时间均早于原告声称的创作时间。",
        "市场调查结果显示，类似的产品图表达方式早已被广泛使用，原告作品独特性主张的空间被大幅压缩。",
    ],
    "prior_market_medium": [
        "市场上存在部分与原告图片风格类似的在先作品，但并不密集，保护范围的争议空间存在但不算决定性。",
        "你找到了几张风格近似的在先产品图，可以辅助支撑保护范围较薄的论点，但材料还不够充分。",
    ],
    "prior_market_sparse": [
        "你在市场上未能找到与原告图片高度相似的在先作品，攻击保护范围的材料基础较弱。",
        "现有检索结果显示，类似风格和构图的在先作品较少，原告独特性主张的压力相对有限。",
    ],
    "similarity_high": [
        "你对比双方图片后发现，客户图片与原告图片在构图、角度、主体位置和背景处理上高度相似，差异点有限。",
        "两张图片的相似程度较高，原告的相似性主张有一定支撑，正面否认相似性的空间较窄。",
    ],
    "similarity_medium": [
        "你对比两张图片，发现存在明显重合之处，但也有若干可辨认的差异，相似性争议空间较大。",
        "双方图片有一定相似度，但细节上存在差别，相似性问题在庭审中仍有一定辩论余地。",
    ],
    "similarity_low": [
        "你仔细对比后认为，两张图片的相似点有限，差异集中在构图、角度或主体展示方式上，相似性主张基础不强。",
        "客户图片与原告图片在细节上存在明显差异，直接攻击相似性不足有较好的事实支撑。",
    ],
    "ownership_clear": [
        "你核查原告提交的版权登记材料，发现权属链条清晰，登记人与起诉人一致，权属基础较难攻击。",
        "原告的版权登记文件完整，所有权归属明确，攻击权属基础需要额外挖掘登记以外的问题。",
    ],
    "ownership_questionable": [
        "你发现原告的版权登记材料中存在一些模糊之处，比如登记时间偏晚或登记信息与诉状陈述存在出入。",
        "原告权属链条并不完全清晰，登记文件与其实际主张之间有一定落差，攻击权属有一定余地。",
    ],
    "ownership_weak": [
        "你核查后发现，原告的版权登记记录存在明显问题，要么登记人与起诉人不一致，要么来源文件缺失严重。",
        "原告提交的权属材料漏洞较多，登记链条不完整，攻击权属基础可以作为主力论点之一。",
    ],
}

PLAINTIFF_EMAILS = {
    "strong": [
        "我方已就贵方提出的各项程序性主张进行充分研究，认为相关论据缺乏依据。我方将继续全力推进本案，并保留就贵方不当拖延申请费用偿还的一切权利。",
        "贵方迄今为止提出的抗辩并未动摇我方在本案中的立场。我方委托人已明确授权，将本案推进至最终裁决，无论耗时多久。",
        "我方注意到贵方持续提出程序性障碍，但本案事实与法律依据均对我方有利。我方不打算在此节点接受任何不合理的和解条件。",
    ],
    "strong_bluff": [
        "我方对本案走向保持高度信心，并已做好充分的后续推进准备。贵方若继续拖延，只会增加最终裁决时的赔偿金额。",
        "我方委托人对本案结果持乐观态度，我方律师团队已全面就绪。建议贵方认真评估继续应诉的成本与风险。",
        "我方已就本案所有可能的后续发展做好充分预案。若贵方无意在合理条件下了结本案，我方将毫不犹豫地继续推进。",
    ],
    "neutral": [
        "我方注意到双方在本案上均已投入相当资源。如贵方有意在合理条件下尽快了结，我方愿意在有限时间窗口内探讨和解可能性。",
        "我方委托人对本案仍持积极推进态度，但亦认识到诉讼程序对双方均有一定成本。如有和解意向，请及时告知。",
        "我方已就本案后续程序作出相应安排。在此告知贵方，若双方有意就和解条件进行初步沟通，我方可以配合安排。",
    ],
    "soft": [
        "考虑到诉讼成本对双方的持续影响，我方委托人授权就本案和解事宜进行实质性讨论。请贵方尽快告知是否有意向。",
        "我方认为，在当前程序节点，双方通过协商了结本案对各方均属合理选择。我方愿意就具体条件展开对话。",
        "我方委托人希望以务实态度处理本案。如贵方有意向在近期内达成和解，请与我方联系以安排进一步沟通。",
    ],
    "urgent": [
        "我方委托人希望在近期内了结本案相关事宜。如贵方能在本周内给出回应，我方可就和解条件作出一定让步，请尽快与我方联系。",
        "出于对双方均有利的考量，我方建议在当前节点认真讨论和解方案。我方授权提供一定的条件灵活性，但此窗口期有限。",
        "我方委托人已表示希望尽快了结本案。如贵方有意在合理框架内达成协议，请务必尽快回复，以免错过当前时间窗口。",
    ],
    "mtd_denied_hardened": [
        "贵方的程序性动议已被法院驳回，本案将继续向实体问题推进。我方委托人对此结果早有预期，后续推进计划已全面就绪。",
        "法院裁决已明确否定了贵方的程序性主张。我方将在此基础上全力推进禁令程序，并就本案实体问题寻求完整救济。",
        "程序性障碍已被清除。我方委托人对案件走向充满信心，并已准备好就侵权事实展开全面举证。",
    ],
    "mtd_partial_recalibrate": [
        "我方注意到法院就程序性动议作出的裁决。尽管部分主张未获全部支持，我方对本案实体问题的立场并未改变，将继续推进。",
        "法院的裁决结果并未实质影响我方对本案的整体判断。我方将在现有程序框架内继续寻求完整救济。",
    ],
    "bankrupt_final": [
        "我方委托人经审慎评估后，认为在当前条件下达成和解符合各方利益。我方现正式授权就和解条件展开实质性谈判，请贵方尽快回复。",
        "综合考量各方面因素，我方委托人希望在当前节点了结本案。我方愿意就和解金额作出实质性让步，请贵方告知可以接受的条件范围。",
    ],
}

COMPLAINT_BLOCKS = {
    "jurisdiction_strong": [
        "起诉状称 Defendant 向 Illinois 销售了被诉产品，并提到数笔指向 Illinois consumers 的交易。",
        "Complaint 主张 Defendant 在 Illinois 存在销售行为，并列出若干 allegedly tied to Illinois consumers 的交易。",
        "起诉状称 Plaintiff 已识别出多笔 Illinois-directed transactions，并据此主张 forum contacts 成立。",
    ],
    "jurisdiction_weak": [
        "起诉状提到 nationwide online availability，但没有明确列出 Illinois transactions。",
        "Complaint 仅以较概括方式主张 forum contacts，未清楚展开具体的 Illinois sales。",
        "起诉状泛泛提到 Illinois market，但没有明确写出订单编号、收货地址或具体 Illinois transactions。",
    ],
    "testbuy_strong": [
        "起诉状称 Plaintiff 完成了一次 Illinois test buy，并附有 order page、shipping details 及 order identifier。",
        "Complaint 描述了一次 completed Illinois test buy，并附有 screenshots 反映下单及收货信息。",
        "起诉状称 Plaintiff 进行了 Illinois test purchase，相关附件包含 order number、delivery information 和页面截图。",
    ],
    "testbuy_weak": [
        "起诉状提到 Plaintiff 做过 test purchase，但未清楚列出 order number 或 shipping confirmation。",
        "Complaint 提到一次 supposed Illinois test buy，但 supporting detail 较为有限。",
        "起诉状称有 Illinois test buy，但附件中对下单时间、订单编号及收货信息的展示并不完整。",
    ],
    "testbuy_none": [
        "起诉状表面上没有附出完整的 Illinois test purchase record。",
        "Complaint 中未见完整的 Illinois test buy 凭证。",
        "现有 pleading 没有清楚展示 completed Illinois test purchase 的完整记录。",
    ],
    "urgency_high": [
        "起诉状反复强调 ongoing sales、platform risk，以及 absent immediate relief 时 continuing harm 的可能性。",
        "Complaint 多次主张 irreparable harm，并将其与 platform exposure 和 continuing sales 绑定。",
        "起诉状将 ongoing infringement、platform risk 和 immediate relief 的必要性反复并列强调。",
    ],
    "urgency_mid": [
        "起诉状主张 continuing harm 并请求 immediate relief，但对 urgency 的展开相对简短。",
        "Complaint 提到 ongoing harm 和 platform risk，但 urgency allegations 本身并不算特别详细。",
        "起诉状要求紧急救济，但对 irreparable harm 的展开篇幅有限。",
    ],
    "evidence_strong": [
        "附件中包含 screenshots、product comparisons 以及 transaction-related images。",
        "Complaint 随附多张 image-based exhibits，试图支撑其 infringement allegations。",
        "起诉状附件含有 screenshots、对比图及若干与 transaction 相关的图片材料。",
    ],
    "evidence_weak": [
        "部分 screenshots 看起来经过裁剪，exhibits 并未明显展示完整 source information。",
        "附件中虽有 screenshots，但未清楚呈现完整 metadata 或 source context。",
        "起诉状虽附有图片材料，但部分 exhibits 的 source context 和 metadata 展示不充分。",
    ],
    "work_claim_simple": [
        "原告主张其享有一张产品展示图片的版权，该图片系白底拍摄，风格简洁，Plaintiff 称其为独创作品并已完成版权登记。",
        "Plaintiff 声称对一张产品图片享有版权，图片呈现为标准产品拍摄风格，并附有 copyright registration certificate。",
        "起诉状称 Plaintiff 对涉案产品图持有有效版权登记，图片为普通产品展示拍摄，Plaintiff 主张该图属其原创作品。",
    ],
    "work_claim_styled": [
        "原告主张其享有一张具有特定布光和场景设计的产品图片的版权，称该图在构图和视觉表达上具有独创性，并已完成版权登记。",
        "Plaintiff 声称对一张经过专业场景搭配的产品图享有版权，主张其在布光、角度和整体风格上体现了创意选择。",
        "起诉状称涉案版权作品系一张有明显风格化处理的产品图，Plaintiff 主张其视觉表达超出了普通产品图的范畴。",
    ],
    "work_claim_creative": [
        "原告主张其享有一张经过精心场景创作的产品图片的版权，称该图融合了独特构图、场景搭配及视觉设计元素，创意性显著。",
        "Plaintiff 声称对一张具有高度创意布置的产品图享有版权，主张其在整体表达上属于具有较强保护价值的原创作品。",
        "起诉状称涉案版权图片系原告精心拍摄制作，具有独特的视觉叙事和场景设计，Plaintiff 主张该作品应受到完整版权保护。",
    ],
    "accused_product_online": [
        "起诉状指控 Defendant 在 Amazon 等电商平台上使用了与原告版权图片实质性相似的产品图，用于其同类产品的商品详情页展示。",
        "Plaintiff 称 Defendant 未经授权，将与原告版权作品高度相似的图片上传至其在线商品页面，用于销售同类产品。",
        "起诉状主张 Defendant 在电商平台的商品 listing 中使用了涉嫌复制自原告版权图片的图像，构成直接侵权。",
    ],
}

def build_complaint_text(hidden_case, rng):
    parts = []

    # 版权作品描述（最先出现，确立案件性质）
    work_type = hidden_case.get("work_type", "simple_product_photo")
    if work_type == "simple_product_photo":
        parts.append(rng.choice(COMPLAINT_BLOCKS["work_claim_simple"]))
    elif work_type == "styled_product_image":
        parts.append(rng.choice(COMPLAINT_BLOCKS["work_claim_styled"]))
    else:
        parts.append(rng.choice(COMPLAINT_BLOCKS["work_claim_creative"]))

    # 被控产品和侵权行为描述
    parts.append(rng.choice(COMPLAINT_BLOCKS["accused_product_online"]))

    # forum contacts
    if hidden_case["forum_sale"]:
        parts.append(rng.choice(COMPLAINT_BLOCKS["jurisdiction_strong"]))
    else:
        parts.append(rng.choice(COMPLAINT_BLOCKS["jurisdiction_weak"]))

    # test buy
    if hidden_case["test_buy"]:
        if hidden_case["test_buy_strength"] == "strong":
            parts.append(rng.choice(COMPLAINT_BLOCKS["testbuy_strong"]))
        else:
            parts.append(rng.choice(COMPLAINT_BLOCKS["testbuy_weak"]))
    else:
        parts.append(rng.choice(COMPLAINT_BLOCKS["testbuy_none"]))

    # urgency
    if hidden_case["plaintiff_goal"] == "freeze_fast":
        parts.append(rng.choice(COMPLAINT_BLOCKS["urgency_high"]))
    else:
        parts.append(rng.choice(COMPLAINT_BLOCKS["urgency_mid"]))

    # evidence
    if hidden_case["evidence_issue"]:
        parts.append(rng.choice(COMPLAINT_BLOCKS["evidence_weak"]))
    else:
        parts.append(rng.choice(COMPLAINT_BLOCKS["evidence_strong"]))

    return " ".join(parts)

ACTIONS_INFO = {
    "review_complaint": {"cost": 400, "type": "review", "label": "阅读 complaint 摘要"},
    "review_client_msg": {"cost": 300, "type": "review", "label": "阅读客户初步陈述"},
    "review_financials": {"cost": 400, "type": "review", "label": "核实冻结金额与销售金额"},
    "invest_sales": {"cost": 1500, "type": "fact", "label": "调查销售流向"},
    "invest_testbuy": {"cost": 1500, "type": "fact", "label": "调查测购情况"},
    "invest_evidence": {"cost": 2000, "type": "fact", "label": "核查证据时间线"},
    "research_pj": {"cost": 1200, "type": "research", "label": "研究个人管辖判例"},
    "research_inj": {"cost": 1200, "type": "research", "label": "研究禁令标准"},
    "research_settle": {"cost": 800, "type": "research", "label": "观察对方推进强度"},
    "choose_mtd": {"cost": 800, "type": "strategy", "label": "确定主打程序抗辩"},
    "choose_inj": {"cost": 1000, "type": "strategy", "label": "确定主打禁令对抗"},
    "choose_settle": {"cost": 500, "type": "strategy", "label": "确定主打和解压价"},
    "choose_attrition": {"cost": 700, "type": "strategy", "label": "确定主打消耗战"},
    "file_motion": {"cost": 1500, "type": "motion", "label": "提交动议/正式行动"},
    "reply_attack_timeline": {"cost": 1200, "type": "reply", "label": "Reply 主打时间线矛盾"},
    "reply_attack_pj": {"cost": 1200, "type": "reply", "label": "Reply 主打程序门槛"},
    "reply_narrow": {"cost": 700, "type": "reply", "label": "Reply 保守收束"},
    "pi_attack_similarity": {"cost": 1400, "type": "pi_opp", "label": "PI Opposition：攻击相似性"},
    "pi_attack_scope": {"cost": 1400, "type": "pi_opp", "label": "PI Opposition：攻击保护范围"},
    "pi_assert_independent_creation": {"cost": 1600, "type": "pi_opp", "label": "PI Opposition：主张独立来源"},
    "pi_attack_ownership": {"cost": 1300, "type": "pi_opp", "label": "PI Opposition：攻击权属与基础"},
    "invest_work_origin": {"cost": 1600, "type": "fact", "label": "调查图片来源与独立性"},
    "invest_prior_market": {"cost": 1800, "type": "fact", "label": "调查市场在先作品"},
    "invest_similarity": {"cost": 1400, "type": "fact", "label": "对比相似度"},
    "invest_ownership": {"cost": 1200, "type": "fact", "label": "核查原告版权权属"},
}

def rand_choice(rng, key):
    return rng.choice(FACT_TEMPLATES[key])

def init_game(seed=None):
    if seed is None:
        seed = random.randint(1, 10_000_000)
    rng = random.Random(seed)

    client = rng.choice(CLIENT_PROFILES)
    opponent_key = rng.choice(list(OPPONENT_PROFILES.keys()))
    judge_key = rng.choice(list(JUDGE_PROFILES.keys()))
    claim = CLAIM_TYPES[0]

    client_budget = rng.randint(*client["budget_range"])
    plaintiff_budget = rng.randint(*OPPONENT_PROFILES[opponent_key]["budget_range"])

    forum_sale = rng.random() < 0.38
    test_buy = rng.random() < 0.50
    test_buy_strength = "strong" if (test_buy and rng.random() < 0.55) else "weak"
    evidence_issue = rng.random() < (0.35 if opponent_key == "gray" else 0.18)
    plaintiff_goal = rng.choice(["freeze_fast", "settle_fast", "pressure_defendant"])

    frozen_amount = rng.randint(0, 30000)
    sales_amount = rng.randint(1000, 80000)

    frozen_norm = min(frozen_amount / 30000, 1)
    sales_norm = min(sales_amount / 80000, 1)
    plaintiff_expectation = round(min(1, 0.6 * frozen_norm + 0.4 * sales_norm), 3)

    plaintiff_expected_recovery = int(
        (0.5 * frozen_amount + 0.15 * sales_amount) * (0.6 + plaintiff_expectation)
    )

    work_type = rng.choice([
        "simple_product_photo",
        "styled_product_image",
        "high_creativity_work",
    ])
    prior_art_density = rng.choice(["low", "medium", "high"])
    similarity_to_claimed = rng.randint(35, 95)
    similarity_to_prior_market = rng.randint(20, 90)
    independent_creation_support = rng.choice(["none", "weak", "strong"])
    ownership_clarity = rng.choice(["clear", "questionable", "weak"])

    state = {
        "seed": seed,
        "rng": seed,
        "round": 1,
        "phase": "intake",
        "subphase_done": False,
        "client_budget": client_budget,
        "initial_client_budget": client_budget,
        "risk": 32,
        "plaintiff_budget_public_signal": "unknown",
        "client": client,
        "claim": claim,
        "judge_key": judge_key,
        "opponent_key": opponent_key,
        "strategy": None,
        "mtd_motion_filed": False,
        "mtd_opposition_seen": False,
        "mtd_reply_done": False,
        "mtd_reply_choices": [],
        "mtd_result": None,
        "pi_motion_seen": False,
        "pi_opposition_choices": [],
        "pi_reply_seen": False,
        "pi_result": None,
        "pi_granted": False,
        "post_pi_phase": None,
        "post_pi_delay_rounds": 0,
        "current_demand": None,
        "settlement_history": [],
        "demand_stage_seen": [],
        "counter_offer_last": None,
        "outcome": None,
        "plaintiff_last_offer_round": -1,
        "plaintiff_weakened": False,
        "history": [],
        "facts_known": [],
        "research_known": [],
        "used_actions": [],
        "story_fragments": [
            f"你的客户是一家{client['name']}。{claim['opening']}",
        ],
        "hidden_case": {
            "forum_sale": forum_sale,
            "test_buy": test_buy,
            "test_buy_strength": test_buy_strength,
            "evidence_issue": evidence_issue,
            "plaintiff_budget": plaintiff_budget,
            "plaintiff_budget_initial": plaintiff_budget,
            "plaintiff_goal": plaintiff_goal,
            "frozen_amount": frozen_amount,
            "sales_amount": sales_amount,
            "plaintiff_expectation": plaintiff_expectation,
            "plaintiff_expected_recovery": plaintiff_expected_recovery,
            "work_type": work_type,
            "prior_art_density": prior_art_density,
            "similarity_to_claimed": similarity_to_claimed,
            "similarity_to_prior_market": similarity_to_prior_market,
            "independent_creation_support": independent_creation_support,
            "ownership_clarity": ownership_clarity,
        },
        "review_materials": {
            "complaint": build_complaint_text(
                {
                    "forum_sale": forum_sale,
                    "test_buy": test_buy,
                    "test_buy_strength": test_buy_strength,
                    "evidence_issue": evidence_issue,
                    "plaintiff_goal": plaintiff_goal,
                    "work_type": work_type,
                },
                rng
            ),
            "client_msg": rng.choice([
                "客户称图片来自供应商，自己并未专门面向 Illinois 投放广告。",
                "客户表示目前最担心的是链接被冻结，因为这个产品占近期销售较高比例。",
                "客户只给出了一部分后台记录，很多细节仍待补充。",
            ]),
        },
    }

    st.session_state.game = state

def g():
    return st.session_state.game

def add_history(title, body):
    g()["history"].append({"title": title, "body": body})

def spend_client(cost):
    g()["client_budget"] -= cost

def spend_plaintiff(cost):
    g()["hidden_case"]["plaintiff_budget"] -= cost

def can_pay(cost):
    return g()["client_budget"] >= cost

def compute_pi_merits_score():
    hc = g()["hidden_case"]

    score = 50

    work_type_bonus = {
        "simple_product_photo": -12,
        "styled_product_image": 4,
        "high_creativity_work": 14,
    }
    prior_art_penalty = {
        "low": 12,
        "medium": 0,
        "high": -14,
    }
    independent_creation_penalty = {
        "none": 10,
        "weak": -4,
        "strong": -14,
    }
    ownership_bonus = {
        "clear": 8,
        "questionable": -6,
        "weak": -14,
    }

    score += work_type_bonus[hc["work_type"]]
    score += prior_art_penalty[hc["prior_art_density"]]
    score += independent_creation_penalty[hc["independent_creation_support"]]
    score += ownership_bonus[hc["ownership_clarity"]]

    score += int((hc["similarity_to_claimed"] - 50) * 0.55)
    score -= int((hc["similarity_to_prior_market"] - 50) * 0.40)

    if hc["evidence_issue"]:
        score -= 8

    if not hc["forum_sale"]:
        score -= 3

    if hc["test_buy"]:
        if hc["test_buy_strength"] == "strong":
            score += 6
        else:
            score += 2

    return max(0, min(100, score))

def is_willful_infringement():
    hc = g()["hidden_case"]
    criteria = 0
    if hc["similarity_to_claimed"] >= 70:
        criteria += 1
    if hc["independent_creation_support"] == "none":
        criteria += 1
    if hc["ownership_clarity"] == "clear":
        criteria += 1
    if not hc["evidence_issue"]:
        criteria += 1
    return criteria >= 2

def can_claim_statutory_damages():
    hc = g()["hidden_case"]
    return hc["ownership_clarity"] != "weak"

def compute_copyright_damages():
    hc = g()["hidden_case"]
    rng = random.Random(g()["seed"] + 7777)

    # 路径一：实际损害 + 不重叠的被告可归因利润
    contribution_range = {
        "simple_product_photo": (0.08, 0.12),
        "styled_product_image": (0.15, 0.25),
        "high_creativity_work": (0.30, 0.50),
    }
    low_c, high_c = contribution_range[hc["work_type"]]
    contribution = rng.uniform(low_c, high_c)

    defendant_profit = int(hc["sales_amount"] * contribution)
    plaintiff_actual_loss = int(hc["frozen_amount"] * 0.15)

    # 独立来源成立则被告利润归零
    if hc["independent_creation_support"] == "strong":
        defendant_profit = 0
    elif hc["independent_creation_support"] == "weak":
        defendant_profit = int(defendant_profit * 0.4)

    path1 = defendant_profit + plaintiff_actual_loss

    # 路径二：法定赔偿（需要登记有效）
    if not can_claim_statutory_damages():
        path2 = 0
        path2_label = "法定赔偿不可用（登记存疑）"
    else:
        merits = compute_pi_merits_score()
        willful = is_willful_infringement()

        if willful:
            # 故意侵权：$30,000–$150,000
            stat_low = 30000
            stat_high = 150000
        else:
            # 普通侵权：$750–$30,000
            stat_low = 750
            stat_high = 30000

        # merits score 决定法院裁量位置（0–100 映射到区间内）
        position = max(0, min(1, (merits - 20) / 60))
        path2 = int(stat_low + (stat_high - stat_low) * position)
        path2_label = f"法定赔偿（{'故意侵权' if willful else '普通侵权'}）"

    # 原告选较高路径
    if path2 >= path1:
        chosen_path = 2
        chosen_amount = path2
        chosen_label = path2_label
    else:
        chosen_path = 1
        chosen_amount = path1
        chosen_label = "实际损害 + 被告可归因利润"

    # floor price：原告愿意接受的最低和解金额
    floor_price = int(chosen_amount * 0.30)

    return {
        "path1": path1,
        "path2": path2,
        "path2_label": path2_label if can_claim_statutory_damages() else "法定赔偿不可用（登记存疑）",
        "chosen_path": chosen_path,
        "chosen_amount": chosen_amount,
        "chosen_label": chosen_label,
        "floor_price": floor_price,
        "willful": is_willful_infringement(),
        "statutory_available": can_claim_statutory_damages(),
        "contribution_rate": round(contribution, 3),
        "defendant_profit": defendant_profit,
        "plaintiff_actual_loss": plaintiff_actual_loss,
    }

def get_initial_position():
    hc = g()["hidden_case"]

    fact_score = 0.5
    if not hc["forum_sale"]:
        fact_score += 0.2
    else:
        fact_score -= 0.2

    if not hc["test_buy"]:
        fact_score += 0.2
    elif hc["test_buy_strength"] == "strong":
        fact_score -= 0.2
    else:
        fact_score -= 0.05

    if hc["evidence_issue"]:
        fact_score += 0.2

    fact_score = max(0, min(1, fact_score))
    budget_score = max(0, min(1, g()["initial_client_budget"] / 10000))

    return {
        "fact_score": fact_score,
        "budget_score": budget_score,
        "fact_quad": "事实有利" if fact_score >= 0.5 else "事实不利",
        "budget_quad": "预算高" if budget_score >= 0.5 else "预算低",
    }

def estimate_liability(outcome):
    title = outcome.get("title", "")

    # 零赔偿结局
    zero_liability_outcomes = {
        "原告撤回推进",
        "Motion to Dismiss 获准",
        "原告推进崩塌",
    }
    if title in zero_liability_outcomes:
        return 0

    # 和解/判决金额由调用方直接传入
    if "liability" in outcome:
        return outcome["liability"]

    # 其他结局使用版权赔偿计算
    dmg = compute_copyright_damages()
    merits = compute_pi_merits_score()

    if "缺席判决" in title:
        if dmg["willful"]:
            return min(150000, dmg["chosen_amount"])
        else:
            return dmg["chosen_amount"]
    elif title in ["禁令对抗失败", "强制裁决·PI已批准"]:
        return int(dmg["chosen_amount"] * 0.85)
    elif title in ["局部顶住禁令压力", "强制裁决·PI未批准"]:
        return int(dmg["chosen_amount"] * 0.40)
    elif title == "禁令压力被显著削弱":
        return int(dmg["chosen_amount"] * 0.10)
    elif title in ["程序抗辩失败", "消耗战未奏效"]:
        return int(dmg["chosen_amount"] * 0.60)
    elif title in ["Motion to Dismiss 部分成功", "对方推进明显放缓"]:
        return int(dmg["chosen_amount"] * 0.20)
    else:
        return int(dmg["chosen_amount"] * 0.50)

def get_final_position(liability, cost_spent):
    if liability == 0:
        liability_quad = "赔偿为零"
    elif liability <= 5000:
        liability_quad = "赔偿低"
    else:
        liability_quad = "赔偿高"
    cost_quad = "消耗低" if cost_spent <= g()["initial_client_budget"] * 0.5 else "消耗高"

    return {
        "liability_quad": liability_quad,
        "cost_quad": cost_quad,
    }

def compute_final_score(outcome):
    init = get_initial_position()

    initial_advantage = init["fact_score"] * 0.6 + init["budget_score"] * 0.4

    liability = estimate_liability(outcome)
    cost_spent = max(0, g()["initial_client_budget"] - g()["client_budget"])

    liability_norm = min(liability / 30000, 1)
    cost_norm = min(cost_spent / max(g()["initial_client_budget"], 1), 1)

    final_goodness = (1 - liability_norm) * 0.7 + (1 - cost_norm) * 0.3

    performance_delta = final_goodness - initial_advantage
    score = int(50 + performance_delta * 50)
    score = max(1, min(99, score))

    outcome["initial_position"] = init
    outcome["liability"] = liability
    outcome["cost_spent"] = cost_spent
    outcome["final_position"] = get_final_position(liability, cost_spent)
    outcome["performance_delta"] = round(performance_delta, 3)
    outcome["score"] = score

    return outcome

def end_with_outcome(outcome):
    g()["outcome"] = compute_final_score(outcome)
    g()["phase"] = "ended"

def risk_text(v):
    if v < 35:
        return "低"
    if v < 60:
        return "中"
    if v < 80:
        return "高"
    return "极高"

def generate_plaintiff_email():
    hc = g()["hidden_case"]
    pb = hc["plaintiff_budget"]
    initial_pb = hc["plaintiff_budget_initial"]
    budget_ratio = pb / max(initial_pb, 1)
    opp_key = g()["opponent_key"]
    opp = OPPONENT_PROFILES[opp_key]
    mtd_result = g().get("mtd_result")
    phase = g()["phase"]
    rng = random.Random(g()["seed"] + g()["round"] * 997)

    # 原告预算归零：无论如何只发软信号
    if pb <= 0:
        return rng.choice(PLAINTIFF_EMAILS["bankrupt_final"])

    # MTD 被完全驳回：强硬跳变
    if mtd_result == "denied" and phase in ["pi_motion", "pi_opposition", "pi_reply", "pi_ruling"]:
        return rng.choice(PLAINTIFF_EMAILS["mtd_denied_hardened"])

    # MTD 部分成功后重新校准
    if mtd_result == "partial" and phase in ["pi_motion", "pi_opposition"]:
        return rng.choice(PLAINTIFF_EMAILS["mtd_partial_recalibrate"])

    # 根据预算比例确定真实状态
    if budget_ratio >= 0.70:
        true_tone = "strong"
    elif budget_ratio >= 0.45:
        true_tone = "neutral"
    elif budget_ratio >= 0.22:
        true_tone = "soft"
    else:
        true_tone = "urgent"

    # 虚张声势判断（预算归零时不适用，已在上面处理）
    bluff_chance = opp["bluff_probability"]
    # gray 型在预算充足时也可能发软信号试探
    if opp_key == "gray" and budget_ratio >= 0.60 and rng.random() < 0.20:
        return rng.choice(PLAINTIFF_EMAILS["neutral"])

    if true_tone in ["soft", "urgent"] and rng.random() < bluff_chance:
        # 虚张声势：发强硬邮件
        return rng.choice(PLAINTIFF_EMAILS["strong_bluff"])

    return rng.choice(PLAINTIFF_EMAILS[true_tone])

def plaintiff_signal():
    return generate_plaintiff_email()

def plaintiff_signal_decoded():
    """仅在玩家做过 research_settle 后显示的解码提示"""
    hc = g()["hidden_case"]
    pb = hc["plaintiff_budget"]
    initial_pb = hc["plaintiff_budget_initial"]
    budget_ratio = pb / max(initial_pb, 1)
    if budget_ratio >= 0.65:
        return "你注意到对方近期补充材料的频率仍然较高，推进节奏未见明显松弛。"
    elif budget_ratio >= 0.40:
        return "你注意到对方推进节奏有所放缓，补充材料的力度不如前期。"
    elif budget_ratio >= 0.18:
        return "你注意到对方近期动作明显减少，追加材料的频率已显著下降。"
    else:
        return "你注意到对方几乎停止了新的程序动作，推进能力似乎已严重受限。"

def plaintiff_initiative_offer():
    """原告主动出价逻辑，在 advance_round 时调用"""
    if g()["outcome"] is not None:
        return
    hc = g()["hidden_case"]
    pb = hc["plaintiff_budget"]
    initial_pb = hc["plaintiff_budget_initial"]
    budget_ratio = pb / max(initial_pb, 1)
    opp_key = g()["opponent_key"]
    phase = g()["phase"]
    rng = random.Random(g()["seed"] + g()["round"] * 1031)

    # 各阶段原告主动出价的预算阈值
    thresholds = {
        "aggressive": 0.28,
        "conservative": 0.42,
        "gray": 0.35,
    }
    threshold = thresholds[opp_key]

    # 只在实体阶段开始后才主动出价
    if phase not in [
        "mtd_motion", "mtd_opposition", "mtd_reply", "mtd_ruling",
        "pi_motion", "pi_opposition", "pi_reply", "pi_ruling"
    ]:
        return

    if budget_ratio > threshold:
        return

    # 避免重复在同一 round 出价
    last_offer_round = g().get("plaintiff_last_offer_round", -1)
    if g()["round"] - last_offer_round < 2:
        return

    stage = f"plaintiff_initiative_{g()['round']}"
    if stage in g()["demand_stage_seen"]:
        return

    # 原告主动出价时折扣更大，模拟希望尽快收场
    discount = 0.55 + budget_ratio * 0.30
    base_demand = compute_current_demand("pre_pi")
    offer = max(500, int(base_demand * discount))

    g()["current_demand"] = offer
    g()["settlement_history"].append({
        "stage": stage,
        "label": "原告主动提出和解",
        "demand": offer,
    })
    g()["demand_stage_seen"].append(stage)
    g()["plaintiff_last_offer_round"] = g()["round"]

    add_history(
        "原告主动接触",
        f"对方律师主动发来邮件，表示愿意就本案和解条件展开讨论。当前报价：${offer:,}。"
    )

def plaintiff_reinforce_budget(stage):
    """原告在关键节点追加预算"""
    hc = g()["hidden_case"]
    opp_key = g()["opponent_key"]
    rng = random.Random(g()["seed"] + hash(stage) % 9999)

    reinforce_map = {
        "aggressive": (6000, 12000),
        "conservative": (2000, 5000),
        "gray": (3000, 8000),
    }
    low, high = reinforce_map[opp_key]
    amount = rng.randint(low, high)
    hc["plaintiff_budget"] += amount
    add_history(
        "对方追加投入",
        f"对方在当前节点追加了推进资源，后续压力可能上升。"
    )

def phase_name():
    mapping = {
        "intake": "了解案情",
        "investigation": "调查事实",
        "research": "研究法律",
        "strategy": "选择策略",
        "mtd_motion": "提交 MTD",
        "mtd_opposition": "阅读原告对 MTD 的 opposition",
        "mtd_reply": "提交 MTD reply",
        "mtd_ruling": "等待 MTD 裁决",
        "pi_motion": "阅读原告 PI motion",
        "pi_opposition": "提交 PI opposition",
        "pi_reply": "阅读原告 PI reply",
        "pi_ruling": "等待 PI 裁决",
        "ended": "本局结束",
    }
    return mapping.get(g()["phase"], f"未知阶段：{g()['phase']}")

def used(action_key):
    return action_key in g()["used_actions"]

def mark_used(action_key):
    if action_key not in g()["used_actions"]:
        g()["used_actions"].append(action_key)

def unlock_story_round():
    r = g()["round"]
    if r == 2:
        g()["story_fragments"].append(
            f"客户当前预算约为 ${g()['initial_client_budget']:,}。客户态度是：{g()['client']['attitude']}"
        )
    if r == 3:
        g()["story_fragments"].append(
            "你从客户和平台处陆续拿到更多材料，但 forum contacts、测购和证据质量仍需自己判断。"
        )
    if r == 4:
        g()["story_fragments"].append(
            "法院对程序节奏和紧急性的关注开始上升。继续拖延会同时放大平台与诉讼压力。"
        )

def forced_end_check():
    if g()["outcome"] is not None:
        return

    phase_min_cost = {
        "intake": 300,
        "investigation": 1500,
        "research": 800,
        "strategy": 500,
        "mtd_motion": 1500,
        "mtd_opposition": 0,
        "mtd_reply": 700,
        "mtd_ruling": 0,
        "pi_motion": 0,
        "pi_opposition": 1300,
        "pi_reply": 0,
        "pi_ruling": 0,
        "post_pi_negotiation": 0,
        "ended": 0,
    }

    current_phase = g()["phase"]
    min_future_cost = phase_min_cost.get(current_phase, 0)

    if (
        g()["client_budget"] <= 0
        or (
            current_phase not in ["mtd_opposition", "mtd_ruling", "pi_motion", "pi_reply", "pi_ruling", "post_pi_negotiation", "ended"]
            and g()["client_budget"] < min_future_cost
        )
    ):
        compute_default_judgment()
        return

    if g()["hidden_case"]["plaintiff_budget"] <= 0:
        if g()["plaintiff_weakened"] and g()["phase"] in [
            "mtd_ruling", "pi_motion", "pi_opposition", "pi_reply", "pi_ruling", "post_pi_negotiation"
        ]:
            end_with_outcome({
                "title": "原告撤回推进",
                "kind": "胜利结局",
                "score": 86,
                "route": "击穿对方预算",
                "summary": "对方未能继续维持推进强度。其后续补充材料和程序动作逐渐停滞，案件最终被主动撤回或停止推进。",
                "liability": 0,
            })
        return

def advance_round():
    if g()["outcome"] is not None:
        return

    g()["round"] += 1
    g()["subphase_done"] = False

    g()["risk"] = min(100, g()["risk"] + OPPONENT_PROFILES[g()["opponent_key"]]["risk_up_each_round"])
    spend_plaintiff(random.randint(700, 1500))
    unlock_story_round()

    # 原告预算归零后标记为 weakened，不再直接终结
    hc = g()["hidden_case"]
    if hc["plaintiff_budget"] <= 0 and not g()["plaintiff_weakened"]:
        g()["plaintiff_weakened"] = True
        hc["plaintiff_budget"] = 0
        add_history(
            "对方推进能力严重受限",
            "你判断对方已接近推进极限。后续程序中对方动作将明显减少，裁决天平将向你方倾斜。"
        )

    plaintiff_initiative_offer()
    forced_end_check()

def current_guidance():
    ph = g()["phase"]
    if ph == "intake":
        return "先看材料，找疑点。此阶段不是下结论，而是识别哪里值得花钱。"
    if ph == "investigation":
        return "选择调查方向。程序性调查影响 MTD 路线；版权实体调查影响 PI opposition 的选择和结果。"
    if ph == "research":
        return "研究判例和攻击路径。重点是程序抗辩与版权实体风险。"
    if ph == "strategy":
        return "决定先打 MTD，还是直接进入 PI opposition。"
    if ph == "mtd_motion":
        return "现在提交 Motion to Dismiss。若不能直接切断案件，后面还会进入 PI。"
    if ph == "mtd_opposition":
        return "原告会针对个人管辖和程序门槛反击。注意它会不会补 forum contacts 和 test buy。"
    if ph == "mtd_reply":
        return "MTD reply 只打关键点，不要贪多。"
    if ph == "mtd_ruling":
        return "MTD 即将裁决。若未彻底终结案件，就会进入 PI 主线。"
    if ph == "pi_motion":
        return "现在阅读原告 PI motion。核心看它如何讲侵权成立。"
    if ph == "pi_opposition":
        return "PI opposition 只围绕实体胜算打。你要决定打相似性、保护范围、独立来源，还是权属基础。"
    if ph == "pi_reply":
        return "原告会对你选择的攻击路径作出针对性反击。"
    if ph == "pi_ruling":
        return "法官即将就 PI 作出裁决。这里基本决定案件后续谈判地位。"
    if ph == "post_pi_negotiation":
        return "PI 程序已结束。你现在面对原告的报价，可以接受、砍价，或选择拖延消耗对方资源。注意：律师费耗尽将触发缺席判决。"
    return ""

def reveal_complaint():
    spend_client(ACTIONS_INFO["review_complaint"]["cost"])
    text = g()["review_materials"]["complaint"]

    hc = g()["hidden_case"]

    # 👉 把 complaint 的结构信息写入系统（核心改动）
    if hc["forum_sale"]:
        g()["facts_known"].append("线索：可能存在 Illinois forum contacts")
    else:
        g()["facts_known"].append("线索：Illinois forum contacts 不明确")

    if hc["test_buy"]:
        if hc["test_buy_strength"] == "strong":
            g()["facts_known"].append("线索：测购材料较完整")
        else:
            g()["facts_known"].append("线索：测购材料存在缺口")
    else:
        g()["facts_known"].append("线索：未见明确测购")

    if hc["evidence_issue"]:
        g()["facts_known"].append("线索：证据可能存在时间线问题")

    # 👉 原始 complaint 文本仍然保留
    g()["facts_known"].append(f"材料：{text}")

    add_history("阅读 complaint 摘要", text)
    mark_used("review_complaint")
    g()["subphase_done"] = True

def reveal_client_msg():
    spend_client(ACTIONS_INFO["review_client_msg"]["cost"])
    text = g()["review_materials"]["client_msg"]
    g()["facts_known"].append(f"材料：{text}")
    add_history("阅读客户初步陈述", text)
    mark_used("review_client_msg")
    g()["subphase_done"] = True

def reveal_financials():
    spend_client(ACTIONS_INFO["review_financials"]["cost"])
    hc = g()["hidden_case"]

    text = (
        f"客户补充称：当前被冻结金额约为 ${hc['frozen_amount']:,}，"
        f"涉案产品相关销售金额约为 ${hc['sales_amount']:,}。"
    )

    if hc["plaintiff_expectation"] >= 0.7:
        signal = "线索：原告对获益金额预期较高"
    elif hc["plaintiff_expectation"] >= 0.4:
        signal = "线索：原告对获益金额预期中等"
    else:
        signal = "线索：原告对获益金额预期较低"

    g()["facts_known"].append(f"材料：{text}")
    g()["facts_known"].append(signal)
    add_history("核实冻结金额与销售金额", text)
    trigger_demand("post_intake", "TRO 后初始报价")
    mark_used("review_financials")
    g()["subphase_done"] = True

def investigate_sales():
    spend_client(ACTIONS_INFO["invest_sales"]["cost"])
    hc = g()["hidden_case"]
    text = rand_choice(random.Random(g()["seed"] + g()["round"] * 13), "sales_true" if hc["forum_sale"] else "sales_false")
    g()["facts_known"].append(f"调查结果：{text}")
    add_history("调查销售流向", text)
    mark_used("invest_sales")
    g()["subphase_done"] = True

def investigate_testbuy():
    spend_client(ACTIONS_INFO["invest_testbuy"]["cost"])
    hc = g()["hidden_case"]
    if not hc["test_buy"]:
        text = rand_choice(random.Random(g()["seed"] + 77), "test_false")
    else:
        key = "test_true_strong" if hc["test_buy_strength"] == "strong" else "test_true_weak"
        text = rand_choice(random.Random(g()["seed"] + 91), key)
    g()["facts_known"].append(f"调查结果：{text}")
    add_history("调查测购情况", text)
    mark_used("invest_testbuy")
    g()["subphase_done"] = True

def investigate_evidence():
    spend_client(ACTIONS_INFO["invest_evidence"]["cost"])
    hc = g()["hidden_case"]
    text = rand_choice(random.Random(g()["seed"] + 111), "evidence_issue_true" if hc["evidence_issue"] else "evidence_issue_false")
    g()["facts_known"].append(f"调查结果：{text}")
    add_history("核查证据时间线", text)
    mark_used("invest_evidence")
    g()["subphase_done"] = True

def investigate_work_origin():
    spend_client(ACTIONS_INFO["invest_work_origin"]["cost"])
    hc = g()["hidden_case"]
    ics = hc["independent_creation_support"]
    wt = hc["work_type"]
    if ics == "strong":
        origin_key = "work_origin_strong"
    elif ics == "weak":
        origin_key = "work_origin_weak"
    else:
        origin_key = "work_origin_none"
    origin_text = rand_choice(random.Random(g()["seed"] + 411), origin_key)
    if wt == "simple_product_photo":
        type_key = "work_type_simple"
    elif wt == "styled_product_image":
        type_key = "work_type_styled"
    else:
        type_key = "work_type_creative"
    type_text = rand_choice(random.Random(g()["seed"] + 421), type_key)
    full_text = origin_text + " " + type_text
    g()["facts_known"].append(f"调查结果：{full_text}")
    add_history("调查图片来源与独立性", full_text)
    mark_used("invest_work_origin")
    g()["subphase_done"] = True

def investigate_prior_market():
    spend_client(ACTIONS_INFO["invest_prior_market"]["cost"])
    hc = g()["hidden_case"]
    pad = hc["prior_art_density"]
    if pad == "high":
        key = "prior_market_dense"
    elif pad == "medium":
        key = "prior_market_medium"
    else:
        key = "prior_market_sparse"
    text = rand_choice(random.Random(g()["seed"] + 431), key)
    g()["facts_known"].append(f"调查结果：{text}")
    add_history("调查市场在先作品", text)
    mark_used("invest_prior_market")
    g()["subphase_done"] = True

def investigate_similarity():
    spend_client(ACTIONS_INFO["invest_similarity"]["cost"])
    hc = g()["hidden_case"]
    sim = hc["similarity_to_claimed"]
    if sim >= 70:
        key = "similarity_high"
    elif sim >= 45:
        key = "similarity_medium"
    else:
        key = "similarity_low"
    text = rand_choice(random.Random(g()["seed"] + 441), key)
    g()["facts_known"].append(f"调查结果：{text}")
    add_history("对比相似度", text)
    mark_used("invest_similarity")
    g()["subphase_done"] = True

def investigate_ownership():
    spend_client(ACTIONS_INFO["invest_ownership"]["cost"])
    hc = g()["hidden_case"]
    oc = hc["ownership_clarity"]
    if oc == "clear":
        key = "ownership_clear"
    elif oc == "questionable":
        key = "ownership_questionable"
    else:
        key = "ownership_weak"
    text = rand_choice(random.Random(g()["seed"] + 451), key)
    g()["facts_known"].append(f"调查结果：{text}")
    add_history("核查原告版权权属", text)
    mark_used("invest_ownership")
    g()["subphase_done"] = True

def research_pj():
    spend_client(ACTIONS_INFO["research_pj"]["cost"])
    hc = g()["hidden_case"]
    good = (not hc["forum_sale"]) or (hc["test_buy"] and hc["test_buy_strength"] == "weak")
    text = rand_choice(random.Random(g()["seed"] + 131), "pj_case_good" if good else "pj_case_bad")
    g()["research_known"].append(f"研究结果：{text}")
    add_history("研究个人管辖判例", text)
    mark_used("research_pj")
    g()["subphase_done"] = True

def research_inj():
    spend_client(ACTIONS_INFO["research_inj"]["cost"])
    hc = g()["hidden_case"]
    good = hc["evidence_issue"] or (hc["test_buy"] and hc["test_buy_strength"] == "weak")
    text = rand_choice(random.Random(g()["seed"] + 151), "inj_case_good" if good else "inj_case_bad")
    g()["research_known"].append(f"研究结果：{text}")
    add_history("研究禁令标准", text)
    mark_used("research_inj")
    g()["subphase_done"] = True

def research_settle():
    spend_client(ACTIONS_INFO["research_settle"]["cost"])
    hc = g()["hidden_case"]
    pb = hc["plaintiff_budget"]
    initial_pb = hc["plaintiff_budget_initial"]
    budget_ratio = pb / max(initial_pb, 1)
    text = rand_choice(
        random.Random(g()["seed"] + 171),
        "settlement_signal_low_budget" if budget_ratio <= 0.40 else "settlement_signal_high_budget"
    )
    g()["research_known"].append(f"研究结果：{text}")
    add_history("观察对方推进强度", text)
    trigger_demand("post_research", "研究后试探报价")
    mark_used("research_settle")
    g()["subphase_done"] = True

def choose_strategy(strategy_key):
    info = {
        "mtd": "你决定把核心资源押在程序抗辩上，尤其关注 forum contacts 和个人管辖门槛。",
        "inj": "你决定正面处理禁令压力，重点放在紧急性和证据可信度上。",
        "settle": "你决定主打和解压价，希望利用已知事实把对方预期往下压。",
        "attrition": "你决定优先消耗对方推进成本，不急着追求立刻裁定。",
    }
    cost_map = {
        "mtd": ACTIONS_INFO["choose_mtd"]["cost"],
        "inj": ACTIONS_INFO["choose_inj"]["cost"],
        "settle": ACTIONS_INFO["choose_settle"]["cost"],
        "attrition": ACTIONS_INFO["choose_attrition"]["cost"],
    }
    spend_client(cost_map[strategy_key])
    g()["strategy"] = strategy_key
    add_history("确定策略路线", info[strategy_key])
    g()["subphase_done"] = True

def file_motion():
    spend_client(ACTIONS_INFO["file_motion"]["cost"])
    spend_plaintiff(random.randint(1200, 2200))
    g()["mtd_motion_filed"] = True

    if g()["strategy"] is None:
        g()["strategy"] = "mtd"

    mapping = {
        "mtd": "你正式提交了 Motion to Dismiss，核心围绕个人管辖与 forum linkage 展开。",
        "inj": "你正式提交了对 TRO / 初步禁令的对抗性材料，重心放在紧急性和证据可靠性上。",
        "settle": "你发出了正式谈判与和解信号，试图在程序成本进一步扩大前压低预期。",
        "attrition": "你选择以有限动作维持推进，同时逼迫对方持续投入程序成本。",
    }
    add_history("正式出手", mapping[g()["strategy"]])
    g()["subphase_done"] = True

def generate_response():
    hc = g()["hidden_case"]
    texts = []

    if g()["strategy"] in ["mtd", "attrition"]:
        if hc["forum_sale"]:
            texts.append(rand_choice(random.Random(g()["seed"] + 191), "response_add_sales"))
        if hc["test_buy"]:
            texts.append(rand_choice(random.Random(g()["seed"] + 211), "response_add_testbuy"))
        if not texts:
            texts.append(rand_choice(random.Random(g()["seed"] + 231), "response_emphasize_urgency"))
    elif g()["strategy"] == "inj":
        texts.append(rand_choice(random.Random(g()["seed"] + 251), "response_emphasize_urgency"))
        if hc["test_buy"]:
            texts.append(rand_choice(random.Random(g()["seed"] + 271), "response_add_testbuy"))
    else:
        texts.append(rand_choice(random.Random(g()["seed"] + 291), "response_emphasize_urgency"))

    response_text = " ".join(texts)
    add_history("对方 response", response_text)
    spend_plaintiff(random.randint(1000, 1800))
    g()["response_seen"] = True
    g()["subphase_done"] = True

def submit_reply(reply_key):
    spend_client(ACTIONS_INFO[reply_key]["cost"])

    if reply_key == "reply_attack_timeline":
        text = rand_choice(random.Random(g()["seed"] + 311), "reply_attack_timeline")
    elif reply_key == "reply_attack_pj":
        text = rand_choice(random.Random(g()["seed"] + 331), "reply_attack_pj")
    else:
        text = rand_choice(random.Random(g()["seed"] + 351), "reply_narrow")

    add_history("我方 reply", text)
    g()["reply_done"] = True
    g()["reply_choice"] = reply_key
    g()["subphase_done"] = True

def generate_mtd_opposition():
    hc = g()["hidden_case"]
    texts = []

    if hc["forum_sale"]:
        texts.append("原告 opposition 强调你客户存在 Illinois 订单，并主张这些记录足以支撑 forum contacts。")
    else:
        texts.append("原告 opposition 试图用 nationwide availability 补强个人管辖，但对具体 Illinois contacts 的展开仍较薄弱。")

    if hc["test_buy"]:
        if hc["test_buy_strength"] == "strong":
            texts.append("原告进一步强调 Illinois test buy 记录较完整，试图把程序争点拉回到具体交易。")
        else:
            texts.append("原告提到做过 Illinois test buy，但其 supporting detail 仍不算完整。")

    opposition_text = " ".join(texts)
    add_history("原告对 MTD 的 opposition", opposition_text)
    spend_plaintiff(random.randint(1000, 1800))
    g()["mtd_opposition_seen"] = True
    g()["subphase_done"] = True

def submit_mtd_reply(reply_key):
    if reply_key in g()["mtd_reply_choices"]:
        return
    spend_client(ACTIONS_INFO[reply_key]["cost"])

    seed_offset = {"reply_attack_timeline": 311, "reply_attack_pj": 331, "reply_narrow": 351}
    text = rand_choice(random.Random(g()["seed"] + seed_offset[reply_key]), reply_key)

    add_history(f"MTD reply：{ACTIONS_INFO[reply_key]['label']}", text)
    g()["mtd_reply_choices"].append(reply_key)
    g()["mtd_reply_done"] = True
    g()["subphase_done"] = True

def generate_pi_motion():
    hc = g()["hidden_case"]
    pi_score = compute_pi_merits_score()
    dmg = compute_copyright_damages()

    texts = []

    if pi_score >= 70:
        texts.append("原告 PI motion 强调其版权作品保护较强，且被告作品与原告作品高度相似。")
    elif pi_score >= 45:
        texts.append("原告 PI motion 主张两者在关键表达上存在较高重合，并试图把争议描述为普通 copying case。")
    else:
        texts.append("原告 PI motion 尝试维持侵权叙事，但其对作品独特性和相似性的论证并不十分扎实。")

    if hc["prior_art_density"] == "high":
        texts.append("你注意到 motion 对市场上在先类似作品的讨论很少。")

    if hc["independent_creation_support"] == "strong":
        texts.append("motion 并未正面回应你方可能主张的独立来源问题。")

    if dmg["willful"]:
        texts.append("原告在 motion 中明确主张被告系故意侵权，并据此请求法院适用法定赔偿上限。")

    motion_text = " ".join(texts)
    add_history("原告 PI motion", motion_text)
    spend_plaintiff(random.randint(1200, 2200))
    g()["pi_motion_seen"] = True
    g()["subphase_done"] = True

def submit_pi_opposition(choice_key):
    if choice_key in g()["pi_opposition_choices"]:
        return
    spend_client(ACTIONS_INFO[choice_key]["cost"])

    mapping = {
        "pi_attack_similarity": "你在 PI opposition 中主打相似性不足，强调客户作品与原告作品并未达到足以支持禁令的相似程度。",
        "pi_attack_scope": "你在 PI opposition 中主张原告作品保护范围较薄，且市场上在先类似作品丰富。",
        "pi_assert_independent_creation": "你在 PI opposition 中主张客户作品存在独立来源或供应商来源，削弱 copying from plaintiff 的叙事。",
        "pi_attack_ownership": "你在 PI opposition 中攻击原告的权属与材料基础，主张其当前记录不足以支撑 PI。",
    }

    add_history(f"PI opposition：{ACTIONS_INFO[choice_key]['label']}", mapping[choice_key])
    g()["pi_opposition_choices"].append(choice_key)
    g()["subphase_done"] = True

def generate_pi_reply():
    choices = g()["pi_opposition_choices"]
    hc = g()["hidden_case"]
    texts = []

    reply_map = {
        "pi_attack_similarity": "原告 PI reply 强调两边在构图、角度和关键细节上的重合，试图把争议重新拉回到核心相似性。",
        "pi_attack_scope": "原告 PI reply 主张其作品并非普通通用表达，而是具有独特组合与可受保护的选择安排。",
        "pi_assert_independent_creation": "原告 PI reply 攻击你方所谓独立来源链条，主张该来源并未被完整、可信地证明。",
        "pi_attack_ownership": "原告 PI reply 补强其权属和来源叙事，强调现有记录已足以支撑当前阶段的 PI。",
    }

    if not choices:
        texts.append("你方未提交正式 PI opposition，原告 PI reply 仅作形式性补充。")
    else:
        for key in choices:
            texts.append(reply_map[key])

    text = " ".join(texts)
    add_history("原告 PI reply", text)
    spend_plaintiff(random.randint(900, 1600))
    g()["pi_reply_seen"] = True
    g()["subphase_done"] = True

def compute_current_demand(stage):
    hc = g()["hidden_case"]
    base = hc["plaintiff_expected_recovery"]
    opp = g()["opponent_key"]

    if opp == "aggressive":
        multiplier = 1.45
    elif opp == "gray":
        multiplier = 1.25
    else:
        multiplier = 1.05

    demand = int(base * multiplier)

    # 节点修正
    if stage == "post_intake":
        demand = int(demand * 1.05)
    elif stage == "post_research":
        demand = int(demand * 1.0)
    elif stage == "post_mtd_win":
        demand = int(demand * 0.15)
    elif stage == "post_mtd_partial":
        demand = int(demand * 0.7)
    elif stage == "post_mtd_loss":
        demand = int(demand * 1.25)
    elif stage == "pre_pi":
        demand = int(demand * 1.15)
    elif stage == "post_pi_loss":
        demand = int(demand * 1.35)
    elif stage == "post_pi_limit":
        demand = int(demand * 0.8)
    elif stage == "post_pi_denied":
        demand = int(demand * 0.2)

    # 证据与实体修正
    pi_score = compute_pi_merits_score()
    demand += int((pi_score - 50) * 120)

    if hc["evidence_issue"]:
        demand -= 2500
    if "线索：Illinois forum contacts 不明确" in g()["facts_known"]:
        demand -= 1200
    if "线索：测购材料存在缺口" in g()["facts_known"] or "线索：未见明确测购" in g()["facts_known"]:
        demand -= 1500
    if "线索：证据可能存在时间线问题" in g()["facts_known"]:
        demand -= 1800

    return max(0, demand)

def trigger_demand(stage, label):
    if stage in g()["demand_stage_seen"]:
        return

    demand = compute_current_demand(stage)
    g()["current_demand"] = demand
    g()["settlement_history"].append({
        "stage": stage,
        "label": label,
        "demand": demand,
    })
    g()["demand_stage_seen"].append(stage)

    add_history("原告报价", f"{label}：原告提出和解条件，要求支付 ${demand:,}。")

def settlement_decision(action, counter_amount=None):
    demand = g()["current_demand"]

    if action == "accept":
        end_with_outcome({
            "title": "最终和解",
            "kind": "中等结局" if demand > 5000 else "较好结局",
            "score": 60,
            "route": "接受原告报价",
            "summary": f"你接受了原告当前报价，案件以和解金额 ${demand:,} 结束。",
            "liability": demand,
        })
        return

    if action == "counter":
        g()["counter_offer_last"] = counter_amount

        hc = g()["hidden_case"]
        floor_price = int(hc["plaintiff_expected_recovery"] * 0.55)

        if counter_amount >= floor_price:
            end_with_outcome({
                "title": "还价后和解",
                "kind": "较好结局" if counter_amount <= demand * 0.75 else "中等结局",
                "score": 66,
                "route": "还价成功",
                "summary": f"你提出 ${counter_amount:,} 的还价，原告最终接受，案件以该金额结案。",
                "liability": counter_amount,
            })
        else:
            add_history("还价结果", f"你提出 ${counter_amount:,} 的还价，原告拒绝。当前报价仍为 ${demand:,}。")
        return

    if action == "reject":
        add_history("拒绝报价", f"你拒绝了原告 ${demand:,} 的报价，决定继续推进案件。")

def generate_pi_reply():
    choice = g()["pi_opposition_choice"]

    if choice == "pi_attack_similarity":
        text = "原告 PI reply 强调两边在构图、角度和关键细节上的重合，试图把争议重新拉回到核心相似性。"
    elif choice == "pi_attack_scope":
        text = "原告 PI reply 主张其作品并非普通通用表达，而是具有独特组合与可受保护的选择安排。"
    elif choice == "pi_assert_independent_creation":
        text = "原告 PI reply 攻击你方所谓独立来源链条，主张该来源并未被完整、可信地证明。"
    else:
        text = "原告 PI reply 补强其权属和来源叙事，强调现有记录已足以支撑当前阶段的 PI。"

    add_history("原告 PI reply", text)
    spend_plaintiff(random.randint(900, 1600))
    g()["pi_reply_seen"] = True
    g()["subphase_done"] = True

def attempt_settlement():
    stage = f"{g()['phase']}_manual"

    if g().get("current_demand") is None:
        trigger_demand(stage, "你方主动提出和解后，原告给出报价")
    else:
        add_history("和解动态", f"当前已有原告报价：${g()['current_demand']:,}。你可以接受、拒绝或还价。")

def contains_any(items, substrings):
    return any(any(s in item for s in substrings) for item in items)

def evaluate_outcome():
    hc = g()["hidden_case"]
    judge = JUDGE_PROFILES[g()["judge_key"]]
    fk = g()["facts_known"]
    rk = g()["research_known"]
    strat = g()["strategy"]
    reply_choice = g().get("reply_choice", None)

    mtd_score = 0.25
    inj_score = 0.25
    settle_score = 0.25
    attrition_score = 0.25

    if "线索：Illinois forum contacts 不明确" in fk:
        mtd_score += 0.26
        settle_score += 0.08
    if "线索：可能存在 Illinois forum contacts" in fk:
        mtd_score -= 0.25
        inj_score -= 0.05

    if "线索：未见明确测购" in fk or "线索：测购材料存在缺口" in fk:        
        mtd_score += 0.12
        inj_score += 0.08
    if "线索：测购材料较完整" in fk:
        mtd_score -= 0.16
        inj_score -= 0.08

    if "线索：证据可能存在时间线问题" in fk:
        inj_score += 0.24
        settle_score += 0.14
        mtd_score += 0.08

    if contains_any(rk, ["forum linkage 并不宽容", "态度较谨慎"]):
        mtd_score += 0.10
    if contains_any(rk, ["接受了较有限的本州联系", "个人管辖抗辩会明显变难"]):
        mtd_score -= 0.10

    if contains_any(rk, ["并不会自动跟着权利主张一起落下", "材料若有瑕疵"]):
        inj_score += 0.10
    if contains_any(rk, ["平台风险和持续销售", "禁令压力会上升"]):
        inj_score -= 0.08

    if contains_any(rk, ["推进速度开始放缓", "推进力度较之前减弱"]):
        settle_score += 0.12
        attrition_score += 0.20
    if contains_any(rk, ["仍有继续投入资源的迹象", "没有表现出明显收缩预算"]):
        attrition_score -= 0.08

    mtd_score += judge["mtd_bonus"]
    inj_score += judge["inj_bonus"]
    settle_score += judge["settle_bonus"]

    if g()["risk"] >= 60:
        settle_score += 0.08
        attrition_score -= 0.05

    if g()["client_budget"] <= g()["initial_client_budget"] * 0.35:
        settle_score += 0.08
        inj_score -= 0.08

    plaintiff_budget_ratio = hc["plaintiff_budget"] / max(hc["plaintiff_budget_initial"], 1)
    if plaintiff_budget_ratio <= 0.20:
        attrition_score += 0.22
        settle_score += 0.12

    if g()["plaintiff_weakened"]:
        attrition_score += 0.18
        settle_score += 0.10
        inj_score += 0.08

    # MTD result carry-over into PI evaluation
    mtd_result = g().get("mtd_result")
    if mtd_result == "denied":
        inj_score -= 0.10
        settle_score -= 0.06
    elif mtd_result == "partial":
        inj_score -= 0.04

    if strat == "mtd":
        mtd_score += 0.16
    if strat == "inj":
        inj_score += 0.16
    if strat == "settle":
        settle_score += 0.16
    if strat == "attrition":
        attrition_score += 0.18

    reply_choices = g().get("mtd_reply_choices", [])

    decay = [1.0, 0.70, 0.50, 0.30]

    # MTD reply multi-select scoring
    reply_bonus_map = {
        "reply_attack_timeline": {"inj": 0.12 if hc["evidence_issue"] else -0.04, "settle": 0.06 if hc["evidence_issue"] else 0},
        "reply_attack_pj": {"mtd": 0.12 if not hc["forum_sale"] else 0.02},
        "reply_narrow": {"settle": 0.03},
    }
    for idx, rc in enumerate(reply_choices):
        mult = decay[min(idx, len(decay) - 1)]
        bonuses = reply_bonus_map.get(rc, {})
        for score_key, bonus in bonuses.items():
            if score_key == "mtd":
                mtd_score += bonus * mult
            elif score_key == "inj":
                inj_score += bonus * mult
            elif score_key == "settle":
                settle_score += bonus * mult

    # merits clues from investigation
    fk_str = " ".join(fk)
    if "独立来源叙事可以成立" in fk_str or "完整的图片来源记录" in fk_str:
        inj_score += 0.14
        settle_score += 0.08
    elif "来源链条不完整" in fk_str or "独立来源的可信度有限" in fk_str:
        inj_score -= 0.04
    elif "完全无法说明" in fk_str or "独立来源抗辩基础很薄弱" in fk_str:
        inj_score -= 0.10

    if "大量与原告图片风格" in fk_str or "大幅压缩" in fk_str:
        inj_score += 0.14
        settle_score += 0.06
    elif "几张风格近似" in fk_str:
        inj_score += 0.05
    elif "未能找到与原告图片高度相似" in fk_str:
        inj_score -= 0.06

    if "构图简单" in fk_str or "通用产品图风格" in fk_str:
        inj_score += 0.10
        settle_score += 0.05
    elif "超出了普通产品图的范畴" in fk_str or "可识别的创意表达" in fk_str:
        inj_score -= 0.10

    if "相似点有限" in fk_str or "相似性主张基础不强" in fk_str:
        inj_score += 0.14
        settle_score += 0.06
    elif "相似程度较高" in fk_str or "正面否认相似性的空间较窄" in fk_str:
        inj_score -= 0.12

    if "漏洞较多" in fk_str or "登记链条不完整" in fk_str:
        inj_score += 0.12
        settle_score += 0.06
    elif "链条并不完全清晰" in fk_str or "有一定落差" in fk_str:
        inj_score += 0.05
    elif "链条清晰" in fk_str or "权属基础较难攻击" in fk_str:
        inj_score -= 0.06

    # PI opposition multi-select alignment bonus with decay
    poc_list = g().get("pi_opposition_choices", [])
    poc_bonus_map = {
        "pi_assert_independent_creation": 0.10 if hc["independent_creation_support"] == "strong" else (-0.08 if hc["independent_creation_support"] == "none" else 0),
        "pi_attack_scope": 0.10 if hc["prior_art_density"] == "high" else (-0.06 if hc["prior_art_density"] == "low" else 0),
        "pi_attack_similarity": 0.10 if hc["similarity_to_claimed"] < 45 else (-0.08 if hc["similarity_to_claimed"] >= 70 else 0),
        "pi_attack_ownership": 0.10 if hc["ownership_clarity"] == "weak" else (-0.06 if hc["ownership_clarity"] == "clear" else 0),
    }
    for idx, poc in enumerate(poc_list):
        mult = decay[min(idx, len(decay) - 1)]
        bonus = poc_bonus_map.get(poc, 0)
        inj_score += bonus * mult

    path_scores = {
        "mtd": mtd_score,
        "inj": inj_score,
        "settle": settle_score,
        "attrition": attrition_score,
    }

    non_settle_scores = {k: v for k, v in path_scores.items() if k != "settle"}
    best_path = max(non_settle_scores, key=non_settle_scores.get)
    best_score = path_scores[best_path]

    if best_path == "mtd":
        if best_score >= 0.72:
            out = {
                "title": "Motion to Dismiss 获准",
                "kind": "胜利结局",
                "score": 94,
                "route": "程序性胜利",
                "summary": "法院接受了你的程序逻辑，认为现有记录不足以支撑本州个人管辖或至少不足以在当前阶段继续推进。",
            }
        elif best_score >= 0.58:
            out = {
                "title": "Motion to Dismiss 部分成功",
                "kind": "较好结局",
                "score": 81,
                "route": "部分程序胜利",
                "summary": "法院没有完全终结案件，但明显接受了你的一部分程序性主张，原告后续推进成本上升。",
            }
        else:
            out = {
                "title": "程序抗辩失败",
                "kind": "失败结局",
                "score": 28,
                "route": "程序路线失利",
                "summary": "法院认为当前记录不足以支持你要求在此节点终结案件，程序抗辩未奏效。",
            }
    elif best_path == "inj":
        if best_score >= 0.70:
            out = {
                "title": "禁令压力被显著削弱",
                "kind": "较好结局",
                "score": 84,
                "route": "禁令防守胜利",
                "summary": "法院对原告证据可信度、紧急性或推进逻辑产生疑问，禁令压力明显下降。",
            }
        elif best_score >= 0.56:
            out = {
                "title": "局部顶住禁令压力",
                "kind": "中等结局",
                "score": 63,
                "route": "有限度的防守成功",
                "summary": "你没有彻底改写局势，但至少把最坏结果挡在门外，争取到了继续操作的空间。",
            }
        else:
            out = {
                "title": "禁令对抗失败",
                "kind": "失败结局",
                "score": 25,
                "route": "正面对抗失利",
                "summary": "你选择了最硬的一条路，但现有材料和资源不足以支撑这一方向。",
            }
    else:
        if best_score >= 0.68:
            out = {
                "title": "原告推进崩塌",
                "kind": "胜利结局",
                "score": 87,
                "route": "消耗战胜利",
                "summary": "你没有追求立刻裁定，而是成功把对方拖入高成本、低收益的局面，最终击穿其推进能力。",
            }
        elif best_score >= 0.52:
            out = {
                "title": "对方推进明显放缓",
                "kind": "中上结局",
                "score": 68,
                "route": "消耗战占优",
                "summary": "对方尚未完全退出，但其后续推进能力和意愿都明显下降，你获得了更大回旋空间。",
            }
        else:
            out = {
                "title": "消耗战未奏效",
                "kind": "失败结局",
                "score": 32,
                "route": "拖延未形成优势",
                "summary": "你试图拖垮对方，但对方预算与推进意愿比预期更强，拖延反而加重了本方压力。",
            }

    g()["path_scores"] = path_scores

    # 记录 PI 是否被批准，进入 post_pi_negotiation 而不是直接结束
    pi_granted = (best_path == "inj" and best_score < 0.56) or (best_path == "attrition" and best_score < 0.52)
    g()["pi_granted"] = pi_granted
    g()["pi_ruling_out"] = out
    g()["post_pi_phase"] = "post_pi_negotiation"
    g()["phase"] = "post_pi_negotiation"
    g()["subphase_done"] = False

    # 初始化 post_pi 报价
    dmg = compute_copyright_damages()
    base = dmg["chosen_amount"]
    if pi_granted:
        offer = int(base * random.uniform(0.75, 0.95))
    elif best_path == "inj" and best_score >= 0.70:
        offer = int(base * random.uniform(0.12, 0.22))
    elif best_path == "inj":
        offer = int(base * random.uniform(0.30, 0.50))
    else:
        offer = int(base * random.uniform(0.20, 0.40))

    g()["current_demand"] = max(500, offer)
    g()["post_pi_initial_demand"] = g()["current_demand"]
    add_history(
        "PI 裁决后原告报价",
        f"PI 程序结束。原告律师发来邮件，提出和解报价 ${g()['current_demand']:,}。"
        f"{'禁令已获批准，' if pi_granted else ''}你现在可以接受、砍价或选择拖延。"
    )

def compute_default_judgment():
    dmg = compute_copyright_damages()
    merits = compute_pi_merits_score()
    pi_granted = g().get("pi_granted", False)
    willful = dmg["willful"]

    if willful and pi_granted:
        title = "缺席判决·故意侵权"
        amount = min(150000, int(dmg["chosen_amount"] * 1.0))
        kind = "失败结局"
        score_val = 2
        summary = f"律师费耗尽后缺席应诉。法院认定被告故意侵权，判决法定赔偿上限 ${amount:,}，并可能附加律师费偿还。"
    elif willful:
        title = "缺席判决·故意侵权"
        amount = min(150000, dmg["chosen_amount"])
        kind = "失败结局"
        score_val = 5
        summary = f"律师费耗尽后缺席应诉。法院认定故意侵权，判决 ${amount:,}。"
    elif merits >= 65:
        title = "缺席判决·高额赔偿"
        amount = int(dmg["chosen_amount"] * 0.90)
        kind = "失败结局"
        score_val = 10
        summary = f"律师费耗尽后缺席应诉。版权实体较强，法院判决 ${amount:,}。"
    elif merits >= 40:
        title = "缺席判决·中额赔偿"
        amount = int(dmg["chosen_amount"] * 0.55)
        kind = "失败结局"
        score_val = 15
        summary = f"律师费耗尽后缺席应诉。法院判决赔偿 ${amount:,}。"
    else:
        title = "缺席判决·低额赔偿"
        amount = max(750, int(dmg["chosen_amount"] * 0.20))
        kind = "失败结局"
        score_val = 22
        summary = f"律师费耗尽后缺席应诉。版权实体较弱，法院判决最低档赔偿 ${amount:,}。"

    end_with_outcome({
        "title": title,
        "kind": kind,
        "score": score_val,
        "route": "缺席判决",
        "summary": summary,
        "liability": amount,
        "damage_detail": dmg,
    })

def post_pi_delay():
    g()["post_pi_delay_rounds"] += 1
    spend_client(random.randint(800, 1400))
    spend_plaintiff(random.randint(600, 1200))

    # 原告报价随预算压缩下降
    hc = g()["hidden_case"]
    ratio = hc["plaintiff_budget"] / max(hc["plaintiff_budget_initial"], 1)
    current = g()["current_demand"]
    decay_factor = 0.85 if ratio < 0.30 else (0.93 if ratio < 0.50 else 0.98)
    new_demand = max(500, int(current * decay_factor))
    g()["current_demand"] = new_demand

    add_history(
        "选择拖延",
        f"你选择暂不回应，消耗双方资源。对方报价调整为 ${new_demand:,}。"
    )

    # 检查终止条件
    forced_end_check()
    if g()["outcome"] is not None:
        return

    if hc["plaintiff_budget"] <= 0:
        end_with_outcome({
            "title": "原告撤回推进",
            "kind": "胜利结局",
            "score": 82,
            "route": "拖延击穿对方预算",
            "summary": "在 PI 后的拖延阶段，对方预算最终耗尽，案件停止推进，赔偿为零。",
            "liability": 0,
        })
        return

    if g()["post_pi_delay_rounds"] >= 3:
        # 强制裁决
        pi_granted = g().get("pi_granted", False)
        dmg = compute_copyright_damages()
        if pi_granted:
            amount = int(dmg["chosen_amount"] * 0.70)
            title = "强制裁决·PI已批准"
            summary = f"拖延回合耗尽，法院强制推进。PI 已批准，判决赔偿 ${amount:,}。"
        else:
            amount = int(dmg["chosen_amount"] * 0.25)
            title = "强制裁决·PI未批准"
            summary = f"拖延回合耗尽，法院强制推进。PI 未获批准，判决赔偿 ${amount:,}。"
        end_with_outcome({
            "title": title,
            "kind": "中等结局" if not pi_granted else "失败结局",
            "score": 35 if not pi_granted else 20,
            "route": "拖延后强制裁决",
            "summary": summary,
            "liability": amount,
            "damage_detail": dmg,
        })

def legal_analysis_text():
    hc = g()["hidden_case"]
    judge = JUDGE_PROFILES[g()["judge_key"]]["name"]
    out = g()["outcome"]["title"]

    analysis = []

    if hc["forum_sale"]:
        analysis.append("本局底层事实中存在 Illinois 订单，这使程序抗辩天然更难。")
    else:
        analysis.append("本局底层事实中不存在明确 Illinois 订单，这为程序抗辩留下了空间。")

    if hc["test_buy"]:
        if hc["test_buy_strength"] == "strong":
            analysis.append("原告确实掌握了较完整的测购材料，因此单纯否认本州联系并不容易。")
        else:
            analysis.append("原告虽然试图主张测购，但底层支撑并不强，仍有攻击余地。")
    else:
        analysis.append("原告并无实质测购支撑，这削弱了其 forum linkage 叙事。")

    if hc["evidence_issue"]:
        analysis.append("原告材料确实存在时间线或来源链条问题，这一点对禁令对抗和压价谈判都很重要。")
    else:
        analysis.append("原告材料整体并无明显时间线硬伤，因此不能把全部希望押在证据瑕疵上。")

    analysis.append(f"法官风格为 {judge}，这改变了程序与禁令两条路线的权重。")

    if "Motion to Dismiss" in out or "程序抗辩" in out:
        analysis.append("本局裁决主要围绕个人管辖与程序门槛展开。你前期获取的材料和研究，决定了法院是否愿意在当前节点接受程序性切断。")
    elif "禁令" in out or "顶住" in out:
        analysis.append("本局裁决重心落在紧急性、材料可信度和继续推进的正当性上，而不只是权利主张本身。")
    elif "和解" in out:
        analysis.append("本局的实质结果不是法院直接替你赢，而是你通过程序压力和事实不确定性改变了双方议价位置。")
    else:
        analysis.append("本局的核心不是法官立即替你下结论，而是谁能把对方拖入更高成本、更低收益的位置。")

    return " ".join(analysis)

def key_cards_text():
    cards = []
    for x in g()["facts_known"]:
        cards.append(x)
    for x in g()["research_known"]:
        cards.append(x)
    return cards

def counterfactual_text():
    strat = g()["strategy"]
    out = g()["outcome"]["route"]
    hc = g()["hidden_case"]

    if out == "程序性胜利":
        return "如果你在更早阶段就仓促出手，而没有先摸 sales 或 test buy 相关材料，程序路线的成功率会明显下降。"
    if out == "经济性胜利":
        return "如果你继续拖延，风险和双方成本都会继续上升。此时收场未必最漂亮，但很可能是最稳妥的商业结果。"
    if out == "禁令防守胜利":
        return "如果你放弃针对紧急性和证据瑕疵的集中攻击，这一局更容易被原告拉回到平台风险叙事。"
    if out == "消耗战胜利":
        return "如果你过早追求正面裁决，反而可能替对方节约了成本。此局真正的胜点，是让对方持续投入却拿不到稳定回报。"

    if strat == "mtd" and hc["forum_sale"]:
        return "本局其实存在州内订单，程序路线先天就比较吃亏。若改打禁令防守或压价谈判，结果未必更差。"
    if strat == "inj" and not hc["evidence_issue"]:
        return "本局原告材料并无明显硬伤，硬打禁令会更吃资源。若改走程序或消耗路线，也许更合适。"
    if strat == "settle":
        return "若你先补一层程序或证据压力，再进入谈判，结果通常会比现在更好。"

    return "如果你能更早识别本局真正的关键变量，并把预算更集中地压在相关调查与研究上，结局通常会更好。"

def reveal_truths():
    hc = g()["hidden_case"]
    truths = [
        f"底层事实：{'存在' if hc['forum_sale'] else '不存在'} Illinois 订单。",
        f"底层事实：{'存在' if hc['test_buy'] else '不存在'}测购。",
        f"测购强度：{hc['test_buy_strength'] if hc['test_buy'] else '无'}。",
        f"底层事实：原告材料{'存在' if hc['evidence_issue'] else '不存在'}时间线/来源异常。",
        f"冻结金额：约 ${hc['frozen_amount']:,}。",
        f"相关销售金额：约 ${hc['sales_amount']:,}。",
        f"原告初始获益预期：{hc['plaintiff_expectation']}",
        f"原告心理价位中枢：约 ${hc['plaintiff_expected_recovery']:,}",
        f"作品类型：{hc['work_type']}",
        f"在先类似作品丰富程度：{hc['prior_art_density']}",
        f"客户作品与原告作品相似度：{hc['similarity_to_claimed']}",
        f"客户作品与在先市场类似作品相似度：{hc['similarity_to_prior_market']}",
        f"独立来源支持：{hc['independent_creation_support']}",
        f"原告权属清晰度：{hc['ownership_clarity']}",
        f"PI 实体胜算强度：{compute_pi_merits_score()}",
        f"原告隐藏预算：约 ${max(hc['plaintiff_budget'], 0):,}（结局时口径）。",
        f"原告隐藏目标：{hc['plaintiff_goal']}。",
    ]
    return truths

def next_phase_button():
    ph = g()["phase"]
    if ph == "intake":
        return "进入调查阶段"
    if ph == "investigation":
        return "进入法律研究阶段"
    if ph == "research":
        return "进入策略阶段"
    if ph == "strategy":
        return "进入下一程序阶段"
    if ph == "mtd_motion":
        return "查看原告 opposition"
    if ph == "mtd_opposition":
        return "进入 MTD reply"
    if ph == "mtd_reply":
        return "等待 MTD 裁决"
    if ph == "mtd_ruling":
        return "进入 PI 主线"
    if ph == "pi_motion":
        return "进入 PI opposition"
    if ph == "pi_opposition":
        return "提交 PI opposition 并进入下一阶段"
    if ph == "pi_reply":
        return "等待 PI 裁决"
    if ph == "pi_ruling":
        return "查看 PI 裁决结果"
    return ""

def advance_phase():
    current = g()["phase"]
    if current == "ended":
        return

    if current == "intake":
        g()["phase"] = "investigation"
    elif current == "investigation":
        g()["phase"] = "research"
    elif current == "research":
        g()["phase"] = "strategy"
    elif current == "strategy":
        if g()["strategy"] == "mtd":
            g()["phase"] = "mtd_motion"
        else:
            g()["phase"] = "pi_motion"
    elif current == "mtd_motion":
        g()["phase"] = "mtd_opposition"
    elif current == "mtd_opposition":
        g()["phase"] = "mtd_reply"
    elif current == "mtd_reply":
        g()["phase"] = "mtd_ruling"
    elif current == "mtd_ruling":
        g()["phase"] = "pi_motion"
    elif current == "pi_motion":
        g()["phase"] = "pi_opposition"
    elif current == "pi_opposition":
        g()["phase"] = "pi_reply"
    elif current == "pi_reply":
        g()["phase"] = "pi_ruling"
    elif current == "pi_ruling":
        g()["phase"] = "post_pi_negotiation"
    elif current == "post_pi_negotiation":
        g()["phase"] = "ended"

    g()["subphase_done"] = False

    if g()["phase"] in [
        "investigation", "research", "strategy",
        "mtd_motion", "mtd_opposition", "mtd_reply", "mtd_ruling",
        "pi_motion", "pi_opposition", "pi_reply", "pi_ruling",
        "post_pi_negotiation"
    ]:
        advance_round()

def render_sidebar():
    st.sidebar.subheader("当前状态")
    st.sidebar.metric("客户预算", f"${max(g()['client_budget'], 0):,}")
    st.sidebar.metric("回合", f"{min(g()['round'], MAX_ROUNDS)}/{MAX_ROUNDS}")
    st.sidebar.metric("风险", f"{g()['risk']}/100")
    st.sidebar.progress(min(g()["risk"], 100) / 100, text=f"风险：{risk_text(g()['risk'])}")

    st.sidebar.markdown("### 客户画像")
    st.sidebar.write(f"类型：{g()['client']['name']}")
    st.sidebar.write(f"态度：{g()['client']['attitude']}")
    st.sidebar.write(f"目标：{g()['client']['goal']}")

    st.sidebar.markdown("### 对方律师来函")
    if g()["phase"] == "intake":
        st.sidebar.caption("尚未收到对方律师的任何书面沟通。")
    else:
        st.sidebar.info(plaintiff_signal())
        if used("research_settle"):
            st.sidebar.caption(f"（你的判断：{plaintiff_signal_decoded()}）")

    st.sidebar.markdown("### 已获得材料")
    for x in g()["facts_known"][-6:]:
        st.sidebar.write(f"• {x}")
    for x in g()["research_known"][-4:]:
        st.sidebar.write(f"• {x}")

    if st.sidebar.checkbox("显示底层设定（测试用）"):
        st.sidebar.write(f"法官：{JUDGE_PROFILES[g()['judge_key']]['name']}")
        st.sidebar.write(f"对手：{OPPONENT_PROFILES[g()['opponent_key']]['name']}")
        for x in reveal_truths():
            st.sidebar.write(f"• {x}")

def render_intro():
    judge = JUDGE_PROFILES[g()["judge_key"]]
    opp = OPPONENT_PROFILES[g()["opponent_key"]]
    st.markdown("---")
    st.subheader("案情片段")
    for frag in g()["story_fragments"]:
        st.write(frag)
    st.write(f"法院风格：**{judge['name']}**。{judge['description']}")
    st.write(f"对手风格：**{opp['name']}**。{opp['description']}")

def render_phase():
    forced_end_check()
    if g()["outcome"] is not None:
        return

    st.markdown("---")
    st.subheader(f"第 {g()['round']} 回合｜{phase_name()}")
    st.info(current_guidance())
    if g().get("current_demand") is not None and g()["outcome"] is None:
        st.markdown("### 原告当前报价")
        st.warning(f"原告当前和解要求：${g()['current_demand']:,}")

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("接受报价", use_container_width=True, key=f"accept_{g()['phase']}"):
                settlement_decision("accept")
                st.rerun()
        with c2:
            if st.button("拒绝并继续打", use_container_width=True, key=f"reject_{g()['phase']}"):
                settlement_decision("reject")
                g()["current_demand"] = None
                st.rerun()
        with c3:
            if st.button("自动还价 70%", use_container_width=True, key=f"counter_{g()['phase']}"):
                settlement_decision("counter", int(g()["current_demand"] * 0.7))
                if g()["outcome"] is None:
                    g()["current_demand"] = None
                st.rerun()

    st.markdown("### 可选动作")
    if st.button("尝试和解（立即推进谈判）", use_container_width=True, key="quick_settle"):
        attempt_settlement()
        st.rerun()

    early_phases = ["intake", "investigation", "research", "strategy"]
    if g()["phase"] in early_phases:
        st.markdown("#### 跳过准备阶段直接出手")
        jcol1, jcol2 = st.columns(2)
        with jcol1:
            st.caption(f"成本：${ACTIONS_INFO['file_motion']['cost']:,}")
            if st.button("直接提交 MTD（程序性抗辩）", use_container_width=True, key="jump_mtd"):
                if can_pay(ACTIONS_INFO["file_motion"]["cost"]):
                    file_motion()
                    g()["strategy"] = g()["strategy"] or "mtd"
                    g()["phase"] = "mtd_motion"
                    g()["mtd_motion_filed"] = True
                    g()["subphase_done"] = False
                    forced_end_check()
                    st.rerun()
                else:
                    st.warning("预算不足。")
        with jcol2:
            st.caption(f"成本：${ACTIONS_INFO['file_motion']['cost']:,}")
            if st.button("直接应对 PI（跳至 PI opposition）", use_container_width=True, key="jump_pi"):
                if can_pay(ACTIONS_INFO["file_motion"]["cost"]):
                    file_motion()
                    g()["strategy"] = g()["strategy"] or "inj"
                    g()["phase"] = "pi_motion"
                    g()["subphase_done"] = False
                    forced_end_check()
                    st.rerun()
                else:
                    st.warning("预算不足。")

    ph = g()["phase"]

    if ph == "intake":
        col1, col2, col3 = st.columns(3)
        with col1:
            disabled = used("review_complaint") or not can_pay(ACTIONS_INFO["review_complaint"]["cost"])
            if st.button("阅读 complaint 摘要", disabled=disabled, use_container_width=True):
                reveal_complaint()
                forced_end_check()
                st.rerun()
        with col2:
            disabled = used("review_client_msg") or not can_pay(ACTIONS_INFO["review_client_msg"]["cost"])
            if st.button("阅读客户初步陈述", disabled=disabled, use_container_width=True):
                reveal_client_msg()
                forced_end_check()
                st.rerun()
        with col3:
            disabled = used("review_financials") or not can_pay(ACTIONS_INFO["review_financials"]["cost"])
            if st.button("核实冻结金额与销售金额", disabled=disabled, use_container_width=True):
                reveal_financials()
                forced_end_check()
                st.rerun()

        if used("review_complaint") or used("review_client_msg") or used("review_financials"):
            if st.button(next_phase_button(), use_container_width=True):
                advance_phase()
                st.rerun()

    elif ph == "investigation":
        st.caption("程序性调查")
        cols = st.columns(3)
        proc_keys = ["invest_sales", "invest_testbuy", "invest_evidence"]
        for i, k in enumerate(proc_keys):
            with cols[i]:
                disabled = used(k) or not can_pay(ACTIONS_INFO[k]["cost"])
                st.caption(f"成本：${ACTIONS_INFO[k]['cost']:,}")
                if st.button(ACTIONS_INFO[k]["label"], key=k, disabled=disabled, use_container_width=True):
                    if k == "invest_sales":
                        investigate_sales()
                    elif k == "invest_testbuy":
                        investigate_testbuy()
                    else:
                        investigate_evidence()
                    forced_end_check()
                    st.rerun()

        st.caption("版权实体调查")
        cols2 = st.columns(2)
        merits_keys = ["invest_work_origin", "invest_prior_market", "invest_similarity", "invest_ownership"]
        merits_fns = {
            "invest_work_origin": investigate_work_origin,
            "invest_prior_market": investigate_prior_market,
            "invest_similarity": investigate_similarity,
            "invest_ownership": investigate_ownership,
        }
        for i, k in enumerate(merits_keys):
            with cols2[i % 2]:
                disabled = used(k) or not can_pay(ACTIONS_INFO[k]["cost"])
                st.caption(f"成本：${ACTIONS_INFO[k]['cost']:,}")
                if st.button(ACTIONS_INFO[k]["label"], key=k, disabled=disabled, use_container_width=True):
                    merits_fns[k]()
                    forced_end_check()
                    st.rerun()

        all_invest_keys = proc_keys + merits_keys
        if any(used(k) for k in all_invest_keys):
            if st.button(next_phase_button(), use_container_width=True):
                advance_phase()
                st.rerun()

    elif ph == "research":
        cols = st.columns(3)
        action_keys = ["research_pj", "research_inj", "research_settle"]
        for i, k in enumerate(action_keys):
            with cols[i]:
                disabled = used(k) or not can_pay(ACTIONS_INFO[k]["cost"])
                st.caption(f"成本：${ACTIONS_INFO[k]['cost']:,}")
                if st.button(ACTIONS_INFO[k]["label"], key=k, disabled=disabled, use_container_width=True):
                    if k == "research_pj":
                        research_pj()
                    elif k == "research_inj":
                        research_inj()
                    else:
                        research_settle()
                    forced_end_check()
                    st.rerun()

        if used("research_pj") or used("research_inj") or used("research_settle"):
            if st.button(next_phase_button(), use_container_width=True):
                advance_phase()
                st.rerun()

    elif ph == "strategy":
        cols = st.columns(2)
        opts = [
            ("mtd", "确定主打程序抗辩", ACTIONS_INFO["choose_mtd"]["cost"]),
            ("inj", "确定主打禁令对抗", ACTIONS_INFO["choose_inj"]["cost"]),
            ("settle", "确定主打和解压价", ACTIONS_INFO["choose_settle"]["cost"]),
            ("attrition", "确定主打消耗战", ACTIONS_INFO["choose_attrition"]["cost"]),
        ]
        for i, (k, label, cost) in enumerate(opts):
            with cols[i % 2]:
                disabled = g()["strategy"] is not None or not can_pay(cost)
                st.caption(f"成本：${cost:,}")
                if st.button(label, key=f"choose_{k}", disabled=disabled, use_container_width=True):
                    choose_strategy(k)
                    forced_end_check()
                    st.rerun()

        if g()["strategy"] is not None:
            if st.button(next_phase_button(), use_container_width=True):
                advance_phase()
                st.rerun()

    elif ph == "mtd_motion":
        disabled = g()["mtd_motion_filed"] or not can_pay(ACTIONS_INFO["file_motion"]["cost"])
        st.caption(f"成本：${ACTIONS_INFO['file_motion']['cost']:,}")
        if st.button("提交 MTD", disabled=disabled, use_container_width=True):
            spend_client(ACTIONS_INFO["file_motion"]["cost"])
            spend_plaintiff(random.randint(1200, 2200))
            g()["mtd_motion_filed"] = True
            add_history("提交 MTD", "你正式提交了 Motion to Dismiss，核心围绕个人管辖与 forum linkage 展开。")
            forced_end_check()
            st.rerun()

        if g()["mtd_motion_filed"]:
            if st.button(next_phase_button(), use_container_width=True):
                advance_phase()
                st.rerun()

    elif ph == "mtd_opposition":
        if not g()["mtd_opposition_seen"]:
            if st.button("查看原告 opposition", use_container_width=True):
                generate_mtd_opposition()
                forced_end_check()
                st.rerun()
        else:
            if st.button(next_phase_button(), use_container_width=True):
                advance_phase()
                st.rerun()

    elif ph == "mtd_reply":
        cols = st.columns(3)
        reply_keys = ["reply_attack_timeline", "reply_attack_pj", "reply_narrow"]
        for i, k in enumerate(reply_keys):
            with cols[i]:
                already = k in g()["mtd_reply_choices"]
                disabled = already or not can_pay(ACTIONS_INFO[k]["cost"])
                label = f"✓ {ACTIONS_INFO[k]['label']}" if already else ACTIONS_INFO[k]["label"]
                st.caption(f"成本：${ACTIONS_INFO[k]['cost']:,}")
                if st.button(label, key=f"mtd_{k}", disabled=disabled, use_container_width=True):
                    submit_mtd_reply(k)
                    forced_end_check()
                    st.rerun()

        if g()["mtd_reply_done"]:
            if st.button(next_phase_button(), use_container_width=True):
                advance_phase()
                st.rerun()

    elif ph == "mtd_ruling":
        if st.button("查看 MTD 裁决", use_container_width=True):
            hc = g()["hidden_case"]
            score = 0.25

            if "线索：Illinois forum contacts 不明确" in g()["facts_known"]:
                score += 0.26
            if "线索：可能存在 Illinois forum contacts" in g()["facts_known"]:
                score -= 0.25
            if "线索：未见明确测购" in g()["facts_known"] or "线索：测购材料存在缺口" in g()["facts_known"]:
                score += 0.12
            if "线索：测购材料较完整" in g()["facts_known"]:
                score -= 0.16
            if "线索：证据可能存在时间线问题" in g()["facts_known"]:
                score += 0.08
            if "reply_attack_pj" in g()["mtd_reply_choices"]:
                score += 0.08

            score += JUDGE_PROFILES[g()["judge_key"]]["mtd_bonus"]

            if score >= 0.72:
                trigger_demand("post_mtd_win", "MTD 后报价")
                end_with_outcome({
                    "title": "Motion to Dismiss 获准",
                    "kind": "胜利结局",
                    "score": 94,
                    "route": "程序性胜利",
                    "summary": "法院接受了你的程序逻辑，认为现有记录不足以支撑本州个人管辖或至少不足以在当前阶段继续推进。",
                    "liability": 0,
                })
            else:
                if score >= 0.58:
                    text = "法院未完全终结案件，但接受了你的一部分程序性主张。原告随后转入 PI 主线继续推进。"
                    g()["mtd_result"] = "partial"
                    trigger_demand("post_mtd_partial", "MTD 后更新报价")
                else:
                    text = "法院未接受你的程序性切断请求。原告随后全面转入 PI 主线。"
                    g()["mtd_result"] = "denied"
                    trigger_demand("post_mtd_loss", "MTD 后更新报价")

                add_history("MTD 裁决", text)
                g()["phase"] = "pi_motion"
                g()["subphase_done"] = False

                if g()["mtd_result"] == "denied":
                    plaintiff_reinforce_budget("mtd_denied")
                    if g()["current_demand"] is not None:
                        boost = random.uniform(1.30, 1.40)
                        g()["current_demand"] = int(g()["current_demand"] * boost)
                        add_history("对方调高报价", f"MTD 被驳回后，对方重新评估胜算，将当前和解要求上调至 ${g()['current_demand']:,}。")
                elif g()["mtd_result"] == "partial":
                    spend_plaintiff(-random.randint(1000, 3000))
                    if g()["current_demand"] is not None:
                        boost = random.uniform(1.05, 1.15)
                        g()["current_demand"] = int(g()["current_demand"] * boost)

            forced_end_check()
            st.rerun()

    elif ph == "pi_motion":
        if not g()["pi_motion_seen"]:
            if st.button("查看原告 PI motion", use_container_width=True):
                generate_pi_motion()
                forced_end_check()
                st.rerun()
        else:
            if st.button(next_phase_button(), use_container_width=True):
                advance_phase()
                st.rerun()

    elif ph == "pi_opposition":
        st.caption("可多选，每个论点单独扣费。选完所有想要的论点后点击提交进入下一阶段。")
        cols = st.columns(2)
        pi_keys = [
            "pi_attack_similarity",
            "pi_attack_scope",
            "pi_assert_independent_creation",
            "pi_attack_ownership",
        ]
        for i, k in enumerate(pi_keys):
            with cols[i % 2]:
                already = k in g()["pi_opposition_choices"]
                disabled = already or not can_pay(ACTIONS_INFO[k]["cost"])
                label = f"✓ {ACTIONS_INFO[k]['label']}" if already else ACTIONS_INFO[k]["label"]
                st.caption(f"成本：${ACTIONS_INFO[k]['cost']:,}")
                if st.button(label, key=f"pi_{k}", disabled=disabled, use_container_width=True):
                    submit_pi_opposition(k)
                    forced_end_check()
                    st.rerun()

        if g()["pi_opposition_choices"]:
            if st.button(next_phase_button(), use_container_width=True):
                advance_phase()
                st.rerun()

    elif ph == "pi_reply":
        if not g()["pi_reply_seen"]:
            if st.button("查看原告 PI reply", use_container_width=True):
                generate_pi_reply()
                forced_end_check()
                st.rerun()
        else:
            if st.button(next_phase_button(), use_container_width=True):
                advance_phase()
                st.rerun()

    elif ph == "pi_ruling":
        if st.button("查看 PI 裁决", use_container_width=True):
            evaluate_outcome()
            forced_end_check()
            st.rerun()

    elif ph == "post_pi_negotiation":
        dmg = compute_copyright_damages()
        pi_granted = g().get("pi_granted", False)

        if pi_granted:
            st.error("禁令已获批准。原告当前处于有利地位。")
        else:
            st.info("禁令未获批准或压力已削弱。你的谈判地位相对有利。")

        st.markdown("### 赔偿风险参考")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("实际损害路径", f"${dmg['path1']:,}")
            st.caption(f"被告利润 ${dmg['defendant_profit']:,} + 原告损失 ${dmg['plaintiff_actual_loss']:,}")
        with c2:
            if dmg["statutory_available"]:
                st.metric("法定赔偿路径", f"${dmg['path2']:,}")
                st.caption(f"{'故意侵权' if dmg['willful'] else '普通侵权'}｜{'登记有效' if dmg['statutory_available'] else '登记存疑'}")
            else:
                st.metric("法定赔偿路径", "不可用")
                st.caption("原告登记存疑，无法主张法定赔偿")
        with c3:
            st.metric("原告可能主张金额", f"${dmg['chosen_amount']:,}")
            st.caption(dmg["chosen_label"])

        st.markdown("### 原告当前报价")
        st.warning(f"当前和解要求：${g()['current_demand']:,}")
        st.caption(f"已拖延回合：{g()['post_pi_delay_rounds']}/3｜律师费剩余：${max(g()['client_budget'], 0):,}")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("接受报价", use_container_width=True, key="post_pi_accept"):
                demand = g()["current_demand"]
                end_with_outcome({
                    "title": "PI 后和解",
                    "kind": "中等结局" if demand > dmg["chosen_amount"] * 0.4 else "较好结局",
                    "score": 52,
                    "route": "PI 后接受报价",
                    "summary": f"PI 程序结束后，你接受了原告的和解报价，案件以 ${demand:,} 结案。",
                    "liability": demand,
                    "damage_detail": dmg,
                })
                st.rerun()
        with col2:
            counter_val = st.number_input(
                "还价金额 ($)", min_value=0,
                value=int(g()["current_demand"] * 0.6),
                step=500, key="post_pi_counter_val"
            )
            if st.button("提交还价", use_container_width=True, key="post_pi_counter"):
                floor = dmg["floor_price"]
                if counter_val >= floor:
                    end_with_outcome({
                        "title": "PI 后砍价成功",
                        "kind": "较好结局",
                        "score": 60,
                        "route": "PI 后砍价成功",
                        "summary": f"你提出 ${counter_val:,} 的还价，原告接受，案件以该金额结案。",
                        "liability": counter_val,
                        "damage_detail": dmg,
                    })
                else:
                    add_history("还价被拒", f"你提出 ${counter_val:,}，低于原告底价 ${floor:,}，原告拒绝。当前报价维持 ${g()['current_demand']:,}。")
                st.rerun()
        with col3:
            delay_disabled = g()["post_pi_delay_rounds"] >= 3
            if st.button("拖延（消耗双方资源）", use_container_width=True, key="post_pi_delay", disabled=delay_disabled):
                post_pi_delay()
                st.rerun()

def render_result():
    st.markdown("---")
    st.subheader("本局结果")
    out = g()["outcome"]
    if "胜利" in out["kind"] or "较好" in out["kind"]:
        st.success(f"{out['title']}｜{out['kind']}｜评分 {out['score']}")
    elif "中等" in out["kind"] or "中上" in out["kind"]:
        st.warning(f"{out['title']}｜{out['kind']}｜评分 {out['score']}")
    else:
        st.error(f"{out['title']}｜{out['kind']}｜评分 {out['score']}")

    st.write(out["summary"])

    st.markdown("### 财务结算")
    liability = out.get("liability", 0)
    cost_spent = out.get("cost_spent", max(0, g()["initial_client_budget"] - g()["client_budget"]))
    net_loss = liability + cost_spent

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        st.metric("赔偿 / 和解金额", f"${liability:,}")
    with fc2:
        st.metric("累计律师费消耗", f"${cost_spent:,}")
    with fc3:
        st.metric("净总损失", f"${net_loss:,}")

    if "damage_detail" in out:
        dmg = out["damage_detail"]
        st.markdown("#### 赔偿路径分析")
        st.caption(
            f"实际损害路径：被告可归因利润 ${dmg['defendant_profit']:,}（贡献系数 {dmg['contribution_rate']:.0%}）"
            f" + 原告实际损失 ${dmg['plaintiff_actual_loss']:,} = ${dmg['path1']:,}"
        )
        if dmg["statutory_available"]:
            st.caption(
                f"法定赔偿路径：${dmg['path2']:,}（{'故意侵权' if dmg['willful'] else '普通侵权'}，"
                f"{'登记有效' if dmg['statutory_available'] else '登记存疑'}）"
            )
        else:
            st.caption("法定赔偿路径：不可用（原告登记存疑）")
        st.caption(f"原告适用路径：{dmg['chosen_label']}，主张金额 ${dmg['chosen_amount']:,}")

    st.markdown("### 位置变化")
    if "initial_position" in out:
        st.write(f"初始位置：**{out['initial_position']['budget_quad']} × {out['initial_position']['fact_quad']}**")
    if "final_position" in out:
        st.write(f"终局位置：**{out['final_position']['cost_quad']} × {out['final_position']['liability_quad']}**")
    if "performance_delta" in out:
        st.caption(f"表现差值：{out['performance_delta']}")

    st.markdown("### 路线结论")
    st.write(f"本局的实际终局路线：**{out['route']}**")

    st.markdown("### 法律分析")
    st.write(legal_analysis_text())

    st.markdown("### 你本局掌握过的材料")
    for x in key_cards_text():
        st.write(f"• {x}")

    st.markdown("### 如果你换一条路")
    st.write(counterfactual_text())

    st.markdown("### 结局时揭晓的标准答案")
    for x in reveal_truths():
        st.write(f"• {x}")

    if "path_scores" in g():
        st.markdown("### 各路线结算倾向")
        for k, v in g()["path_scores"].items():
            st.write(f"• {k}: {round(v, 3)}")

    st.markdown("### 剧情记录")
    for item in reversed(g()["history"]):
        with st.expander(item["title"], expanded=False):
            st.write(item["body"])

if "game" not in st.session_state:
    init_game()

st.title("⚖️ 美国诉讼模拟 Demo")
st.caption("内部测试版本")
st.caption("仅用于模拟与学习交流，不构成法律意见或专业建议。")

top1, top2 = st.columns(2)
with top1:
    if st.button("开始新的一局", use_container_width=True):
        init_game()
        st.rerun()
with top2:
    if st.button("重开同一局", use_container_width=True):
        init_game(seed=g()["seed"])
        st.rerun()

render_sidebar()
render_intro()

if g()["outcome"] is None:
    render_phase()
else:
    render_result()

st.markdown("---")
st.subheader("最近记录")
if not g()["history"]:
    st.write("你还没有行动。")
else:
    for item in reversed(g()["history"][-5:]):
        with st.expander(item["title"], expanded=True):
            st.write(item["body"])
