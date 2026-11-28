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

# Who to target first, and why
TARGET = {
    "Champions": ("Reward", "Protect these first. They bring the most money."),
    "Loyal": ("Grow", "Best chance to raise order value with bundles and points."),
    "At-risk": ("Win back", "Contact these soon, before they are lost for good."),
    "Occasional": ("Nurture", "Low cost to try: small offers can turn them into regulars."),
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
            "tag": TARGET[kind][0],
            "why": TARGET[kind][1],
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
    data = json.loads(text)
    for item in data:
        kind = _kind(item["segment"])
        item.setdefault("tag", TARGET[kind][0])
        item.setdefault("why", TARGET[kind][1])
    return data


def generate_insights(segments):
    if USE_AI:
        return ai_insights(segments)
    return rule_based_insights(segments)


# ---------------------------------------------------------------- message writer
MESSAGES = {
    "en": {
        "Champions": "Hi! Thank you for being one of our best customers at {shop}. As a thank you, you get early access to our new arrivals this week. Reply YES and we will keep your favourites ready.",
        "Loyal": "Hi! Thanks for shopping with {shop} again and again. Buy 2 items this week and get a special loyalty discount. See you soon!",
        "At-risk": "Hi! We miss you at {shop}. Here is 10% off your next order, valid this week only. Come back and see what is new!",
        "Occasional": "Hi! Welcome to {shop}. Here is a small gift: 5% off your next order. Our best sellers are waiting for you!",
    },
    "ta": {
        "Champions": "வணக்கம்! {shop} கடையின் சிறந்த வாடிக்கையாளர்களில் ஒருவராக இருப்பதற்கு நன்றி. இந்த வாரம் எங்கள் புதிய பொருட்களை முதலில் பார்க்கும் வாய்ப்பு உங்களுக்கு. 'ஆம்' என்று பதிலளியுங்கள், உங்களுக்குப் பிடித்தவற்றை ஒதுக்கி வைக்கிறோம்.",
        "Loyal": "வணக்கம்! {shop} கடையில் தொடர்ந்து வாங்குவதற்கு நன்றி. இந்த வாரம் 2 பொருட்கள் வாங்கினால் சிறப்பு தள்ளுபடி கிடைக்கும். விரைவில் சந்திப்போம்!",
        "At-risk": "வணக்கம்! {shop} கடையில் உங்களைத் தவறவிடுகிறோம். அடுத்த ஆர்டருக்கு 10% தள்ளுபடி, இந்த வாரம் மட்டும். வந்து புதியவற்றைப் பாருங்கள்!",
        "Occasional": "வணக்கம்! {shop} கடைக்கு வரவேற்கிறோம். சிறிய பரிசாக அடுத்த ஆர்டருக்கு 5% தள்ளுபடி. எங்கள் அதிகம் விற்கும் பொருட்கள் உங்களுக்காகக் காத்திருக்கின்றன!",
    },
}


def messages_for(segments, lang="en"):
    """One ready-to-send message per customer group. {shop} is filled in by the page."""
    book = MESSAGES["ta" if lang == "ta" else "en"]
    return [{"segment": s["Segment"], "text": book[_kind(s["Segment"])]} for s in segments]
