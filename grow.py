"""Option 4: grow my business.

The owner enters the business name, the kind of business, the goal and the area.
We return a practical plan of things to improve to get more customers.
Every idea is stored as (English, Tamil).
"""

TYPES = {
    "shop": ("Shop / retail (grocery, clothes, electronics)", "கடை / சில்லறை (மளிகை, துணி, மின்னணு)"),
    "food": ("Food (restaurant, tea shop, bakery)", "உணவு (உணவகம், தேநீர் கடை, பேக்கரி)"),
    "salon": ("Salon / beauty / fitness", "சலூன் / அழகு / உடற்பயிற்சி"),
    "clinic": ("Clinic / medical shop / lab", "கிளினிக் / மருந்துக்கடை / ஆய்வகம்"),
    "education": ("Tuition / coaching / school", "டியூஷன் / பயிற்சி மையம் / பள்ளி"),
    "service": ("Service (repair, tailoring, plumbing)", "சேவை (பழுது, தையல், பிளம்பிங்)"),
    "online": ("Online / home business", "ஆன்லைன் / வீட்டு வணிகம்"),
    "other": ("Something else", "வேறு ஏதாவது"),
}

GOALS = {
    "new": ("Get more new customers", "அதிக புதிய வாடிக்கையாளர்களைப் பெற"),
    "repeat": ("Make customers come back", "வாடிக்கையாளர்கள் மீண்டும் வர"),
    "bill": ("Increase what each customer spends", "ஒவ்வொரு வாடிக்கையாளரும் செலவிடுவதை உயர்த்த"),
}

COMMON = [
    ("Create a free Google Business Profile with your name, phone, timings, photos and a map pin. Most people now search \"near me\" before they visit.",
     "பெயர், தொலைபேசி, நேரம், புகைப்படங்கள், வரைபடக் குறியுடன் இலவச Google Business Profile உருவாக்குங்கள். பலர் செல்லும் முன் \"அருகில்\" என்று தேடுகிறார்கள்."),
    ("Set up WhatsApp Business with a catalogue, your timings and a quick-reply greeting. Put the number on your board, bills and bags.",
     "பட்டியல், நேரம், தானியங்கி வரவேற்புடன் WhatsApp Business அமையுங்கள். எண்ணை பலகை, பில், பையில் அச்சிடுங்கள்."),
    ("Make your signboard readable from 20 metres: big name, what you sell, phone number. Keep it clean and lit at night.",
     "20 மீட்டர் தூரத்திலிருந்தும் படிக்கும்படி பலகையை அமையுங்கள்: பெரிய பெயர், என்ன விற்கிறீர்கள், தொலைபேசி எண். இரவில் வெளிச்சம் இருக்கட்டும்."),
    ("Ask every happy customer for a Google review. Send them the review link on WhatsApp right after they buy. Aim for 5 new reviews a week.",
     "மகிழ்ச்சியான ஒவ்வொரு வாடிக்கையாளரிடமும் Google மதிப்புரை கேளுங்கள். வாங்கியவுடன் WhatsApp-இல் இணைப்பை அனுப்புங்கள். வாரம் 5 புதிய மதிப்புரைகள் இலக்கு."),
    ("Write down every customer's name and phone number (with permission). This list is your most valuable asset.",
     "ஒவ்வொரு வாடிக்கையாளரின் பெயர், தொலைபேசி எண்ணை (அனுமதியுடன்) எழுதிவையுங்கள். இந்தப் பட்டியல்தான் உங்கள் மிகப் பெரிய சொத்து."),
    ("Be clear about prices. A visible price list builds trust and saves staff time.",
     "விலையைத் தெளிவாகக் காட்டுங்கள். விலைப்பட்டியல் நம்பிக்கையை வளர்க்கும், ஊழியர் நேரத்தையும் மிச்சப்படுத்தும்."),
    ("Learn from complaints: ask 3 customers each week \"what should we improve?\" and fix the top answer.",
     "குறைகளிலிருந்து கற்றுக்கொள்ளுங்கள்: வாரம் 3 வாடிக்கையாளர்களிடம் \"எதை மேம்படுத்த வேண்டும்?\" என்று கேட்டு முதல் பதிலைச் சரிசெய்யுங்கள்."),
    ("Keep a simple weekly record: customers per day, sales per day, best product. What you measure improves.",
     "எளிய வாராந்திர பதிவு வையுங்கள்: நாளுக்கு எத்தனை வாடிக்கையாளர்கள், எவ்வளவு விற்பனை, சிறந்த பொருள். அளப்பது மேம்படும்."),
]

