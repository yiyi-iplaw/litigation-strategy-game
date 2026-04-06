import random
import streamlit as st

st.set_page_config(page_title="美国诉讼模拟 Demo", page_icon="⚖️", layout="centered")

MAX_ROUNDS = 6

INVESTIGATION_ACTIONS = {
    "invest_sales": {
        "label": "调查销售流向",
        "cost": 1500,
        "desc": "核查是否存在 Illinois 订单。这是个人管辖权最关键的一张事实牌。",
    },
    "invest_test_buy": {
        "label": "调查原告是否测购",
        "cost": 1500,
        "desc": "测购会显著影响原告的程序准备程度。",
    },
    "invest_fabrication": {
        "label": "核查对方证据瑕疵",
        "cost": 2000,
        "desc": "高风险高回报。成功时会改变整局走势。",
    },
    "wait": {
        "label": "观望",
        "cost": 0,
        "desc": "本回合不主动出击，保留预算，但风险会上升。",
    },
}

DECISION_ACTIONS = {
    "file_mtd": {
        "label": "提交 Motion to Dismiss",
        "cost": 2000,
        "desc": "终局动作。点击后本局立即结算。",
    },
    "negotiate": {
        "label": "发起正式和解",
        "cost": 500,
        "desc": "终局动作。点击后本局立即结算。",
    },
    "fight_tro": {
        "label": "对抗 TRO / 初步禁令",
        "cost": 2500,
        "desc": "终局动作。点击后本局立即结算。",
    },
}

JUDGE_PROFILES = {
    "strict_procedure": {
        "name": "程序型法官",
        "mtd_bonus": 0.15,
        "settlement_bonus": 0.00,
        "injunction_bonus": -0.05,
        "description": "更看重程序缺陷，对缺乏 forum contacts 的案子更敏感。",
    },
    "rights_holder_friendly": {
        "name": "偏权利人法官",
        "mtd_bonus": -0.10,
        "settlement_bonus": 0.10,
        "injunction_bonus": 0.12,
        "description": "对原告的保护诉求更敏感，程序性动议更难打。",
    },
    "efficiency": {
        "name": "效率型法官",
        "mtd_bonus": 0.05,
        "settlement_bonus": 0.12,
        "injunction_bonus": 0.00,
        "description": "强调尽快收束争议，和解更容易推进。",
    },
}

OPPONENT_PROFILES = {
    "aggressive": {
        "name": "激进型对手",
        "risk_up_each_round": 9,
        "fake_evidence_chance": 0.15,
        "description": "动作快，压力大，愿意把事情推到极限。",
    },
    "conservative": {
        "name": "保守型对手",
        "risk_up_each_round": 5,
        "fake_evidence_chance": 0.03,
        "description": "节奏较慢，更在意成本控制。",
    },
    "gray": {
        "name": "灰色型对手",
        "risk_up_each_round": 7,
        "fake_evidence_chance": 0.30,
        "description": "有概率走极端路线，包括伪造或包装证据。",
    },
}

CLIENT_PROFILES = [
    {
        "key": "small_seller",
        "name": "小卖家",
        "budget_range": (3000, 5000),
        "attitude": "怕冻结，怕拖，偏向尽快止损。",
        "goal": "优先避免链接和资金被冻结。",
    },
    {
        "key": "mid_seller",
        "name": "中型卖家",
        "budget_range": (5000, 9000),
        "attitude": "愿意打一打，但不能失控。",
        "goal": "争取更好的程序结果，同时控制总成本。",
    },
    {
        "key": "strong_client",
        "name": "强势客户",
        "budget_range": (9000, 15000),
        "attitude": "不想示弱，愿意硬打。",
        "goal": "尽量压制原告，必要时正面应对禁令。",
    },
]


