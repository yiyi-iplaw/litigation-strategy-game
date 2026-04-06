import random
import streamlit as st

st.set_page_config(page_title="美国诉讼模拟 Demo", page_icon="⚖️", layout="centered")

# -----------------------------
# Data model
# -----------------------------
MAX_ROUNDS = 6
INITIAL_BUDGET = 5000

ACTIONS = {
    "invest_sales": {
        "label": "调查销售流向（是否有 Illinois 订单）",
        "cost": 1500,
        "time": 1,
        "desc": "可能摸到对管辖权最关键的一张牌。",
    },
    "invest_test_buy": {
        "label": "调查原告是否做过测购",
        "cost": 1500,
        "time": 1,
        "desc": "可能削弱对方程序基础，也可能一无所获。",
    },
    "file_mtd": {
        "label": "提交 Motion to Dismiss（缺乏个人管辖权）",
        "cost": 2000,
        "time": 1,
        "desc": "需要较好的事实基础。打早了，可能直接失败。",
    },
    "negotiate": {
        "label": "试探性和解",
        "cost": 500,
        "time": 1,
        "desc": "可以快速止损，但也可能暴露你的软弱。",
    },
    "invest_fabrication": {
        "label": "核查对方证据是否存在伪造或重大瑕疵",
        "cost": 2000,
        "time": 1,
        "desc": "高风险高回报。成功时会大幅改变局势。",
    },
    "wait": {
        "label": "观望一周",
        "cost": 0,
        "time": 1,
        "desc": "保预算，但风险会上升。",
    },
}