BY_TYPE = {
    "shop": [
        ("Put your fastest-selling items at the front and eye level, and keep them always in stock. Use this tool's Stock option to find what is running low.",
         "அதிகம் விற்கும் பொருட்களை முன்பகுதியில் கண் மட்டத்தில் வையுங்கள்; எப்போதும் இருப்பில் வையுங்கள். எது குறைகிறது என அறிய இந்தத் தளத்தின் இருப்பு விருப்பத்தைப் பயன்படுத்துங்கள்."),
        ("Create 2-3 combo packs (for example \"monthly grocery pack\") at a small saving. Customers love a ready choice.",
         "சிறிய சேமிப்புடன் 2-3 தொகுப்புகளை (எ.கா. \"மாதாந்திர மளிகைத் தொகுப்பு\") உருவாக்குங்கள். தயாரான தேர்வை வாடிக்கையாளர்கள் விரும்புவார்கள்."),
        ("Offer free home delivery for nearby streets above a minimum bill. Take orders on WhatsApp.",
         "குறைந்தபட்ச பில்லுக்கு மேல் அருகிலுள்ள தெருக்களுக்கு இலவச வீட்டு விநியோகம் வழங்குங்கள். ஆர்டர்களை WhatsApp-இல் பெறுங்கள்."),
        ("Run a clear weekly offer on slow-moving items so stock does not get stuck.",
         "தேங்கும் பொருட்களுக்கு வாராந்திர சலுகை வைத்து இருப்பு முடங்காமல் பார்த்துக்கொள்ளுங்கள்."),
    ],
    "food": [
        ("Take clear, bright photos of your top 5 dishes and put them on Google, WhatsApp status and Instagram.",
         "முதன்மையான 5 உணவுகளின் தெளிவான புகைப்படங்களை Google, WhatsApp status, Instagram-இல் பதிவிடுங்கள்."),
        ("Join Swiggy or Zomato, or take direct orders on WhatsApp with a delivery radius, to reach people who do not walk by.",
         "நடந்து வராதவர்களைச் சென்றடைய Swiggy அல்லது Zomato-வில் சேருங்கள்; அல்லது WhatsApp-இல் நேரடி ஆர்டர் எடுத்து விநியோக எல்லை நிர்ணயுங்கள்."),
        ("Create a combo meal and a quiet-hour offer (for example 3-5 pm) to fill empty time.",
         "காலி நேரத்தை நிரப்ப காம்போ உணவும் அமைதியான நேர (எ.கா. மாலை 3-5) சலுகையும் வையுங்கள்."),
        ("Keep taste and cleanliness the same every day. Display your food-safety licence.",
         "ருசியையும் சுத்தத்தையும் தினமும் ஒரே மாதிரி வையுங்கள். உணவுப் பாதுகாப்பு உரிமத்தைக் காட்சிப்படுத்துங்கள்."),
    ],
    "salon": [
        ("Take bookings on WhatsApp with fixed time slots so customers do not wait and you do not lose walk-aways.",
         "WhatsApp-இல் நேரம் குறித்து முன்பதிவு எடுங்கள்; வாடிக்கையாளர்கள் காத்திருக்க வேண்டாம், உங்களுக்கும் வாடிக்கையாளர் இழப்பு இல்லை."),
        ("Post before-and-after photos (with permission). Results sell better than words.",
         "(அனுமதியுடன்) முன்-பின் புகைப்படங்களைப் பதிவிடுங்கள். வார்த்தைகளை விட முடிவுகளே அதிகம் விற்கும்."),
        ("Sell packages (for example 5 visits for the price of 4) paid in advance.",
         "தொகுப்புகளை (எ.கா. 4 முறை கட்டணத்தில் 5 முறை) முன்பணத்துடன் விற்கவும்."),
        ("Give a small reward for bringing a friend, for both people.",
         "நண்பரை அழைத்து வந்தால் இருவருக்கும் சிறு வெகுமதி கொடுங்கள்."),
    ],
    "clinic": [
        ("Show doctor name, qualification, timings and services clearly on Google and at the entrance.",
         "மருத்துவர் பெயர், தகுதி, நேரம், சேவைகளை Google-இலும் நுழைவாயிலிலும் தெளிவாகக் காட்டுங்கள்."),
        ("Send appointment and follow-up reminders on WhatsApp. This brings patients back at the right time.",
         "நேரம் மற்றும் தொடர் சிகிச்சை நினைவூட்டல்களை WhatsApp-இல் அனுப்புங்கள். இது நோயாளிகளைச் சரியான நேரத்தில் மீண்டும் கொண்டுவரும்."),
        ("Run a free health camp or awareness talk in your area (BP, sugar check). It builds trust fast.",
         "உங்கள் பகுதியில் இலவச மருத்துவ முகாம் அல்லது விழிப்புணர்வு நடத்துங்கள் (BP, சர்க்கரை பரிசோதனை). நம்பிக்கை வேகமாக வளரும்."),
        ("Reduce waiting time with a token system and a clean, comfortable waiting area.",
         "டோக்கன் முறை, சுத்தமான வசதியான காத்திருப்பு இடம் மூலம் காத்திருப்பு நேரத்தைக் குறையுங்கள்."),
    ],
    "education": [
        ("Offer a free demo class and share short success stories of your students (with permission).",
         "இலவச டெமோ வகுப்பு வழங்குங்கள்; மாணவர்களின் வெற்றிக் கதைகளை (அனுமதியுடன்) பகிருங்கள்."),
        ("Send parents a monthly progress message on WhatsApp. Parents who see progress refer others.",
         "பெற்றோருக்கு மாதாந்திர முன்னேற்றச் செய்தியை WhatsApp-இல் அனுப்புங்கள். முன்னேற்றம் காணும் பெற்றோர் மற்றவர்களை அழைத்து வருவார்கள்."),
        ("Offer a sibling or friend discount and an early-admission offer before the new session.",
         "உடன்பிறப்பு அல்லது நண்பர் தள்ளுபடியும், புதிய பருவத்துக்கு முன் முன்கூட்டிய சேர்க்கைச் சலுகையும் வழங்குங்கள்."),
        ("Hold a free doubt-clearing session or test series to attract new students.",
         "புதிய மாணவர்களை ஈர்க்க இலவச சந்தேகம் தீர்க்கும் அமர்வு அல்லது தேர்வுத் தொடர் நடத்துங்கள்."),
    ],
    "service": [
        ("Give a clear price range and a time promise (for example \"ready in 2 days\"). Reliability wins repeat work.",
         "தெளிவான விலை வரம்பும் நேர வாக்குறுதியும் (எ.கா. \"2 நாளில் தயார்\") கொடுங்கள். நம்பகத்தன்மை மீண்டும் வேலை தரும்."),
        ("Photograph finished work and post it on Google and WhatsApp status.",
         "முடித்த வேலையைப் புகைப்படம் எடுத்து Google, WhatsApp status-இல் பதிவிடுங்கள்."),
        ("Give a short warranty on your work and print your number on a small sticker or card for every job.",
         "உங்கள் வேலைக்கு குறுகிய உத்தரவாதம் கொடுத்து, ஒவ்வொரு வேலையிலும் உங்கள் எண்ணுடன் சிறிய ஸ்டிக்கர் அல்லது அட்டை வையுங்கள்."),
        ("Ask for referrals right after a job is done, and reward them with a small discount.",
         "வேலை முடிந்தவுடனே பரிந்துரை கேளுங்கள்; அதற்கு சிறு தள்ளுபடி வெகுமதி கொடுங்கள்."),
    ],
    "online": [
        ("Show real photos and short videos of your products, and answer every message within one hour.",
         "பொருட்களின் உண்மையான புகைப்படங்களையும் சிறு வீடியோக்களையும் காட்டுங்கள்; ஒவ்வொரு செய்திக்கும் ஒரு மணி நேரத்துக்குள் பதில் அளியுங்கள்."),
        ("Post on Instagram and WhatsApp status 4 days a week. Use local language and local examples.",
         "வாரம் 4 நாட்கள் Instagram, WhatsApp status-இல் பதிவிடுங்கள். உள்ளூர் மொழியும் உள்ளூர் எடுத்துக்காட்டுகளும் பயன்படுத்துங்கள்."),
        ("Offer cash on delivery or easy returns for first-time buyers to remove fear.",
         "முதல் முறை வாங்குவோரின் அச்சத்தைப் போக்க கேஷ் ஆன் டெலிவரி அல்லது எளிய திரும்பப்பெறல் வழங்குங்கள்."),
        ("Start a small WhatsApp broadcast list for new arrivals and offers. Keep it to one message a week.",
         "புதிய வரவுகள், சலுகைகளுக்கான சிறிய WhatsApp ஒளிபரப்புப் பட்டியலைத் தொடங்குங்கள். வாரம் ஒரு செய்தி மட்டும்."),
    ],
    "other": [
        ("List the three reasons a customer should choose you over the next shop, and say them everywhere.",
         "அடுத்த கடையை விட உங்களை ஏன் தேர்ந்தெடுக்க வேண்டும் என்பதற்கான மூன்று காரணங்களை எழுதி எங்கும் சொல்லுங்கள்."),
        ("Find one thing nobody nearby offers (free delivery, late hours, home visit) and offer it.",
         "அருகில் யாரும் வழங்காத ஒன்றைக் (இலவச விநியோகம், தாமத நேரம், வீட்டுக்கே வருதல்) கண்டறிந்து வழங்குங்கள்."),
        ("Talk to ten past customers and ask why they chose you. Use their words in your advertising.",
         "முந்தைய பத்து வாடிக்கையாளர்களிடம் ஏன் உங்களைத் தேர்ந்தெடுத்தார்கள் எனக் கேளுங்கள். அவர்கள் சொற்களையே விளம்பரத்தில் பயன்படுத்துங்கள்."),
        ("Try one new low-cost promotion every two weeks and keep what works.",
         "இரண்டு வாரத்துக்கு ஒரு புதிய குறைந்த செலவு விளம்பரத்தை முயன்று, பலன் தருவதை வைத்துக்கொள்ளுங்கள்."),
    ],
}