def init_game(seed=None):
    if seed is None:
        seed = random.randint(1, 10_000_000)
    rng = random.Random(seed)

    judge_key = rng.choice(list(JUDGE_PROFILES.keys()))
    opponent_key = rng.choice(list(OPPONENT_PROFILES.keys()))
    client_profile = rng.choice(CLIENT_PROFILES)

    budget = rng.randint(client_profile["budget_range"][0], client_profile["budget_range"][1])
    has_il_sales = rng.random() < 0.35
    has_test_buy = rng.random() < 0.45
    fake_evidence = rng.random() < OPPONENT_PROFILES[opponent_key]["fake_evidence_chance"]

    st.session_state.game = {
        "seed": seed,
        "round": 1,
        "budget": budget,
        "initial_budget": budget,
        "risk": 35,
        "phase": "investigation",
        "turn_action_taken": False,
        "turn_summary": "",
        "judge_key": judge_key,
        "opponent_key": opponent_key,
        "client_profile": client_profile,
        "history": [],
        "outcome": None,
        "facts_known": {
            "客户使用的是供应商提供的图片": True,
        },
        "facts_hidden": {
            "是否存在 Illinois 订单": has_il_sales,
            "原告是否做过测购": has_test_buy,
            "对方是否存在伪造或重大证据瑕疵": fake_evidence,
        },
        "story_unlocked": {
            "intro_1": True,
            "intro_2": False,
            "intro_3": False,
            "intro_4": False,
        }
    }


def g():
    return st.session_state.game


def add_history(title, body):
    g()["history"].append({"title": title, "body": body})


def can_pay(cost):
    return g()["budget"] >= cost


def spend(cost):
    g()["budget"] -= cost


def status_text():
    risk = g()["risk"]
    if risk < 35:
        return "低"
    if risk < 60:
        return "中"
    if risk < 80:
        return "高"
    return "极高"


def unlock_story_by_round():
    game = g()
    if game["round"] >= 2:
        game["story_unlocked"]["intro_2"] = True
    if game["round"] >= 3:
        game["story_unlocked"]["intro_3"] = True
    if game["round"] >= 4:
        game["story_unlocked"]["intro_4"] = True


def get_story_fragments():
    game = g()
    client = game["client_profile"]
    unlocked = game["story_unlocked"]

    fragments = []

    if unlocked["intro_1"]:
        fragments.append(
            f"你的客户是一家{client['name']}。刚刚收到 Illinois 起诉通知，原告同时申请了 TRO。"
        )

    if unlocked["intro_2"]:
        fragments.append(
            f"客户当前预算约为 ${game['initial_budget']:,}。客户态度是：{client['attitude']}"
        )

    if unlocked["intro_3"]:
        fragments.append(
            "你从客户处拿到了一部分初步材料，但 forum contacts、测购情况、证据质量仍未完全明朗。"
        )

    if unlocked["intro_4"]:
        fragments.append(
            "随着时间推进，法院对紧急性和程序节奏的关注正在上升。若继续拖延，平台和诉讼压力都可能同步放大。"
        )

    return fragments


def base_case_score():
    game = g()
    score = 35
    fk = game["facts_known"]
    judge = JUDGE_PROFILES[game["judge_key"]]

    if "发现：不存在 Illinois 订单" in fk:
        score += 20
    if "发现：存在 Illinois 订单" in fk:
        score -= 20
    if "发现：原告未做测购" in fk:
        score += 12
    if "发现：原告做过测购" in fk:
        score -= 10
    if "发现：对方证据存在重大瑕疵" in fk:
        score += 18

    score -= max(0, game["risk"] - 35) * 0.35
    score -= max(0, game["initial_budget"] - game["budget"]) * 0.002
    score += judge["mtd_bonus"] * 10
    return score


def forced_ending():
    game = g()
    score = base_case_score()
    if score >= 70:
        game["outcome"] = {
            "title": "逼近终局后达成可接受收场",
            "kind": "中上结局",
            "score": 72,
            "text": "你没有在某一个回合果断打出终局牌，但在 deadline 压力下，仍凭借已掌握的事实把案子压到了可承受区间。",
            "route": "被动但可接受的收尾",
        }
    elif score >= 50:
        game["outcome"] = {
            "title": "被动收尾",
            "kind": "一般结局",
            "score": 55,
            "text": "你积累了一些有利事实，但没有形成 decisive move。案子最后以偏被动的方式收场。",
            "route": "缺乏决定性动作",
        }
    else:
        game["outcome"] = {
            "title": "错过时机",
            "kind": "失败结局",
            "score": 30,
            "text": "你始终没有凑齐牌型，也没有在合适时点出决定性动作。时间把你拖进了坏结局。",
            "route": "时间压力压垮了你",
        }