JUDGE_PROFILES = {
    "strict_procedure": {
        "name": "程序型法官",
        "mtd_bonus": 0.15,
        "settlement_bonus": 0.00,
        "description": "更看重程序缺陷，对缺乏 forum contacts 的案子更敏感。",
    },
    "rights_holder_friendly": {
        "name": "偏权利人法官",
        "mtd_bonus": -0.10,
        "settlement_bonus": 0.10,
        "description": "对原告的保护诉求更敏感，程序性动议更难打。",
    },
    "efficiency": {
        "name": "效率型法官",
        "mtd_bonus": 0.05,
        "settlement_bonus": 0.10,
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

# -----------------------------
# Helpers
# -----------------------------
def init_game(seed: int | None = None):
    if seed is None:
        seed = random.randint(1, 10_000_000)
    rng = random.Random(seed)

    judge_key = rng.choice(list(JUDGE_PROFILES.keys()))
    opponent_key = rng.choice(list(OPPONENT_PROFILES.keys()))

    # Hidden world state
    has_il_sales = rng.random() < 0.35
    has_test_buy = rng.random() < 0.45
    supplier_images = True
    fake_evidence = rng.random() < OPPONENT_PROFILES[opponent_key]["fake_evidence_chance"]

    st.session_state.game = {
        "seed": seed,
        "rng_seed_note": f"本局种子：{seed}",
        "round": 1,
        "budget": INITIAL_BUDGET,
        "risk": 35,
        "facts_known": {
            "客户没有刻意向 Illinois 销售": True,
            "客户使用的是供应商提供的图片": supplier_images,
        },
        "facts_hidden": {
            "是否存在 Illinois 订单": has_il_sales,
            "原告是否做过测购": has_test_buy,
            "对方是否存在伪造或重大证据瑕疵": fake_evidence,
        },
        "judge_key": judge_key,
        "opponent_key": opponent_key,
        "history": [],
        "outcome": None,
        "revealed_end": False,
    }

def game() -> dict:
    return st.session_state.game

def push_history(title: str, body: str):
    game()["history"].append({"title": title, "body": body})

def can_afford(action_key: str) -> bool:
    return game()["budget"] >= ACTIONS[action_key]["cost"]

def apply_round_cost(action_key: str):
    g = game()
    g["budget"] -= ACTIONS[action_key]["cost"]

def end_round_base_pressure():
    g = game()
    opp = OPPONENT_PROFILES[g["opponent_key"]]
    g["risk"] = min(100, g["risk"] + opp["risk_up_each_round"])
    g["round"] += 1

def ending_check():
    g = game()

    if g["outcome"] is not None:
        return True

    if g["budget"] < 0:
        g["outcome"] = {
            "title": "你把预算打穿了",
            "kind": "失败",
            "text": "预算已经不足以支撑后续动作。客户在压力下被迫接受高价和解。",
            "score": 20,
        }
        return True

    if g["risk"] >= 90:
        g["outcome"] = {
            "title": "风险失控",
            "kind": "失败",
            "text": "法院和对手的压力叠加，客户最终在极不利条件下和解。",
            "score": 25,
        }
        return True

    if g["round"] > MAX_ROUNDS:
        # Timed ending based on state
        known = g["facts_known"]
        if "发现：不存在 Illinois 订单" in known and "发现：原告未做测购" in known:
            g["outcome"] = {
                "title": "程序性胜利",
                "kind": "较好结局",
                "text": "你虽然没有完全终结案件，但成功迫使原告撤回 Illinois 诉讼并考虑异地重诉。",
                "score": 80,
            }
        elif g["risk"] <= 50:
            g["outcome"] = {
                "title": "低成本收尾",
                "kind": "中等结局",
                "text": "你把局势控制在可承受范围内，最终以较低成本和解收场。",
                "score": 65,
            }
        else:
            g["outcome"] = {
                "title": "拖到最后仍未翻盘",
                "kind": "一般结局",
                "text": "你保住了部分局面，但没有凑齐关键牌型，结局偏被动。",
                "score": 45,
            }
        return True

    return False

def action_invest_sales():
    g = game()
    hidden = g["facts_hidden"]["是否存在 Illinois 订单"]
    apply_round_cost("invest_sales")
    if hidden:
        g["facts_known"]["发现：存在 Illinois 订单"] = True
        g["risk"] = min(100, g["risk"] + 8)
        push_history(
            "你调查了销售流向",
            "你摸到一张坏牌：系统显示存在 Illinois 订单。管辖权动议会明显变难。风险上升。"
        )
    else:
        g["facts_known"]["发现：不存在 Illinois 订单"] = True
        g["risk"] = max(0, g["risk"] - 8)
        push_history(
            "你调查了销售流向",
            "你摸到一张关键好牌：目前未发现 Illinois 订单。个人管辖权抗辩显著增强。"
        )
    end_round_base_pressure()

def action_invest_test_buy():
    g = game()
    hidden = g["facts_hidden"]["原告是否做过测购"]
    apply_round_cost("invest_test_buy")
    if hidden:
        g["facts_known"]["发现：原告做过测购"] = True
        g["risk"] = min(100, g["risk"] + 6)
        push_history(
            "你调查了测购情况",
            "对方做过测购。原告在程序准备上比你预期更完整。"
        )
    else:
        g["facts_known"]["发现：原告未做测购"] = True
        g["risk"] = max(0, g["risk"] - 6)
        push_history(
            "你调查了测购情况",
            "你摸到一张不错的牌：目前未发现原告做过测购，这会削弱对方在本地起诉的姿态。"
        )
    end_round_base_pressure()

def action_invest_fabrication():
    g = game()
    hidden = g["facts_hidden"]["对方是否存在伪造或重大证据瑕疵"]
    apply_round_cost("invest_fabrication")
    if hidden:
        g["facts_known"]["发现：对方证据存在重大瑕疵"] = True
        g["risk"] = max(0, g["risk"] - 15)
        push_history(
            "你核查了对方证据",
            "你抓到一张高价值牌：对方证据存在重大瑕疵，甚至接近伪造。局势明显向你倾斜。"
        )
    else:
        push_history(
            "你核查了对方证据",
            "你没有发现足够有力的瑕疵。调查花了钱和时间，但暂时没有实质收获。"
        )
    end_round_base_pressure()

def action_wait():
    g = game()
    apply_round_cost("wait")
    g["risk"] = min(100, g["risk"] + 10)
    push_history(
        "你选择观望",
        "你暂时没有出牌。预算保住了，但对手和法院的压力继续累积。"
    )
    end_round_base_pressure()

def action_negotiate():
    g = game()
    apply_round_cost("negotiate")

    settlement_power = 0.25
    if "发现：不存在 Illinois 订单" in g["facts_known"]:
        settlement_power += 0.20
    if "发现：原告未做测购" in g["facts_known"]:
        settlement_power += 0.15
    if "发现：对方证据存在重大瑕疵" in g["facts_known"]:
        settlement_power += 0.25

    settlement_power += JUDGE_PROFILES[g["judge_key"]]["settlement_bonus"]

    if settlement_power >= 0.65:
        g["outcome"] = {
            "title": "低价和解成功",
            "kind": "较好结局",
            "text": "你利用已掌握的有利事实压低了对方预期，案件以可接受成本结束。",
            "score": 78,
        }
        push_history(
            "你发起了和解试探",
            "对方感受到你手里的牌不差，愿意接受较低金额收场。"
        )
    elif settlement_power >= 0.40:
        g["outcome"] = {
            "title": "中价和解",
            "kind": "中等结局",
            "text": "案件结束了，但你没有拿到特别理想的数字。至少止损成功。",
            "score": 60,
        }
        push_history(
            "你发起了和解试探",
            "对方愿谈，但并不慌。你拿到的是一个中间价位。"
        )
    else:
        g["risk"] = min(100, g["risk"] + 8)
        push_history(
            "你发起了和解试探",
            "对方把你的动作解读为底气不足，提出了偏高的数字。局势没有改善。"
        )
        end_round_base_pressure()

def action_file_mtd():
    g = game()
    apply_round_cost("file_mtd")

    score = 0.35
    if "发现：不存在 Illinois 订单" in g["facts_known"]:
        score += 0.30
    if "发现：存在 Illinois 订单" in g["facts_known"]:
        score -= 0.35
    if "发现：原告未做测购" in g["facts_known"]:
        score += 0.20
    if "发现：原告做过测购" in g["facts_known"]:
        score -= 0.10
    if "发现：对方证据存在重大瑕疵" in g["facts_known"]:
        score += 0.15

    score += JUDGE_PROFILES[g["judge_key"]]["mtd_bonus"]

    if score >= 0.75:
        g["outcome"] = {
            "title": "Motion to Dismiss 获准",
            "kind": "最佳结局",
            "text": "你凑齐了足够漂亮的牌型。法院认为个人管辖权存在明显问题，案件被驳回。",
            "score": 95,
        }
        push_history(
            "你提交了 Motion to Dismiss",
            "这一次你不是蒙对，而是真的凑齐了关键事实、证据和法官倾向。动议获准。"
        )
    elif score >= 0.55:
        g["outcome"] = {
            "title": "动议部分成功",
            "kind": "较好结局",
            "text": "法院没有完全照你的路走，但明显接受了你的一部分逻辑，原告压力增大，案件大概率转向较低成本和解或异地重诉。",
            "score": 82,
        }
        push_history(
            "你提交了 Motion to Dismiss",
            "法院没有完全站在你这边，但也没有给原告一张完整好牌。你逼出了对方的退让空间。"
        )
    else:
        g["risk"] = min(100, g["risk"] + 18)
        push_history(
            "你提交了 Motion to Dismiss",
            "这张程序牌打得太早，或者基础还不够。法院暂时不买账，风险明显上升。"
        )
        end_round_base_pressure()

# -----------------------------
# UI
# -----------------------------
st.title("⚖️ 美国诉讼模拟 Demo")
st.caption("纯文字类策略游戏原型。你的目标不是背法条，而是在不完全信息下凑出有利牌型。")

with st.expander("玩法说明", expanded=False):
    st.markdown(
        """
- 你扮演被告律师。
- 初始预算 **$5,000**，最多 **6 回合**。
- 调查会消耗金钱和时间，但能摸到关键事实牌。
- 动议不是越早越好，关键在于你手里牌型是否凑够。
- 法官风格和对手风格会改变局势，但你开局看不到全部底牌。
        """
    )

col_a, col_b = st.columns([1, 1])
with col_a:
    if st.button("开始新的一局", use_container_width=True):
        init_game()
with col_b:
    if st.button("重开同一局", use_container_width=True):
        old_seed = st.session_state.game["seed"] if "game" in st.session_state else None
        init_game(seed=old_seed)

if "game" not in st.session_state:
    init_game()

g = game()

# Sidebar
with st.sidebar:
    st.subheader("当前状态")
    st.metric("预算", f"${g['budget']:,}")
    st.metric("回合", f"{min(g['round'], MAX_ROUNDS)}/{MAX_ROUNDS}")
    st.metric("风险", f"{g['risk']}/100")
    st.progress(min(g["risk"], 100) / 100, text="风险条")
    st.caption(g["rng_seed_note"])

    st.markdown("### 已知事实")
    for k in g["facts_known"]:
        st.write(f"• {k}")

    if st.checkbox("显示隐藏设定（测试用）", value=False):
        st.markdown("### 隐藏设定")
        st.write(f"法官风格：{JUDGE_PROFILES[g['judge_key']]['name']}")
        st.write(f"对手风格：{OPPONENT_PROFILES[g['opponent_key']]['name']}")
        for k, v in g["facts_hidden"].items():
            st.write(f"• {k}: {'是' if v else '否'}")

# Intro card
st.markdown("---")
st.subheader("案件背景")
st.write(
    """
你的客户是一名中国卖家，刚刚在伊利诺伊州北区联邦法院被起诉。  
原告诉称其产品图片被侵权，并且已经申请了 TRO。  
你目前只知道几件事：

- 客户没有刻意向 Illinois 销售  
- 客户使用的是供应商提供的图片  
- 你不确定是否存在自然流入订单  
- 你也不确定原告是否做过测购
    """
)

judge = JUDGE_PROFILES[g["judge_key"]]
opp = OPPONENT_PROFILES[g["opponent_key"]]

st.markdown("### 桌面气氛")
st.write(f"法院气质偏向：**{judge['name']}**。{judge['description']}")
st.write(f"对手风格偏向：**{opp['name']}**。{opp['description']}")

# Outcome
if g["outcome"] is not None:
    st.markdown("---")
    st.subheader("本局结果")
    kind = g["outcome"]["kind"]
    score = g["outcome"]["score"]
    if kind in ["最佳结局", "较好结局"]:
        st.success(f"{g['outcome']['title']}｜{kind}｜评分 {score}")
    elif kind == "中等结局":
        st.warning(f"{g['outcome']['title']}｜{kind}｜评分 {score}")
    else:
        st.error(f"{g['outcome']['title']}｜{kind}｜评分 {score}")
    st.write(g["outcome"]["text"])

    st.markdown("### 你本局摸到的牌")
    for k in g["facts_known"]:
        if k.startswith("发现："):
            st.write(f"• {k}")

    st.markdown("### 操作记录")
    for item in g["history"]:
        with st.expander(item["title"], expanded=False):
            st.write(item["body"])

    st.info("你可以点击左上方按钮开始新的一局，或者重开同一局。")
else:
    st.markdown("---")
    st.subheader(f"第 {g['round']} 回合：请选择你的动作")

    action_order = [
        "invest_sales",
        "invest_test_buy",
        "invest_fabrication",
        "file_mtd",
        "negotiate",
        "wait",
    ]

    for action_key in action_order:
        action = ACTIONS[action_key]
        disabled = not can_afford(action_key)
        card = st.container(border=True)
        with card:
            st.markdown(f"**{action['label']}**")
            st.write(action["desc"])
            st.caption(f"成本：${action['cost']:,}｜耗时：{action['time']} 回合")
            if st.button(
                f"选择：{action['label']}",
                key=f"btn_{action_key}",
                use_container_width=True,
                disabled=disabled,
            ):
                if action_key == "invest_sales":
                    action_invest_sales()
                elif action_key == "invest_test_buy":
                    action_invest_test_buy()
                elif action_key == "invest_fabrication":
                    action_invest_fabrication()
                elif action_key == "file_mtd":
                    action_file_mtd()
                elif action_key == "negotiate":
                    action_negotiate()
                elif action_key == "wait":
                    action_wait()

                ending_check()
                st.rerun()

    st.markdown("### 已发生的剧情")
    if not g["history"]:
        st.write("还没有出牌。")
    else:
        for item in reversed(g["history"][-5:]):
            with st.expander(item["title"], expanded=True):
                st.write(item["body"])