BY_GOAL = {
    "new": [
        ("Offer a first-visit welcome gift or small discount, and put it on a flyer for homes and offices within 1-2 km.",
         "முதல் வருகைக்கு வரவேற்புப் பரிசு அல்லது சிறு தள்ளுபடி கொடுத்து, 1-2 கி.மீ. சுற்றளவில் வீடு, அலுவலகங்களுக்கு துண்டுப்பிரசுரம் கொடுங்கள்."),
        ("Ask your best customers to bring one friend. Give both a small reward.",
         "உங்கள் சிறந்த வாடிக்கையாளர்களிடம் ஒரு நண்பரை அழைத்து வரச் சொல்லுங்கள். இருவருக்கும் சிறு வெகுமதி கொடுங்கள்."),
        ("Join local WhatsApp groups (apartments, shops, parents) and share one useful offer. Do not spam.",
         "உள்ளூர் WhatsApp குழுக்களில் (அடுக்குமாடி, கடைகள், பெற்றோர்) சேர்ந்து ஒரு பயனுள்ள சலுகையைப் பகிருங்கள். தொந்தரவு செய்யாதீர்கள்."),
        ("Take part in a local festival, fair or school event with a small stall or sponsorship.",
         "உள்ளூர் திருவிழா, கண்காட்சி அல்லது பள்ளி நிகழ்வில் சிறு கடை அல்லது ஆதரவுடன் பங்கேற்குங்கள்."),
    ],
    "repeat": [
        ("Start a simple stamp card or points: every 5th visit gets a reward. Even a paper card works.",
         "எளிய முத்திரை அட்டை அல்லது புள்ளிகள் தொடங்குங்கள்: 5-வது வருகைக்கு வெகுமதி. காகித அட்டையும் போதும்."),
        ("Message customers who have not visited in 30 days with a small \"we miss you\" offer. The Customers option of this tool finds them for you.",
         "30 நாட்களாக வராதவர்களுக்கு \"உங்களை மிஸ் செய்கிறோம்\" என்ற சிறு சலுகைச் செய்தி அனுப்புங்கள். இந்தத் தளத்தின் வாடிக்கையாளர் விருப்பம் அவர்களைக் கண்டறிந்து தரும்."),
        ("Remember names and favourites, and greet regulars by name. People return to places where they feel known.",
         "பெயர்களையும் விருப்பங்களையும் நினைவில் வைத்து, நிரந்தர வாடிக்கையாளர்களைப் பெயர் சொல்லி வரவேற்குங்கள். தெரிந்தவராக உணரும் இடத்துக்கே மக்கள் திரும்புவார்கள்."),
        ("Send a thank-you message after purchase and a festival greeting. It costs nothing.",
         "வாங்கிய பிறகு நன்றிச் செய்தியும் பண்டிகை வாழ்த்தும் அனுப்புங்கள். செலவே இல்லை."),
    ],
    "bill": [
        ("Train staff to suggest one add-on with every sale (\"would you like ... with this?\").",
         "ஒவ்வொரு விற்பனையிலும் ஒரு கூடுதல் பொருளைப் பரிந்துரைக்க ஊழியர்களுக்குப் பயிற்சி அளியுங்கள் (\"இதனுடன் ... வேண்டுமா?\")."),
        ("Offer combo or bundle deals priced a little above your average bill, so customers move up.",
         "சராசரி பில்லை விட சற்று மேல் விலையில் காம்போ அல்லது தொகுப்புச் சலுகைகள் வையுங்கள்; வாடிக்கையாளர்கள் உயர்ந்து வாங்குவார்கள்."),
        ("Give a free gift or discount when the bill crosses a set amount (for example above 500).",
         "பில் குறிப்பிட்ட தொகையைத் தாண்டினால் (எ.கா. 500-க்கு மேல்) இலவசப் பரிசு அல்லது தள்ளுபடி கொடுங்கள்."),
        ("Keep a premium option next to your regular one. Many people choose the better one.",
         "வழக்கமான பொருளின் அருகிலேயே ஒரு உயர்தர விருப்பத்தையும் வையுங்கள். பலர் சிறந்ததைத் தேர்ந்தெடுப்பார்கள்."),
    ],
}