def end_turn():
    game = g()
    if game["outcome"] is not None:
        return

    game["risk"] = min(
        100,
        game["risk"] + OPPONENT_PROFILES[game["opponent_key"]]["risk_up_each_round"]
    )

    game["round"] += 1
    game["turn_action_taken"] = False
    game["turn_summary"] = ""

    if game["round"] >= 3:
        game["phase"] = "decision"

    unlock_story_by_round()

    if game["round"] > MAX_ROUNDS and game["outcome"] is None:
        forced_ending()


def turn_guidance():
    game = g()
    fk = game["facts_known"]

    if game["phase"] == "investigation":
        if "发现：不存在 Illinois 订单" not in fk and "发现：存在 Illinois 订单" not in fk:
            return "当前最重要的问题：你还不知道是否存在 Illinois 订单。优先确认这个事实。"
        if "发现：原告未做测购" not in fk and "发现：原告做过测购" not in fk:
            return "你已经摸到一张 jurisdiction 相关牌。下一步可以考虑确认原告是否做过测购。"
        return "你已经开始摸到关键牌了。再补一张信息牌，第三回合后就能考虑终局动作。"

    if "发现：不存在 Illinois 订单" in fk and "发现：原告未做测购" in fk:
        return "你手里的程序牌已经很强了。现在最适合考虑 Motion to Dismiss。"
    if "发现：对方证据存在重大瑕疵" in fk:
        return "你抓到了对方证据问题。这是硬打 TRO / 初步禁令的窗口。"
    if game["risk"] >= 60:
        return "风险已经抬高。若手牌一般，可以考虑尽快谈判止损。"
    return "你已进入终局阶段。可以继续补信息，也可以根据现有牌型尝试出手。"


def judge_mtd_unlock():
    fk = g()["facts_known"]
    return (
        "发现：不存在 Illinois 订单" in fk
        or "发现：原告未做测购" in fk
        or g()["round"] >= 4
    )


def judge_fight_unlock():
    fk = g()["facts_known"]
    return (
        "发现：对方证据存在重大瑕疵" in fk
        or "发现：原告未做测购" in fk
        or g()["round"] >= 4
    )


def judge_settlement_unlock():
    return g()["phase"] == "decision" or g()["risk"] >= 55


def do_investigate_sales():
    spend(1500)
    if g()["facts_hidden"]["是否存在 Illinois 订单"]:
        g()["facts_known"]["发现：存在 Illinois 订单"] = True
        g()["turn_summary"] = "你摸到一张坏牌：存在 Illinois 订单。个人管辖权抗辩明显变难。"
        add_history("调查销售流向", g()["turn_summary"])
    else:
        g()["facts_known"]["发现：不存在 Illinois 订单"] = True
        g()["risk"] = max(0, g()["risk"] - 6)
        g()["turn_summary"] = "你摸到一张关键好牌：目前未发现 Illinois 订单。"
        add_history("调查销售流向", g()["turn_summary"])
    g()["turn_action_taken"] = True


def do_investigate_test_buy():
    spend(1500)
    if g()["facts_hidden"]["原告是否做过测购"]:
        g()["facts_known"]["发现：原告做过测购"] = True
        g()["turn_summary"] = "原告做过测购。对方程序准备比你预期更完整。"
        add_history("调查测购", g()["turn_summary"])
    else:
        g()["facts_known"]["发现：原告未做测购"] = True
        g()["risk"] = max(0, g()["risk"] - 4)
        g()["turn_summary"] = "你摸到一张不错的牌：目前未发现原告做过测购。"
        add_history("调查测购", g()["turn_summary"])
    g()["turn_action_taken"] = True


def do_investigate_fabrication():
    spend(2000)
    if g()["facts_hidden"]["对方是否存在伪造或重大证据瑕疵"]:
        g()["facts_known"]["发现：对方证据存在重大瑕疵"] = True
        g()["risk"] = max(0, g()["risk"] - 10)
        g()["turn_summary"] = "你抓到一张高价值牌：对方证据存在重大瑕疵，局势明显向你倾斜。"
        add_history("核查对方证据", g()["turn_summary"])
    else:
        g()["turn_summary"] = "你没有抓到足够有力的瑕疵。这一步花了钱和时间，但没有改写局势。"
        add_history("核查对方证据", g()["turn_summary"])
    g()["turn_action_taken"] = True


def do_wait():
    g()["turn_summary"] = "你选择观望。本回合没有主动出手。"
    add_history("观望", g()["turn_summary"])
    g()["turn_action_taken"] = True


