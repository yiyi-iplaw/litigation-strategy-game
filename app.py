import random
import streamlit as st

st.set_page_config(page_title="美国诉讼模拟 Demo", page_icon="⚖️", layout="centered")

MAX_ROUNDS = 6
INITIAL_BUDGET = 5000

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
        "label": "观望一周",
        "cost": 0,
        "desc": "不花钱，但风险会继续累积。",
    },
}

DECISION_ACTIONS = {
    "file_mtd": {
        "label": "提交 Motion to Dismiss",
        "cost": 2000,
        "desc": "终局动作。点击后立即结算。",
    },
    "negotiate": {
        "label": "发起正式和解",
        "cost": 500,
        "desc": "终局动作。点击后立即结算。",
    },
    "fight_tro": {
        "label": "对抗 TRO / 初步禁令",
        "cost": 2500,
        "desc": "终局动作。点击后立即结算。",
    },
}

JUDGE_PROFILES = {
    "strict_procedure": {"mtd": 0.15, "settle": 0.0, "inj": -0.05},
    "rights_holder": {"mtd": -0.1, "settle": 0.1, "inj": 0.12},
    "efficiency": {"mtd": 0.05, "settle": 0.12, "inj": 0.0},
}

def init_game():
    st.session_state.g = {
        "round": 1,
        "budget": INITIAL_BUDGET,
        "risk": 35,
        "judge": random.choice(list(JUDGE_PROFILES.keys())),
        "facts": {},
        "hidden": {
            "sales": random.random() < 0.35,
            "test": random.random() < 0.45,
            "fake": random.random() < 0.25,
        },
        "history": [],
        "outcome": None
    }

def g():
    return st.session_state.g

def log(t, c):
    g()["history"].append((t, c))

def spend(x):
    g()["budget"] -= x

def next_round(risk=5):
    g()["risk"] = min(100, g()["risk"] + risk)
    g()["round"] += 1
    if g()["round"] > MAX_ROUNDS and not g()["outcome"]:
        g()["outcome"] = ("超时结局", "你没有在关键时刻做出决定，案件被动收场。", 50)

# --- 调查 ---
def invest_sales():
    spend(1500)
    if g()["hidden"]["sales"]:
        g()["facts"]["sales_bad"] = True
        log("调查销售", "发现存在 Illinois 订单（坏牌）")
    else:
        g()["facts"]["sales_good"] = True
        g()["risk"] -= 5
        log("调查销售", "未发现 Illinois 订单（好牌）")
    next_round()

def invest_test():
    spend(1500)
    if g()["hidden"]["test"]:
        g()["facts"]["test_bad"] = True
        log("调查测购", "原告已测购（坏）")
    else:
        g()["facts"]["test_good"] = True
        g()["risk"] -= 3
        log("调查测购", "未发现测购（好）")
    next_round()

def invest_fake():
    spend(2000)
    if g()["hidden"]["fake"]:
        g()["facts"]["fake_good"] = True
        g()["risk"] -= 10
        log("证据核查", "发现重大瑕疵（强牌）")
    else:
        log("证据核查", "未发现问题")
    next_round()

def wait():
    log("观望", "你没有行动，风险上升")
    next_round(10)

# --- 终局 ---
def decide_mtd():
    spend(2000)
    s = 0.4
    f = g()["facts"]
    j = JUDGE_PROFILES[g()["judge"]]

    if "sales_good" in f: s += 0.3
    if "sales_bad" in f: s -= 0.3
    if "test_good" in f: s += 0.2
    if "fake_good" in f: s += 0.15

    s += j["mtd"]

    if s > 0.7:
        g()["outcome"] = ("MTD成功", "案件被驳回", 95)
    elif s > 0.55:
        g()["outcome"] = ("部分成功", "局势明显好转", 80)
    else:
        g()["outcome"] = ("失败", "动议失败", 30)

def decide_settle():
    spend(500)
    s = 0.3
    f = g()["facts"]

    if "sales_good" in f: s += 0.2
    if "fake_good" in f: s += 0.2
    if g()["risk"] > 60: s += 0.1

    if s > 0.6:
        g()["outcome"] = ("低价和解", "很好", 80)
    elif s > 0.4:
        g()["outcome"] = ("中等和解", "一般", 60)
    else:
        g()["outcome"] = ("高价和解", "亏", 35)

def decide_fight():
    spend(2500)
    s = 0.35
    f = g()["facts"]

    if "fake_good" in f: s += 0.25
    if "test_good" in f: s += 0.1

    if s > 0.6:
        g()["outcome"] = ("抗住TRO", "不错", 80)
    elif s > 0.45:
        g()["outcome"] = ("部分成功", "一般", 60)
    else:
        g()["outcome"] = ("失败", "被压制", 25)

# --- UI ---
if "g" not in st.session_state:
    init_game()

st.title("⚖️ Litigation Game")

st.sidebar.write("预算", g()["budget"])
st.sidebar.write("回合", g()["round"])
st.sidebar.write("风险", g()["risk"])

if g()["outcome"]:
    st.success(f"{g()['outcome'][0]} | {g()['outcome'][2]}分")
    st.write(g()["outcome"][1])
else:
    st.subheader("调查阶段")
    if st.button("调查销售"): invest_sales()
    if st.button("调查测购"): invest_test()
    if st.button("查证据"): invest_fake()
    if st.button("观望"): wait()

    st.subheader("终局动作（点击即结算）")
    if st.button("MTD"): decide_mtd()
    if st.button("和解"): decide_settle()
    if st.button("打TRO"): decide_fight()

st.subheader("记录")
for t,c in g()["history"]:
    st.write(t, "-", c)