# keyword -> idea, matched against the owner's own words (English or Tamil)
PROBLEMS = [
    (("compet", "pottiyi", "போட்டி", "another shop", "nearby shop"),
     ("Do not fight on price alone. Pick one thing you do better (speed, freshness, service, trust) and say it everywhere.",
      "விலையில் மட்டும் போட்டி வேண்டாம். நீங்கள் சிறப்பாகச் செய்யும் ஒன்றை (வேகம், புத்துணர்ச்சி, சேவை, நம்பிக்கை) தேர்ந்தெடுத்து எங்கும் சொல்லுங்கள்.")),
    (("price", "costly", "expensive", "விலை"),
     ("If customers say you are costly, show the value: quality, freshness, warranty. Add a small low-price starter item.",
      "விலை அதிகம் என்றால் மதிப்பைக் காட்டுங்கள்: தரம், புத்துணர்ச்சி, உத்தரவாதம். குறைந்த விலையில் சிறு தொடக்கப் பொருளையும் சேருங்கள்.")),
    (("unknown", "nobody know", "not known", "awareness", "new shop", "தெரிய"),
     ("Few people know you yet. Focus on a clear signboard, Google profile, and a launch offer for your first 100 customers.",
      "உங்களை இன்னும் சிலருக்கே தெரியும். தெளிவான பலகை, Google profile, முதல் 100 வாடிக்கையாளர்களுக்கு அறிமுகச் சலுகை மீது கவனம் செலுத்துங்கள்.")),
    (("empty", "few customer", "no customer", "footfall", "slow", "கூட்டம்", "வாடிக்கையாளர் குறைவு"),
     ("For a slow shop, pick your quietest two hours and run a daily offer only in those hours.",
      "கூட்டம் குறைவாக இருந்தால், மிகவும் அமைதியான இரண்டு மணி நேரத்தைத் தேர்ந்து அந்த நேரத்தில் மட்டும் தினசரிச் சலுகை வையுங்கள்.")),
    (("online", "instagram", "facebook", "internet", "ஆன்லைன்"),
     ("Start small online: Google profile, WhatsApp Business, and 3 posts a week. Do not try every app at once.",
      "ஆன்லைனில் சிறியதாகத் தொடங்குங்கள்: Google profile, WhatsApp Business, வாரம் 3 பதிவுகள். எல்லா செயலிகளையும் ஒரே நேரத்தில் முயல வேண்டாம்.")),
    (("staff", "worker", "employee", "ஊழியர்"),
     ("Train staff on greeting, product knowledge and one add-on suggestion. Good service is the cheapest marketing.",
      "வரவேற்பு, பொருள் அறிவு, ஒரு கூடுதல் பொருள் பரிந்துரை பற்றி ஊழியர்களுக்குப் பயிற்சி அளியுங்கள். நல்ல சேவையே மிகக் குறைந்த செலவு விளம்பரம்.")),
]

