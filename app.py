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
        "budget_range": (7000, 12000),
        "description": "动作快，敢压强度，愿意把事情推到极限。",
    },
    "conservative": {
        "name": "保守型对手",
        "risk_up_each_round": 5,
        "budget_range": (5000, 9000),
        "description": "节奏较慢，更在意成本控制。",
    },
    "gray": {
        "name": "灰色型对手",
        "risk_up_each_round": 7,
        "budget_range": (6000, 11000),
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
}

COMPLAINT_BLOCKS = {
    "jurisdiction_strong": [
        "Plaintiff alleges that Defendant sold products into Illinois and refers to several Illinois-directed transactions.",
        "Complaint states that Defendant made sales into Illinois and identifies multiple transactions allegedly tied to Illinois consumers.",
    ],
    "jurisdiction_weak": [
        "Complaint refers to nationwide online availability, but does not clearly identify Illinois transactions.",
        "Plaintiff alleges forum contacts in general terms, without clearly setting out specific Illinois transactions.",
    ],
    "testbuy_strong": [
        "Plaintiff states it conducted an Illinois test purchase and includes an order page, shipping details, and an order identifier.",
        "The pleading describes a completed Illinois test buy with screenshots reflecting order and delivery information.",
    ],
    "testbuy_weak": [
        "Plaintiff states that it conducted a test purchase, but the pleading does not clearly identify an order number or shipping confirmation.",
        "The complaint refers to a supposed Illinois test buy, but the supporting detail is limited.",
    ],
    "testbuy_none": [
        "The complaint does not clearly attach a completed Illinois test purchase record.",
        "No complete Illinois test purchase record appears on the face of the pleading.",
    ],
    "urgency_high": [
        "Plaintiff emphasizes ongoing sales, platform risk, and the possibility of continuing harm absent immediate relief.",
        "The complaint repeatedly stresses continuing sales and irreparable harm tied to platform exposure.",
    ],
    "urgency_mid": [
        "Plaintiff asserts continuing harm and requests immediate relief, though the discussion of urgency is relatively brief.",
        "The pleading invokes ongoing harm and platform risk, but the urgency allegations are not especially detailed.",
    ],
    "evidence_strong": [
        "Attached exhibits include screenshots, product comparisons, and transaction-related images.",
        "The pleading is accompanied by screenshots and image-based exhibits that purport to support the allegations.",
    ],
    "evidence_weak": [
        "Some screenshots appear cropped, and the exhibits do not obviously reveal full source information.",
        "The exhibits include screenshots, but they do not clearly disclose full metadata or source context.",
    ],
}