def decide_mtd():
    spend(2000)
    game = g()
    score = 0.35
    fk = game["facts_known"]
    judge = JUDGE_PROFILES[game["judge_key"]]

    if "发现：不存在 Illinois 订单" in fk:
        score += 0.30
    if "发现：存在 Illinois 订单" in fk:
        score -= 0.35
    if "发现：原告未做测购" in fk:
        score += 0.18
    if "发现：原告做过测购" in fk:
        score -= 0.10
    if "发现：对方证据存在重大瑕疵" in fk:
        score += 0.15

    score += judge["mtd_bonus"]
    score -= max(0, game["risk"] - 40) / 200

    if score >= 0.75:
        game["outcome"] = {
            "title": "Motion to Dismiss 获准",
            "kind": "胜利结局",
            "score": 95,
            "text": "你在正确的时点把决定性动作打了出去。法院接受了你的管辖权逻辑，案件被驳回。",
            "route": "程序性压制成功",
        }
    elif score >= 0.58:
        game["outcome"] = {
            "title": "Motion to Dismiss 部分成功",
            "kind": "较好结局",
            "score": 82,
            "text": "法院没有完全照你的路走，但明显接受了你的一部分逻辑。原告压力增大，案件大概率转向低成本和解或异地重诉。",
            "route": "部分程序胜利",
        }
    else:
        game["outcome"] = {
            "title": "Motion to Dismiss 失败",
            "kind": "失败结局",
            "score": 28,
            "text": "你把终局动作打得过早，或者牌型不够。法院不买账，案件局势明显恶化。",
            "route": "程序动作时机错误",
        }
    add_history("你提交了 Motion to Dismiss", game["outcome"]["text"])


def decide_settlement():
    spend(500)
    game = g()
    power = 0.28
    fk = game["facts_known"]
    judge = JUDGE_PROFILES[game["judge_key"]]

    if "发现：不存在 Illinois 订单" in fk:
        power += 0.18
    if "发现：原告未做测购" in fk:
        power += 0.12
    if "发现：对方证据存在重大瑕疵" in fk:
        power += 0.24
    if game["risk"] >= 60:
        power += 0.08

    power += judge["settlement_bonus"]

    if power >= 0.65:
        game["outcome"] = {
            "title": "低价和解成功",
            "kind": "较好结局",
            "score": 78,
            "text": "你在有牌时发起谈判，对方感受到了压力，案件以可接受成本结束。",
            "route": "以谈判实现止损",
        }
    elif power >= 0.45:
        game["outcome"] = {
            "title": "中价和解",
            "kind": "中等结局",
            "score": 62,
            "text": "案件结束了，但你没有拿到特别理想的数字。至少止损成功。",
            "route": "中等成本收尾",
        }
    else:
        game["outcome"] = {
            "title": "和解失败且报价偏高",
            "kind": "失败结局",
            "score": 35,
            "text": "你在底牌不够时谈判，对方把这看成了软弱信号。你拿到的是一个很差的报价。",
            "route": "谈判时点不佳",
        }
    add_history("你发起了正式和解", game["outcome"]["text"])


def decide_fight_tro():
    spend(2500)
    game = g()
    score = 0.32
    fk = game["facts_known"]
    judge = JUDGE_PROFILES[game["judge_key"]]

    if "发现：对方证据存在重大瑕疵" in fk:
        score += 0.28
    if "发现：原告未做测购" in fk:
        score += 0.10
    if "发现：存在 Illinois 订单" in fk:
        score -= 0.12
    if game["budget"] >= 2500:
        score += 0.08
    if game["risk"] >= 55:
        score += 0.06

    score -= judge["injunction_bonus"]

    if score >= 0.62:
        game["outcome"] = {
            "title": "TRO / 初步禁令被显著削弱",
            "kind": "较好结局",
            "score": 80,
            "text": "你选择了硬碰硬，而且碰对了位置。法院对原告证据和紧急性产生疑问，禁令压力明显下降。",
            "route": "正面对抗成功",
        }
    elif score >= 0.46:
        game["outcome"] = {
            "title": "局部顶住压力",
            "kind": "中等结局",
            "score": 60,
            "text": "你没有完全扭转局势，但至少把最坏结果挡在了门外。",
            "route": "有限度地控制风险",
        }
    else:
        game["outcome"] = {
            "title": "正面对抗失败",
            "kind": "失败结局",
            "score": 25,
            "text": "你选择了最贵也最硬的一条路，但牌型不够，资源也不够，最后正面失利。",
            "route": "硬打失败",
        }
    add_history("你集中资源对抗 TRO / 初步禁令", game["outcome"]["text"])


