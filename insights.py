import json

# Set to True later if you add API credits
USE_AI = False
MODEL = "claude-sonnet-5-5"

PLAYBOOK = {
    "Champions": [
        "Launch a VIP or early-access program with exclusive offers.",
        "Ask for reviews and referrals, and reward them with points or gifts.",
        "Cross-sell premium or new products, but avoid heavy discounts.",
    ],
    "Loyal": [
        "Offer a points-based loyalty program to increase order value.",
        "Send personalised product recommendations based on past orders.",
        "Offer bundle deals to move them toward Champion spend levels.",
    ],
    "At-risk": [
        "Send a win-back email with a time-limited discount.",
        "Run a short survey asking why they stopped buying.",
        "Retarget them with ads showing products they bought before.",
    ],
    "Occasional": [
        "Send a welcome series that introduces best-selling products.",
        "Offer a small incentive on the next order to build the habit.",
        "Use reminders and seasonal campaigns to bring them back.",
    ],
}


def _kind(name):
    for key in PLAYBOOK:
        if name.startswith(key):
            return key
    return "Occasional"


def rule_based_insights(segments):
    out = []
    for s in segments:
        kind = _kind(s["Segment"])
        summary = (
            f"This segment has {int(s['Customers']):,} customers "
            f"({float(s['Share'])}% of the base). They last bought about "
            f"{float(s['Recency']):.0f} days ago, place around "
            f"{float(s['Frequency']):.1f} orders and spend about "
            f"{float(s['Monetary']):,.0f} on average."
        )
        out.append({
            "segment": s["Segment"],
            "summary": summary,
            "actions": PLAYBOOK[kind],
        })
    return out


def ai_insights(segments):
    from anthropic import Anthropic
    client = Anthropic()
    summary = [
        {
            "segment": s["Segment"],
            "customers": int(s["Customers"]),
            "share_percent": float(s["Share"]),
            "avg_days_since_last_purchase": float(s["Recency"]),
            "avg_orders": float(s["Frequency"]),
            "avg_total_spend": float(s["Monetary"]),
        }
        for s in segments
    ]
    prompt = (
        "You are a marketing analyst. Below are customer segments from an RFM "
        "analysis of a retail business.\n\n"
        f"{json.dumps(summary, indent=2)}\n\n"
        "For each segment, write a short explanation (2 sentences) of what these "
        "customers are like, and exactly 3 specific marketing actions.\n"
        "Reply with ONLY a JSON list, no other text and no code fences, in this form:\n"
        '[{"segment": "<exact segment name>", "summary": "...", '
        '"actions": ["...", "...", "..."]}]'
    )
    message = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


def generate_insights(segments):
    if USE_AI:
        return ai_insights(segments)
    return rule_based_insights(segments)