def build_complaint_text(hidden_case, rng):
    parts = []

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
        "motion_filed": False,
        "response_seen": False,
        "reply_done": False,
        "outcome": None,
        "history": [],
        "facts_known": [],
        "research_known": [],
        "used_actions": set(),
        "story_fragments": [
            f"你的客户是一家{client['name']}。{claim['opening']}",
        ],
        "hidden_case": {
            "forum_sale": forum_sale,
            "test_buy": test_buy,
            "test_buy_strength": test_buy_strength,
            "evidence_issue": evidence_issue,
            "plaintiff_budget": plaintiff_budget,
            "plaintiff_goal": plaintiff_goal,
        },
        "review_materials": {
            "complaint": build_complaint_text(
                {
                    "forum_sale": forum_sale,
                    "test_buy": test_buy,
                    "test_buy_strength": test_buy_strength,
                    "evidence_issue": evidence_issue,
                    "plaintiff_goal": plaintiff_goal,
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

def risk_text(v):
    if v < 35:
        return "低"
    if v < 60:
        return "中"
    if v < 80:
        return "高"
    return "极高"

def plaintiff_signal():
    pb = g()["hidden_case"]["plaintiff_budget"]
    if pb <= 3500:
        return "对方近期推进速度开始放缓。"
    if pb <= 5500:
        return "对方仍在推进，但追加投入的力度似乎不如前期。"
    return "对方当前仍有继续投入资源的迹象。"

def phase_name():
    mapping = {
        "intake": "了解案情",
        "investigation": "调查事实",
        "research": "研究法律",
        "strategy": "选择策略",
        "motion": "提交动议",
        "response": "阅读对方 response",
        "reply": "提交我方 reply",
        "ruling": "等待裁决",
        "ended": "本局结束",
    }
    return mapping[g()["phase"]]

def used(action_key):
    return action_key in g()["used_actions"]

def mark_used(action_key):
    g()["used_actions"].add(action_key)

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
        "motion": 1500,
        "response": 0,
        "reply": 700,
        "ruling": 0,
        "ended": 0,
    }

    current_phase = g()["phase"]
    min_future_cost = phase_min_cost.get(current_phase, 0)

    if (
        g()["client_budget"] <= 0
        or (
            current_phase not in ["response", "ruling", "ended"]
            and g()["client_budget"] < min_future_cost
        )
    ):
        g()["outcome"] = {
            "title": "代理终止 / 缺席判决",
            "kind": "失败结局",
            "score": 8,
            "route": "客户预算耗尽",
            "summary": (
                "随着费用持续消耗，客户明确表示无法继续承担后续律师费用。"
                "你被迫退出代理。案件随后进入无人应诉状态，原告申请 default judgment 并获得支持。"
            ),
        }
        g()["phase"] = "ended"
        return

    if g()["hidden_case"]["plaintiff_budget"] <= 0:
        g()["outcome"] = {
            "title": "原告撤回推进",
            "kind": "胜利结局",
            "score": 86,
            "route": "击穿对方预算",
            "summary": (
                "对方未能继续维持推进强度。其后续补充材料和程序动作逐渐停滞，案件最终被主动撤回或停止推进。"
            ),
        }
        g()["phase"] = "ended"
        return

def advance_round():
    if g()["outcome"] is not None:
        return

    g()["round"] += 1
    g()["subphase_done"] = False

    g()["risk"] = min(100, g()["risk"] + OPPONENT_PROFILES[g()["opponent_key"]]["risk_up_each_round"])
    spend_plaintiff(random.randint(700, 1500))
    unlock_story_round()
    forced_end_check()

def current_guidance():
    ph = g()["phase"]
    if ph == "intake":
        return "先看材料，找疑点。此阶段不是下结论，而是识别哪里值得花钱。"
    if ph == "investigation":
        return "选一个事实调查方向。调查结果只会给你材料，不会告诉你好坏。"
    if ph == "research":
        return "研究本 circuit 倾向。它会影响后面的策略与裁决，但不会替你做判断。"
    if ph == "strategy":
        return "现在要定路线。程序抗辩、禁令对抗、和解压价、消耗战，不会同时都最优。"
    if ph == "motion":
        return "决定正式出手。你现在选择的动作，会触发对方 response。"
    if ph == "response":
        return "对方会补材料、补说法或强调紧急性。你要从中看出弱点。"
    if ph == "reply":
        return "reply 不是重打一遍，而是决定你把最后资源压在哪个点上。"
    if ph == "ruling":
        return "法官即将裁定。真正的标准答案会在结局时揭晓。"
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
    pb = g()["hidden_case"]["plaintiff_budget"]
    text = rand_choice(
        random.Random(g()["seed"] + 171),
        "settlement_signal_low_budget" if pb <= 5500 else "settlement_signal_high_budget"
    )
    g()["research_known"].append(f"研究结果：{text}")
    add_history("观察对方推进强度", text)
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
    g()["motion_filed"] = True

    mapping = {
        "mtd": "你正式提交了 Motion to Dismiss，核心围绕个人管辖与 forum linkage 展开。",
        "inj": "你正式提交了对 TRO / 初步禁令的对抗性材料，重心放在紧急性和证据可靠性。",
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
    inj_score -= judge["inj_bonus"]
    settle_score += judge["settle_bonus"]

    if g()["risk"] >= 60:
        settle_score += 0.08
        attrition_score -= 0.05

    if g()["client_budget"] <= g()["initial_client_budget"] * 0.35:
        settle_score += 0.08
        inj_score -= 0.08

    if hc["plaintiff_budget"] <= 4500:
        attrition_score += 0.22
        settle_score += 0.12

    if strat == "mtd":
        mtd_score += 0.16
    if strat == "inj":
        inj_score += 0.16
    if strat == "settle":
        settle_score += 0.16
    if strat == "attrition":
        attrition_score += 0.18

    if reply_choice == "reply_attack_timeline":
        if hc["evidence_issue"]:
            inj_score += 0.12
            settle_score += 0.06
        else:
            inj_score -= 0.04
    elif reply_choice == "reply_attack_pj":
        if not hc["forum_sale"]:
            mtd_score += 0.12
        else:
            mtd_score += 0.02
    elif reply_choice == "reply_narrow":
        settle_score += 0.03

    path_scores = {
        "mtd": mtd_score,
        "inj": inj_score,
        "settle": settle_score,
        "attrition": attrition_score,
    }

    best_path = max(path_scores, key=path_scores.get)
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
    elif best_path == "settle":
        if best_score >= 0.66:
            out = {
                "title": "低价和解成功",
                "kind": "较好结局",
                "score": 77,
                "route": "经济性胜利",
                "summary": "你利用已有事实和程序压力压低了对方预期，案件以可接受成本结束。",
            }
        elif best_score >= 0.50:
            out = {
                "title": "中等和解",
                "kind": "中等结局",
                "score": 60,
                "route": "中间价位收尾",
                "summary": "案件结束了，但你没有拿到特别理想的数字。至少成功止损。",
            }
        else:
            out = {
                "title": "和解条件不佳",
                "kind": "失败结局",
                "score": 34,
                "route": "谈判时点不佳",
                "summary": "你在底牌不够或压力不足时进入谈判，对方没有给出理想条件。",
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
    g()["outcome"] = out
    g()["phase"] = "ended"

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
        return "进入正式出手阶段"
    if ph == "motion":
        return "查看对方 response"
    if ph == "response":
        return "进入 reply 阶段"
    if ph == "reply":
        return "等待法官裁决"
    if ph == "ruling":
        return "结算本局"
    return ""

def advance_phase():
    ph_order = ["intake", "investigation", "research", "strategy", "motion", "response", "reply", "ruling"]
    current = g()["phase"]
    if current == "ended":
        return
    idx = ph_order.index(current)
    if idx < len(ph_order) - 1:
        g()["phase"] = ph_order[idx + 1]
        g()["subphase_done"] = False
        if g()["phase"] in ["investigation", "research", "strategy", "motion", "response", "reply", "ruling"]:
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

    st.sidebar.markdown("### 对方信号")
    st.sidebar.write(plaintiff_signal())

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

    ph = g()["phase"]

    if ph == "intake":
        col1, col2 = st.columns(2)
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

        if used("review_complaint") or used("review_client_msg"):
            if st.button(next_phase_button(), use_container_width=True):
                advance_phase()
                st.rerun()

    elif ph == "investigation":
        cols = st.columns(3)
        action_keys = ["invest_sales", "invest_testbuy", "invest_evidence"]
        for i, k in enumerate(action_keys):
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

        if used("invest_sales") or used("invest_testbuy") or used("invest_evidence"):
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

    elif ph == "motion":
        disabled = g()["motion_filed"] or not can_pay(ACTIONS_INFO["file_motion"]["cost"])
        st.caption(f"成本：${ACTIONS_INFO['file_motion']['cost']:,}")
        if st.button("提交动议 / 正式行动", disabled=disabled, use_container_width=True):
            file_motion()
            forced_end_check()
            st.rerun()

        if g()["motion_filed"]:
            if st.button(next_phase_button(), use_container_width=True):
                advance_phase()
                st.rerun()

    elif ph == "response":
        if not g()["response_seen"]:
            if st.button("查看对方 response", use_container_width=True):
                generate_response()
                forced_end_check()
                st.rerun()
        else:
            if st.button(next_phase_button(), use_container_width=True):
                advance_phase()
                st.rerun()

    elif ph == "reply":
        cols = st.columns(3)
        reply_keys = ["reply_attack_timeline", "reply_attack_pj", "reply_narrow"]
        for i, k in enumerate(reply_keys):
            with cols[i]:
                disabled = g()["reply_done"] or not can_pay(ACTIONS_INFO[k]["cost"])
                st.caption(f"成本：${ACTIONS_INFO[k]['cost']:,}")
                if st.button(ACTIONS_INFO[k]["label"], key=k, disabled=disabled, use_container_width=True):
                    submit_reply(k)
                    forced_end_check()
                    st.rerun()

        if g()["reply_done"]:
            if st.button(next_phase_button(), use_container_width=True):
                advance_phase()
                st.rerun()

    elif ph == "ruling":
        if st.button("查看裁决", use_container_width=True):
            evaluate_outcome()
            forced_end_check()
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