WEEK = [
    ("Week 1: set up", "வாரம் 1: அடித்தளம்",
     "Google Business Profile, WhatsApp Business, price list, signboard.",
     "Google Business Profile, WhatsApp Business, விலைப்பட்டியல், பலகை."),
    ("Week 2: collect", "வாரம் 2: சேகரிப்பு",
     "Start the customer list and ask for 5 reviews.",
     "வாடிக்கையாளர் பட்டியலைத் தொடங்கி 5 மதிப்புரைகள் கேளுங்கள்."),
    ("Week 3: offer", "வாரம் 3: சலுகை",
     "Launch one offer for your goal and tell your list on WhatsApp.",
     "உங்கள் இலக்குக்கான ஒரு சலுகையைத் தொடங்கி WhatsApp-இல் பட்டியலுக்குத் தெரிவியுங்கள்."),
    ("Week 4: review", "வாரம் 4: மதிப்பாய்வு",
     "Compare customers and sales with week 1. Keep what worked, drop what did not.",
     "வாடிக்கையாளர்கள், விற்பனையை வாரம் 1-உடன் ஒப்பிடுங்கள். பலன் தந்ததை வைத்து, தராததை விடுங்கள்."),
]

MESSAGE = (
    "Hi! This is {name}{place}. Visit us this week and get a small welcome offer. Reply to this message for details. Thank you!",
    "வணக்கம்! இது {name}{place}. இந்த வாரம் எங்களைப் பார்க்க வாருங்கள், சிறிய வரவேற்புச் சலுகை உண்டு. விவரங்களுக்கு இந்தச் செய்திக்குப் பதில் அனுப்புங்கள். நன்றி!",
)