def outcome_key_cards():
    fk = g()["facts_known"]
    cards = []

    if "发现：不存在 Illinois 订单" in fk:
        cards.append("你确认了不存在 Illinois 订单")
    if "发现：存在 Illinois 订单" in fk:
        cards.append("你发现了存在 Illinois 订单，这削弱了程序抗辩")
    if "发现：原告未做测购" in fk:
        cards.append("你确认了原告未做测购")
    if "发现：原告做过测购" in fk:
        cards.append("你发现原告做过测购，这提升了对方准备程度")
    if "发现：对方证据存在重大瑕疵" in fk:
        cards.append("你抓到了对方证据存在重大瑕疵")

    cards.append(f"本案法官风格为：{JUDGE_PROFILES[g()['judge_key']]['name']}")
    cards.append(f"你在第 {min(g()['round'], MAX_ROUNDS)} 回合进入或接近终局动作")

    return cards


def outcome_legal_analysis():
    out = g()["outcome"]
    fk = g()["facts_known"]
    judge = JUDGE_PROFILES[g()["judge_key"]]["name"]

    if out["title"] == "Motion to Dismiss 获准":
        return (
            "法院更重视程序门槛。你所掌握的记录足以削弱原告关于 forum contacts 的论证。"
            "当不存在 Illinois 订单，或者原告缺乏有力测购支撑时，个人管辖权基础会明显变弱。"
            f"在本局中，{judge}进一步放大了这一程序性优势，因此 MTD 获得支持。"
        )

    if out["title"] == "Motion to Dismiss 部分成功":
        return (
            "法院没有完全接受你的全部程序主张，但接受了其中一部分。"
            "这意味着你虽然未能一击终结案件，却成功提高了原告继续推进的成本，"
            "并为后续低成本和解或异地重诉创造了现实压力。"
        )

    if out["title"] == "低价和解成功":
        return (
            "这并不是单纯的妥协，而是利用已有事实牌压低对方预期。"
            "当你已经掌握部分有利程序事实，或对对方证据质量提出有效怀疑时，"
            "和解就不再只是被动止损，而会转化为一种可控收场。"
        )

    if out["title"] == "中价和解":
        return (
            "你形成了一定压力，但压力还不足以彻底压低对方报价。"
            "从法律上看，你的局面并非完全不利，但也没有强到足以迫使对方显著退让。"
            "因此，结局落在了中间区间。"
        )

    if out["title"] == "TRO / 初步禁令被显著削弱":
        return (
            "你选择正面处理禁令风险，而且选对了支点。"
            "在对方证据存在瑕疵、紧急性不足，或者程序准备不稳时，"
            "法院对于禁令的态度往往会明显收紧。本局中，你成功把争点从情绪化紧急性拉回到了证据和程序。"
        )

    if out["title"] == "局部顶住压力":
        return (
            "你没有彻底赢下这一轮程序对抗，但至少阻止了局势进一步恶化。"
            "这类结局通常出现在手牌不够漂亮、但仍能抓住一两个核心薄弱点的时候。"
        )

    if out["title"] == "和解失败且报价偏高":
        return (
            "问题不在于你选择了和解，而在于你过早进入谈判。"
            "当你尚未形成程序压力，或未能证明对方证据存在明显问题时，"
            "对方更容易把你的谈判动作理解为底气不足。"
        )

    if out["title"] == "正面对抗失败":
        return (
            "正面对抗禁令是资源消耗最大的一条路径。"
            "若没有足够强的瑕疵牌、程序牌或预算支撑，硬打往往会把局势进一步推向原告有利的一侧。"
        )

    if out["title"] == "Motion to Dismiss 失败":
        return (
            "程序动议最忌讳两点：事实基础不足，或者出手过早。"
            "如果你尚未确认 forum contacts 的缺失，或者对方已有相对完整的测购和本地联系材料，"
            "法院通常不会愿意在这个节点直接替你终结案件。"
        )

    if out["title"] == "逼近终局后达成可接受收场":
        return (
            "你没有形成最锋利的终局动作，但还是通过有限的事实积累把案件压进了可控范围。"
            "这类结果常见于中等预算、信息不完全、但操作尚算稳健的局面。"
        )

    if out["title"] == "被动收尾":
        return (
            "你并非完全没有收获，只是这些收获未能组合成一个决定性牌型。"
            "从诉讼策略角度看，这意味着你避免了最差结局，但也错过了最好的窗口。"
        )

    return (
        "你没有在合适时点完成从调查到出手的转换。"
        "时间本身成为了对你不利的力量，程序压力、平台风险和谈判位置都随之恶化。"
    )