def advise(name, btype, goal, area="", problem="", lang="en"):
    i = 1 if lang == "ta" else 0
    btype = btype if btype in TYPES else "other"
    goal = goal if goal in GOALS else "new"
    name = (name or "").strip() or ("உங்கள் வணிகம்" if i else "Your business")
    area = (area or "").strip()
    text = (problem or "").lower()

    wanted = [idea[i] for kw, idea in PROBLEMS if any(k in text for k in kw)]
    sections = [
        {"title": ["Your goal first", "முதலில் உங்கள் இலக்கு"][i], "ideas": [x[i] for x in BY_GOAL[goal]]},
        {"title": ["For your kind of business", "உங்கள் வணிக வகைக்கு"][i], "ideas": [x[i] for x in BY_TYPE[btype]]},
    ]
    if wanted:
        sections.insert(0, {"title": ["About the problem you mentioned", "நீங்கள் குறிப்பிட்ட சிக்கலுக்கு"][i], "ideas": wanted})
    sections.append({"title": ["Basics every business needs", "ஒவ்வொரு வணிகத்துக்கும் தேவையான அடிப்படைகள்"][i],
                     "ideas": [x[i] for x in COMMON]})

    start = [sections[0]["ideas"][0], COMMON[0][i], COMMON[1][i]]
    place = (f" ({area})" if i else f", {area}") if area else ""
    message = MESSAGE[i].format(name=name, place=place)
    return {
        "name": name, "type_label": TYPES[btype][i], "goal_label": GOALS[goal][i], "area": area,
        "start": start, "sections": sections,
        "plan": [{"week": w[i], "todo": w[2 + i]} for w in WEEK],
        "message": message,
        "measure": [
            ["Customers per day", "நாளுக்கு வாடிக்கையாளர்கள்"][i],
            ["Sales per day", "நாளுக்கு விற்பனை"][i],
            ["Repeat customers each week", "வாரம் மீண்டும் வருவோர்"][i],
            ["New Google reviews", "புதிய Google மதிப்புரைகள்"][i],
        ],
    }