def outcome_counterfactual():
    out = g()["outcome"]["title"]
    fk = g()["facts_known"]

    if out in ["Motion to Dismiss 获准", "Motion to Dismiss 部分成功"]:
        return (
            "如果你更早贸然提交 MTD，而当时尚未确认 Illinois 订单或测购情况，"
            "成功率会明显下降。相反，如果你在这个节点转向和解，对方很可能仍会坚持更高报价。"
        )

    if out in ["低价和解成功", "中价和解"]:
        return (
            "如果你在现有基础上继续拖延，风险和平台压力可能继续上升。"
            "但如果你手里已经有不存在 Illinois 订单和未测购两张强牌，"
            "也存在改走程序动议、争取更强结果的空间。"
        )

    if out in ["TRO / 初步禁令被显著削弱", "局部顶住压力"]:
        return (
            "如果你放弃正面对抗而直接和解，案件也许会结束得更快，"
            "但你将失去借助证据瑕疵或程序弱点压低对方预期的机会。"
        )

    if "发现：不存在 Illinois 订单" in fk and "发现：原告未做测购" in fk:
        return (
            "你其实已经接近一手漂亮的程序牌型。若在更早的回合果断打出 MTD，"
            "本局存在明显上升空间。"
        )

    return (
        "如果你能在前两回合更集中地围绕 forum contacts、测购或证据质量摸牌，"
        "结局通常会比现在更好。"
    )


if "game" not in st.session_state:
    init_game()

st.title("⚖️ 美国诉讼模拟 Demo")
st.caption("这是一版回合制文字策略原型。每回合做一个选择，结束回合，局势继续推进。")

top1, top2 = st.columns(2)
with top1:
    if st.button("开始新的一局", use_container_width=True):
        init_game()
        st.rerun()
with top2:
    if st.button("重开同一局", use_container_width=True):
        init_game(seed=g()["seed"])
        st.rerun()

with st.sidebar:
    st.subheader("当前状态")
    st.metric("预算", f"${g()['budget']:,}")
    st.metric("回合", f"{min(g()['round'], MAX_ROUNDS)}/{MAX_ROUNDS}")
    st.metric("风险", f"{g()['risk']}/100")
    st.progress(min(g()["risk"], 100) / 100, text=f"风险：{status_text()}")

    st.markdown("### 客户画像")
    st.write(f"类型：{g()['client_profile']['name']}")
    st.write(f"态度：{g()['client_profile']['attitude']}")
    st.write(f"目标：{g()['client_profile']['goal']}")

    st.markdown("### 已知事实")
    for k in g()["facts_known"]:
        st.write(f"• {k}")

    if st.checkbox("显示隐藏设定（测试用）"):
        st.markdown("### 隐藏设定")
        st.write(f"法官风格：{JUDGE_PROFILES[g()['judge_key']]['name']}")
        st.write(f"对手风格：{OPPONENT_PROFILES[g()['opponent_key']]['name']}")
        for k, v in g()["facts_hidden"].items():
            st.write(f"• {k}: {'是' if v else '否'}")

judge = JUDGE_PROFILES[g()["judge_key"]]
opp = OPPONENT_PROFILES[g()["opponent_key"]]

st.markdown("---")
st.subheader("案件背景")
for fragment in get_story_fragments():
    st.write(fragment)

st.write(f"法院风格：**{judge['name']}**。{judge['description']}")
st.write(f"对手风格：**{opp['name']}**。{opp['description']}")

if g()["outcome"] is not None:
    st.markdown("---")
    st.subheader("本局结果")
    out = g()["outcome"]
    if "胜利" in out["kind"] or "较好" in out["kind"]:
        st.success(f"{out['title']}｜{out['kind']}｜评分 {out['score']}")
    elif "中等" in out["kind"] or "中上" in out["kind"]:
        st.warning(f"{out['title']}｜{out['kind']}｜评分 {out['score']}")
    else:
        st.error(f"{out['title']}｜{out['kind']}｜评分 {out['score']}")

    st.write(out["text"])

    st.markdown("### 结论")
    st.write(f"本局路线：{out['route']}")

    st.markdown("### 法律分析")
    st.write(outcome_legal_analysis())

    st.markdown("### 你本局的关键牌")
    for card in outcome_key_cards():
        st.write(f"• {card}")

    st.markdown("### 如果你换一条路")
    st.write(outcome_counterfactual())

    st.markdown("### 剧情记录")
    for item in reversed(g()["history"]):
        with st.expander(item["title"], expanded=False):
            st.write(item["body"])

else:
    st.markdown("---")
    st.subheader(f"第 {g()['round']} 回合")

    if g()["phase"] == "investigation":
        st.info("当前阶段：信息收集。前两回合主要是摸牌。先确认销售流向或测购情况，会比较稳。")
    else:
        st.warning("当前阶段：终局阶段已开启。你可以继续补信息，也可以选择正式出手。")

    st.markdown(f"**局势提示：** {turn_guidance()}")

    if g()["turn_summary"]:
        st.success(f"本回合结果：{g()['turn_summary']}")

    if not g()["turn_action_taken"]:
        st.markdown("### 本回合可选行动")

        cols = st.columns(2)
        inv_keys = list(INVESTIGATION_ACTIONS.keys())
        for idx, key in enumerate(inv_keys):
            action = INVESTIGATION_ACTIONS[key]
            with cols[idx % 2]:
                with st.container(border=True):
                    st.markdown(f"**{action['label']}**")
                    st.write(action["desc"])
                    st.caption(f"成本：${action['cost']:,}")
                    disabled = not can_pay(action["cost"])
                    if st.button(f"选择：{action['label']}", key=f"inv_{key}", use_container_width=True, disabled=disabled):
                        if key == "invest_sales":
                            do_investigate_sales()
                        elif key == "invest_test_buy":
                            do_investigate_test_buy()
                        elif key == "invest_fabrication":
                            do_investigate_fabrication()
                        elif key == "wait":
                            do_wait()
                        st.rerun()

        if g()["phase"] == "decision":
            st.markdown("### 终局动作")
            st.caption("第三回合开始，终局动作逐步开放。点击后本局立即结算。")

            if judge_mtd_unlock():
                action = DECISION_ACTIONS["file_mtd"]
                with st.container(border=True):
                    st.markdown(f"**{action['label']}**")
                    st.write(action["desc"])
                    st.caption(f"成本：${action['cost']:,}")
                    disabled = not can_pay(action["cost"])
                    if st.button(f"最终决定：{action['label']}", key="dec_mtd", use_container_width=True, disabled=disabled):
                        decide_mtd()
                        st.rerun()

            if judge_settlement_unlock():
                action = DECISION_ACTIONS["negotiate"]
                with st.container(border=True):
                    st.markdown(f"**{action['label']}**")
                    st.write(action["desc"])
                    st.caption(f"成本：${action['cost']:,}")
                    disabled = not can_pay(action["cost"])
                    if st.button(f"最终决定：{action['label']}", key="dec_settle", use_container_width=True, disabled=disabled):
                        decide_settlement()
                        st.rerun()

            if judge_fight_unlock():
                action = DECISION_ACTIONS["fight_tro"]
                with st.container(border=True):
                    st.markdown(f"**{action['label']}**")
                    st.write(action["desc"])
                    st.caption(f"成本：${action['cost']:,}")
                    disabled = not can_pay(action["cost"])
                    if st.button(f"最终决定：{action['label']}", key="dec_fight", use_container_width=True, disabled=disabled):
                        decide_fight_tro()
                        st.rerun()

    else:
        st.info("你本回合已经做出选择。现在点击“结束本回合”，让时间继续推进。")

        if st.button("结束本回合 →", use_container_width=True):
            end_turn()
            st.rerun()

    st.markdown("### 最近剧情")
    if not g()["history"]:
        st.write("你还没有行动。")
    else:
        for item in reversed(g()["history"][-5:]):
            with st.expander(item["title"], expanded=True):
                st.write(item["body"])
