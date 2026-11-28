"""Tamil / English support.

Pages are written in English. When the visitor picks Tamil, the finished HTML
is passed through translate_html(), which swaps each English text for Tamil.
To fix a Tamil sentence or add a new one, edit the TA dictionary below.
"""
import html as _html
import re

MONTHS_TA = {"Jan": "ஜனவரி", "Feb": "பிப்ரவரி", "Mar": "மார்ச்", "Apr": "ஏப்ரல்",
             "May": "மே", "Jun": "ஜூன்", "Jul": "ஜூலை", "Aug": "ஆகஸ்ட்",
             "Sep": "செப்டம்பர்", "Oct": "அக்டோபர்", "Nov": "நவம்பர்", "Dec": "டிசம்பர்"}
DAYS_TA = {"Monday": "திங்கள்", "Tuesday": "செவ்வாய்", "Wednesday": "புதன்",
           "Thursday": "வியாழன்", "Friday": "வெள்ளி", "Saturday": "சனி", "Sunday": "ஞாயிறு",
           "Mon": "திங்", "Tue": "செவ்", "Wed": "புத", "Thu": "வியா", "Fri": "வெள்", "Sat": "சனி", "Sun": "ஞாயி"}

TA = {
    # navigation and common
    "Upload": "பதிவேற்று", "My analyses": "என் பகுப்பாய்வுகள்", "Log out": "வெளியேறு",
    "Log in": "உள்நுழை", "Register": "பதிவு செய்", "Email": "மின்னஞ்சல்",
    "Password": "கடவுச்சொல்", "Password (min 6 characters)": "கடவுச்சொல் (குறைந்தது 6 எழுத்துகள்)",
    "Upload a file": "கோப்பைப் பதிவேற்றுங்கள்", "Get started": "தொடங்குங்கள்",
    "Download (CSV)": "பதிவிறக்கு (CSV)", "Upload another file": "மற்றொரு கோப்பைப் பதிவேற்று",
    # home
    "Know your customers. Sell the right product at the right time.": "உங்கள் வாடிக்கையாளர்களை அறியுங்கள். சரியான பொருளை, சரியான நேரத்தில் விற்கவும்.",
    "Upload your sales file and get customer groups, fast and slow products, demand forecasts and the best time to sell.": "உங்கள் விற்பனை கோப்பைப் பதிவேற்றி வாடிக்கையாளர் குழுக்கள், வேகமாக மற்றும் மெதுவாக விற்கும் பொருட்கள், தேவை கணிப்பு, விற்க சிறந்த நேரம் ஆகியவற்றைப் பெறுங்கள்.",
    "Customers to target": "இலக்கு வைக்க வேண்டிய வாடிக்கையாளர்கள்",
    "See your Champions, Loyal, At-risk and Occasional buyers, and what to do for each.": "சிறந்த, விசுவாசமான, இழக்கும் அபாயமுள்ள, எப்போதாவது வாங்கும் வாடிக்கையாளர்களையும், ஒவ்வொருவருக்கும் செய்ய வேண்டியதையும் பாருங்கள்.",
    "Fast and slow products": "வேகமாக & மெதுவாக விற்கும் பொருட்கள்",
    "Find what sells quickly, what is stuck, and ideas to move it.": "எது வேகமாக விற்கிறது, எது தேங்கியுள்ளது, அதை விற்க யோசனைகள்.",
    "Demand and timing": "தேவை மற்றும் நேரம்",
    "See the best months, days and hours to sell, with a simple forecast.": "விற்க சிறந்த மாதங்கள், நாட்கள், மணிநேரங்கள் மற்றும் எளிய கணிப்பைப் பாருங்கள்.",
    "Who buys what": "யார் எதை வாங்குகிறார்கள்",
    "Estimate which products suit children, men, women or older people.": "குழந்தைகள், ஆண்கள், பெண்கள், முதியோருக்கு எந்தப் பொருட்கள் பொருந்தும் என மதிப்பிடுங்கள்.",
    # tabs
    "Fast & slow products": "வேகமாக & மெதுவாக விற்கும் பொருட்கள்",
    "Demand & best time": "தேவை & சிறந்த நேரம்",
    "Demand and best time": "தேவை மற்றும் சிறந்த நேரம்",
    # login / register
    "No account yet?": "கணக்கு இல்லையா?", "Create an account": "கணக்கை உருவாக்குங்கள்",
    "Already have an account?": "ஏற்கெனவே கணக்கு உள்ளதா?",
    "What is customer segmentation?": "வாடிக்கையாளர் பிரிவுப்படுத்தல் என்றால் என்ன?",
    "It means sorting your customers into groups that buy in a similar way, so you can talk to each group differently.": "ஒரே மாதிரி வாங்கும் வாடிக்கையாளர்களை குழுக்களாகப் பிரிப்பது. இதனால் ஒவ்வொரு குழுவிடமும் வெவ்வேறு விதமாகப் பேச முடியும்.",
    "How we group them": "எப்படிக் குழுப்படுத்துகிறோம்",
    "Recency:": "சமீபத்தில்:", "how long ago they last bought": "கடைசியாக எப்போது வாங்கினார்கள்",
    "Frequency:": "எத்தனை முறை:", "how often they buy": "எவ்வளவு அடிக்கடி வாங்குகிறார்கள்",
    "Money:": "பணம்:", "how much they spend": "எவ்வளவு செலவு செய்கிறார்கள்",
    "Why shops use it": "கடைகள் ஏன் பயன்படுத்துகின்றன",
    "Reward your best customers so they stay": "சிறந்த வாடிக்கையாளர்களுக்குப் பரிசளித்து அவர்களைத் தக்கவைக்க",
    "Win back customers who stopped buying": "வாங்குவதை நிறுத்தியவர்களை மீண்டும் கொண்டுவர",
    "Spend less on ads that do not work": "பலனில்லாத விளம்பரச் செலவைக் குறைக்க",
    "What you get here": "இங்கே உங்களுக்குக் கிடைப்பது",
    "Customer groups and who to target first": "வாடிக்கையாளர் குழுக்கள் மற்றும் முதலில் யாரை அணுகுவது",
    "Fast, slow and low-stock products": "வேகமாக, மெதுவாக விற்கும் மற்றும் இருப்பு குறைந்த பொருட்கள்",
    "Demand forecast and best selling time": "தேவை கணிப்பு மற்றும் விற்க சிறந்த நேரம்",
    # upload / history
    "Upload data": "தரவு பதிவேற்றம்",
    "Upload your sales file": "உங்கள் விற்பனை கோப்பைப் பதிவேற்றுங்கள்",
    "Choose a .csv or .xlsx file with one row per sale.": "ஒரு விற்பனைக்கு ஒரு வரிசை உள்ள .csv அல்லது .xlsx கோப்பைத் தேர்ந்தெடுக்கவும்.",
    "Needed:": "தேவை:",
    "quantity, unit price and date (for example Quantity, UnitPrice, InvoiceDate).": "அளவு, ஒரு பொருளின் விலை, தேதி (எ.கா. Quantity, UnitPrice, InvoiceDate).",
    "Better results with:": "இவை இருந்தால் சிறந்த முடிவு:",
    "CustomerID (customer groups), Description or StockCode (product analysis), InvoiceNo, Country, and a Stock column if you have one.": "CustomerID (வாடிக்கையாளர் குழுக்களுக்கு), Description அல்லது StockCode (பொருள் பகுப்பாய்வுக்கு), InvoiceNo, Country, மற்றும் இருப்பு (Stock) நெடுவரிசை இருந்தால் அதுவும்.",
    "Common names such as Qty, Price, OrderDate, SKU and Product are understood.": "Qty, Price, OrderDate, SKU, Product போன்ற பொதுவான பெயர்களும் புரிந்துகொள்ளப்படும்.",
    "Upload and analyse": "பதிவேற்றிப் பகுப்பாய்வு செய்",
    "File": "கோப்பு", "Uploaded (UTC)": "பதிவேற்றிய நேரம் (UTC)", "View results": "முடிவுகளைப் பார்",
    "No analyses yet. Upload a sales file to start.": "இன்னும் பகுப்பாய்வுகள் இல்லை. தொடங்க விற்பனை கோப்பைப் பதிவேற்றுங்கள்.",
    # flash messages
    "Please choose a file.": "கோப்பைத் தேர்ந்தெடுக்கவும்.",
    "Only .csv or .xlsx files are allowed.": ".csv அல்லது .xlsx கோப்புகள் மட்டுமே அனுமதிக்கப்படும்.",
    "Wrong email or password.": "மின்னஞ்சல் அல்லது கடவுச்சொல் தவறு.",
    "Please enter a valid email.": "சரியான மின்னஞ்சலை உள்ளிடவும்.",
    "Password must be at least 6 characters.": "கடவுச்சொல் குறைந்தது 6 எழுத்துகள் இருக்க வேண்டும்.",
    "That email is already registered. Please log in.": "இந்த மின்னஞ்சல் ஏற்கெனவே பதிவு செய்யப்பட்டுள்ளது. உள்நுழையவும்.",
    "You can only view your own analyses.": "உங்கள் சொந்த பகுப்பாய்வுகளை மட்டுமே பார்க்க முடியும்.",
    "File not found. Please upload again.": "கோப்பு கிடைக்கவில்லை. மீண்டும் பதிவேற்றவும்.",
    # results
    "Total sales": "மொத்த விற்பனை", "Orders": "ஆர்டர்கள்", "Average order value": "சராசரி ஆர்டர் மதிப்பு",
    "Customers": "வாடிக்கையாளர்கள்", "Products": "பொருட்கள்",
    "Who to target first": "முதலில் யாரை அணுக வேண்டும்",
    "Customers per group": "குழு வாரியாக வாடிக்கையாளர்கள்", "Group details": "குழு விவரங்கள்",
    "Group": "குழு", "Share %": "பங்கு %", "Last bought (days)": "கடைசி வாங்கல் (நாட்கள்)",
    "Avg. spend": "சராசரி செலவு", "Top 15 customers by spend": "அதிகம் செலவிட்ட 15 வாடிக்கையாளர்கள்",
    "Customer": "வாடிக்கையாளர்", "Spend": "செலவு",
    "Download all customers with groups (CSV)": "குழுக்களுடன் அனைத்து வாடிக்கையாளர்களையும் பதிவிறக்கு (CSV)",
    "Customer groups need a CustomerID column (with at least 10 customers). This file does not have one, so the other tabs still work.": "வாடிக்கையாளர் குழுக்களுக்கு CustomerID நெடுவரிசை (குறைந்தது 10 வாடிக்கையாளர்கள்) தேவை. இந்த கோப்பில் அது இல்லை; மற்ற தாவல்கள் வேலை செய்யும்.",
    "Top 10 products by sales": "விற்பனையில் முதல் 10 பொருட்கள்",
    "Sales by country / region": "நாடு / பகுதி வாரியான விற்பனை",
    "Reward": "பரிசளி", "Grow": "வளர்த்தெடு", "Win back": "மீட்டெடு", "Nurture": "பேணு",
    "Champions (high spend, recent)": "சிறந்தவர்கள் (அதிக செலவு, சமீபத்தில்)",
    "At-risk / Lost (haven't bought recently)": "இழக்கும் அபாயம் / இழந்தவர்கள் (சமீபத்தில் வாங்கவில்லை)",
    "Loyal customers": "விசுவாசமான வாடிக்கையாளர்கள்", "Occasional buyers": "எப்போதாவது வாங்குபவர்கள்",
    "Protect these first. They bring the most money.": "இவர்களை முதலில் பாதுகாக்கவும். இவர்கள்தான் அதிக வருமானம் தருகிறார்கள்.",
    "Best chance to raise order value with bundles and points.": "தொகுப்புச் சலுகைகள், புள்ளிகள் மூலம் ஆர்டர் மதிப்பை உயர்த்த சிறந்த வாய்ப்பு.",
    "Contact these soon, before they are lost for good.": "முழுவதுமாக இழக்கும் முன் விரைவில் இவர்களைத் தொடர்புகொள்ளுங்கள்.",
    "Low cost to try: small offers can turn them into regulars.": "குறைந்த செலவில் முயற்சிக்கலாம்: சிறு சலுகைகள் இவர்களை நிரந்தர வாடிக்கையாளர்களாக்கும்.",
    "Launch a VIP or early-access program with exclusive offers.": "பிரத்யேக சலுகைகளுடன் VIP அல்லது முன்கூட்டிய அணுகல் திட்டத்தைத் தொடங்குங்கள்.",
    "Ask for reviews and referrals, and reward them with points or gifts.": "மதிப்புரைகள், பரிந்துரைகளைக் கேளுங்கள்; புள்ளிகள் அல்லது பரிசுகளால் வெகுமதி அளியுங்கள்.",
    "Cross-sell premium or new products, but avoid heavy discounts.": "உயர்தர அல்லது புதிய பொருட்களை அறிமுகப்படுத்துங்கள்; பெரிய தள்ளுபடிகளைத் தவிர்க்கவும்.",
    "Offer a points-based loyalty program to increase order value.": "ஆர்டர் மதிப்பை உயர்த்த புள்ளிகள் அடிப்படையிலான விசுவாசத் திட்டம் வழங்குங்கள்.",
    "Send personalised product recommendations based on past orders.": "முந்தைய ஆர்டர்களின் அடிப்படையில் தனிப்பட்ட பொருள் பரிந்துரைகளை அனுப்புங்கள்.",
    "Offer bundle deals to move them toward Champion spend levels.": "சிறந்த வாடிக்கையாளர் அளவுக்கு உயர்த்த தொகுப்புச் சலுகைகள் வழங்குங்கள்.",
    "Send a win-back email with a time-limited discount.": "குறிப்பிட்ட காலத் தள்ளுபடியுடன் மீண்டும் வர அழைக்கும் மின்னஞ்சல் அனுப்புங்கள்.",
    "Run a short survey asking why they stopped buying.": "ஏன் வாங்குவதை நிறுத்தினார்கள் எனக் கேட்கும் சிறு கருத்துக்கணிப்பு நடத்துங்கள்.",
    "Retarget them with ads showing products they bought before.": "அவர்கள் முன்பு வாங்கிய பொருட்களைக் காட்டும் விளம்பரங்களை மீண்டும் காட்டுங்கள்.",
    "Send a welcome series that introduces best-selling products.": "அதிகம் விற்கும் பொருட்களை அறிமுகப்படுத்தும் வரவேற்புச் செய்திகளை அனுப்புங்கள்.",
    "Offer a small incentive on the next order to build the habit.": "பழக்கத்தை உருவாக்க அடுத்த ஆர்டருக்கு சிறு சலுகை வழங்குங்கள்.",
    "Use reminders and seasonal campaigns to bring them back.": "நினைவூட்டல்கள், பருவகால விளம்பரங்கள் மூலம் அவர்களை மீண்டும் வரவழையுங்கள்.",
    # health + messages
    "Business health score": "வணிக ஆரோக்கிய மதிப்பெண்", "out of 100": "100-க்கு",
    "This week's action list": "இந்த வார செயல் பட்டியல்",
    "Demand": "தேவை", "Healthy": "நல்ல நிலை", "Okay": "சராசரி", "Needs attention": "கவனம் தேவை",
    "Message writer": "செய்தி எழுதுபவர்",
    "Ready-to-send WhatsApp or SMS messages for each customer group. Type your shop name and the messages update.": "ஒவ்வொரு வாடிக்கையாளர் குழுவுக்கும் அனுப்பத் தயாரான WhatsApp அல்லது SMS செய்திகள். உங்கள் கடை பெயரை உள்ளிடுங்கள், செய்திகள் மாறும்.",
    "Your shop name": "உங்கள் கடை பெயர்", "Copy": "நகலெடு", "Open WhatsApp": "WhatsApp-ஐத் திற",
    "Check each message before sending. Only message customers who agreed to hear from you.": "அனுப்பும் முன் ஒவ்வொரு செய்தியையும் சரிபார்க்கவும். உங்களிடமிருந்து செய்தி பெற ஒப்புக்கொண்டவர்களுக்கு மட்டும் அனுப்புங்கள்.",
    "Copied!": "நகலெடுக்கப்பட்டது!", "our shop": "எங்கள் கடை",
    # products
    "Product analysis needs a Description or StockCode column. This file has neither.": "பொருள் பகுப்பாய்வுக்கு Description அல்லது StockCode நெடுவரிசை தேவை. இந்த கோப்பில் இரண்டுமில்லை.",
    "Product movement": "பொருள் நகர்வு", "How we decide": "எப்படி முடிவு செய்கிறோம்",
    "Fast": "வேகமாக", "Slow": "மெதுவாக", "Medium": "நடுத்தரம்",
    "Sells in the top quarter by units and has sold recently.": "அலகுகளில் முதல் கால்பங்கில் விற்பது, சமீபத்தில் விற்றது.",
    "Sells in the bottom quarter, or has had no sale for a long time.": "கடைசி கால்பங்கில் விற்பது அல்லது நீண்ட காலமாக விற்பனை இல்லாதது.",
    "Everything in between.": "மற்ற அனைத்தும்.",
    "This uses sales history only. It is a guide, not a stock count.": "இது விற்பனை வரலாற்றை மட்டுமே பயன்படுத்துகிறது. இது வழிகாட்டி மட்டுமே, இருப்பு எண்ணிக்கை அல்ல.",
    "Low stock risk": "இருப்பு குறையும் அபாயம்",
    "Your file has a Stock column. These products may run out within 14 days at their usual sales speed.": "உங்கள் கோப்பில் Stock நெடுவரிசை உள்ளது. வழக்கமான விற்பனை வேகத்தில் இந்தப் பொருட்கள் 14 நாட்களுக்குள் தீர்ந்துவிடலாம்.",
    "Your file has no stock column, so we cannot see real stock. These fast products are selling faster than usual in the last 30 days, so check their stock.": "உங்கள் கோப்பில் இருப்பு நெடுவரிசை இல்லை, எனவே உண்மையான இருப்பைப் பார்க்க முடியாது. இந்த வேகமான பொருட்கள் கடந்த 30 நாட்களில் வழக்கத்தை விட வேகமாக விற்கின்றன; இருப்பைச் சரிபார்க்கவும்.",
    "Product": "பொருள்", "In stock": "இருப்பு", "Days of cover": "எத்தனை நாளுக்கு இருப்பு",
    "What to do": "செய்ய வேண்டியது", "No products look at risk right now.": "இப்போது அபாயத்தில் உள்ள பொருட்கள் இல்லை.",
    "Fast-moving products": "வேகமாக விற்கும் பொருட்கள்", "Units sold": "விற்ற அலகுகள்",
    "Sales": "விற்பனை", "Units / month": "அலகுகள் / மாதம்",
    "Keep these in stock, show them first, and do not discount them.": "இவற்றை இருப்பில் வையுங்கள், முதலில் காட்டுங்கள், தள்ளுபடி வேண்டாம்.",
    "Slow-moving products: why and what to try": "மெதுவாக விற்கும் பொருட்கள்: ஏன், என்ன செய்யலாம்",
    "Units": "அலகுகள்", "Days since last sale": "கடைசி விற்பனைக்குப் பின் நாட்கள்",
    "Likely issue": "சாத்தியமான சிக்கல்", "Idea to sell faster": "வேகமாக விற்க யோசனை",
    "No recent sales: it may be out of season or forgotten": "சமீபத்திய விற்பனை இல்லை: பருவம் முடிந்திருக்கலாம் அல்லது மறக்கப்பட்டிருக்கலாம்",
    "Priced higher than most of your products": "உங்கள் பெரும்பாலான பொருட்களை விட விலை அதிகம்",
    "Very few customers have bought it": "மிகக் குறைவான வாடிக்கையாளர்களே வாங்கியுள்ளனர்",
    "Sells mostly in one season": "பெரும்பாலும் ஒரே பருவத்தில் விற்கிறது",
    "Steady but low interest": "நிலையானது ஆனால் ஆர்வம் குறைவு",
    "Run a clearance sale, or bring it back onto the homepage / shelf front": "கிளியரன்ஸ் விற்பனை நடத்துங்கள் அல்லது முகப்பு பக்கம் / கடையின் முன்புறத்துக்குக் கொண்டுவாருங்கள்",
    "Try a limited-time discount or a 'buy 2, save more' offer": "குறிப்பிட்ட காலத் தள்ளுபடி அல்லது '2 வாங்கினால் அதிகம் சேமிக்கலாம்' சலுகையை முயற்சிக்கவும்",
    "Bundle it with a fast-moving product so more people see it": "வேகமாக விற்கும் பொருளுடன் சேர்த்து விற்றால் அதிகமானோர் பார்ப்பார்கள்",
    "Keep stock low now and promote it before its peak months": "இப்போது இருப்பைக் குறைவாக வைத்து, உச்ச மாதங்களுக்கு முன் விளம்பரம் செய்யுங்கள்",
    "Improve its display or description and test a small discount": "காட்சியமைப்பு அல்லது விளக்கத்தை மேம்படுத்தி சிறு தள்ளுபடியைச் சோதிக்கவும்",
    # demand
    "Best months": "சிறந்த மாதங்கள்", "Best day": "சிறந்த நாள்", "Busiest hours": "அதிக பரபரப்பான மணிநேரங்கள்",
    "Sales by month": "மாத வாரியான விற்பனை",
    "Forecasting needs at least 3 months of data.": "கணிப்புக்கு குறைந்தது 3 மாத தரவு தேவை.",
    "The forecast is a simple estimate from recent months. It does not know about holidays or promotions.": "கணிப்பு சமீபத்திய மாதங்களின் எளிய மதிப்பீடு. விடுமுறை நாட்கள் அல்லது விளம்பரங்கள் இதற்குத் தெரியாது.",
    "Sales by weekday": "கிழமை வாரியான விற்பனை", "Sales by hour": "மணி வாரியான விற்பனை",
    "Sales by month of year": "ஆண்டின் மாதம் வாரியான விற்பனை",
    "Your dates have no time of day, so hourly timing is not available.": "உங்கள் தேதிகளில் நேரம் இல்லை, எனவே மணி வாரியான நேரம் கிடைக்காது.",
    "Top products: next month and best time to sell": "முதன்மைப் பொருட்கள்: அடுத்த மாதமும் விற்க சிறந்த நேரமும்",
    "Expected units next month": "அடுத்த மாதம் எதிர்பார்க்கும் அலகுகள்", "Trend": "போக்கு", "Peak months": "உச்ச மாதங்கள்",
    "Rising": "உயர்கிறது", "Falling": "குறைகிறது", "Steady": "நிலையானது",
    "Stock up and advertise a few weeks before the peak months.": "உச்ச மாதங்களுக்கு சில வாரங்கள் முன்பே இருப்பு வைத்து விளம்பரம் செய்யுங்கள்.",
    # audience
    "This needs a Description or StockCode column. This file has neither.": "இதற்கு Description அல்லது StockCode நெடுவரிசை தேவை. இந்த கோப்பில் இரண்டுமில்லை.",
    "This is an estimate.": "இது ஒரு மதிப்பீடு.",
    "Your file has no age or gender. We guess the group from words in the product name (for example \"kids\", \"baby\", \"ladies\"). Products that match nothing go to \"General / both\".": "உங்கள் கோப்பில் வயது அல்லது பாலினம் இல்லை. பொருளின் பெயரில் உள்ள சொற்களை (எ.கா. \"kids\", \"baby\", \"ladies\") வைத்து குழுவை ஊகிக்கிறோம். எதிலும் பொருந்தாத பொருட்கள் \"பொதுவானது / இருவருக்கும்\" குழுவுக்குச் செல்லும்.",
    "Share of sales": "விற்பனைப் பங்கு", "Summary": "சுருக்கம்",
    "Children": "குழந்தைகள்", "Men": "ஆண்கள்", "Women": "பெண்கள்", "Elderly": "முதியோர்",
    "General / both": "பொதுவானது / இருவருக்கும்",
}
TA.update(MONTHS_TA)
TA.update(DAYS_TA)


# ---------------------------------------------------------------- four-option pages
TA.update({
    "Home": "முகப்பு", "Report": "அறிக்கை",
    "Know your data. Grow your business.": "உங்கள் தரவை அறியுங்கள். உங்கள் வணிகத்தை வளர்த்தெடுங்கள்.",
    "Pick what you need. Each option gives you a clear report in plain words, in English or Tamil.": "தேவையானதைத் தேர்ந்தெடுங்கள். ஒவ்வொன்றும் எளிய சொற்களில் தெளிவான அறிக்கையை ஆங்கிலம் அல்லது தமிழில் தரும்.",
    "Any-file report": "எந்தக் கோப்பிற்குமான அறிக்கை",
    "Upload any CSV or Excel file (sales, marks, attendance, anything) and get a report on what your data says.": "எந்த CSV அல்லது Excel கோப்பையும் (விற்பனை, மதிப்பெண், வருகைப்பதிவு, எதுவானாலும்) பதிவேற்றி, உங்கள் தரவு என்ன சொல்கிறது என்ற அறிக்கையைப் பெறுங்கள்.",
    "Open": "திற",
    "Valuable customers": "மதிப்புமிக்க வாடிக்கையாளர்கள்",
    "Find your best customers, who is about to leave, and whom to target first. Needs a sales file with a customer ID.": "உங்கள் சிறந்த வாடிக்கையாளர்கள், யார் விலகப்போகிறார்கள், முதலில் யாரை அணுக வேண்டும் என்பதைக் கண்டறியுங்கள். வாடிக்கையாளர் எண் உள்ள விற்பனை கோப்பு தேவை.",
    "Stock check": "இருப்புச் சோதனை",
    "See what is out of stock, running low, overstocked or not selling, and how much to order.": "எது தீர்ந்துவிட்டது, குறைகிறது, அதிகமாக உள்ளது, விற்பனையாகவில்லை, எவ்வளவு ஆர்டர் செய்ய வேண்டும் என்பதைப் பாருங்கள்.",
    "Grow my business": "என் வணிகத்தை வளர்க்க",
    "Tell us about your business and your goal. Get a practical plan to win more customers in your area.": "உங்கள் வணிகம் மற்றும் இலக்கைச் சொல்லுங்கள். உங்கள் பகுதியில் அதிக வாடிக்கையாளர்களைப் பெற நடைமுறைத் திட்டம் பெறுங்கள்.",
    "Upload any .csv or .xlsx file. It can be about anything: sales, marks, attendance, patients, expenses.": ".csv அல்லது .xlsx கோப்பைப் பதிவேற்றுங்கள். விற்பனை, மதிப்பெண், வருகை, நோயாளிகள், செலவுகள் என எதைப் பற்றியதாகவும் இருக்கலாம்.",
    "Upload your stock list or your sales file. We show what to reorder and what is stuck.": "உங்கள் இருப்புப் பட்டியல் அல்லது விற்பனை கோப்பைப் பதிவேற்றுங்கள். எதை மறுஆர்டர் செய்ய வேண்டும், எது தேங்கியுள்ளது எனக் காட்டுவோம்.",
    "Choose a file": "கோப்பைத் தேர்ந்தெடுக்கவும்",
    "The first row must be the column names. Nothing else is needed.": "முதல் வரிசை நெடுவரிசைப் பெயர்களாக இருக்க வேண்டும். வேறு எதுவும் தேவையில்லை.",
    "Needed: a product name column and a stock column (for example Product, Stock).": "தேவை: பொருள் பெயர் நெடுவரிசை மற்றும் இருப்பு நெடுவரிசை (எ.கா. Product, Stock).",
    "Better results with: Price, Reorder level, or a sales file with Date and Quantity.": "இவை இருந்தால் சிறந்த முடிவு: Price, Reorder level, அல்லது Date, Quantity உள்ள விற்பனை கோப்பு.",
    "Your data report": "உங்கள் தரவு அறிக்கை", "Rows": "வரிசைகள்", "Columns": "நெடுவரிசைகள்",
    "Data quality": "தரவுத் தரம்", "Main number": "முக்கிய எண்",
    "What your data says": "உங்கள் தரவு சொல்வது", "What to do next": "அடுத்து செய்ய வேண்டியது",
    "Change over time": "காலப்போக்கில் மாற்றம்", "How the numbers are spread": "எண்கள் எப்படிப் பரவியுள்ளன",
    "Every column": "ஒவ்வொரு நெடுவரிசையும்", "Column": "நெடுவரிசை", "Type": "வகை", "Missing": "விடுபட்டவை",
    "Unique values": "தனித்த மதிப்புகள்", "Details": "விவரங்கள்", "First rows of your file": "உங்கள் கோப்பின் முதல் வரிசைகள்",
    "Back to options": "விருப்பங்களுக்குத் திரும்பு",
    "Number": "எண்", "Category": "பிரிவு", "Date": "தேதி", "Text": "உரை", "ID / name": "அடையாளம் / பெயர்", "Empty": "காலி",
    "Your stock check": "உங்கள் இருப்புச் சோதனை", "Out of stock": "இருப்பு தீர்ந்தது", "Reorder soon": "விரைவில் மறுஆர்டர்",
    "Too much or not selling": "அதிகம் அல்லது விற்பனையாகாதவை", "Money in stock": "இருப்பில் உள்ள பணம்",
    "What your stock says": "உங்கள் இருப்பு சொல்வது", "What to do this week": "இந்த வாரம் செய்ய வேண்டியது",
    "Reorder now": "இப்போதே மறுஆர்டர்", "Low": "குறைவு", "Overstocked": "அதிக இருப்பு", "No sales": "விற்பனை இல்லை", "OK": "சரி",
    "Suggested order": "பரிந்துரைக்கும் ஆர்டர்", "Stock value": "இருப்பு மதிப்பு",
    "Where your money is stored": "உங்கள் பணம் எங்கே முடங்கியுள்ளது",
    "Tell us about your business. You get a practical plan to win more customers in your area. No file needed.": "உங்கள் வணிகத்தைப் பற்றிச் சொல்லுங்கள். உங்கள் பகுதியில் அதிக வாடிக்கையாளர்களைப் பெற நடைமுறைத் திட்டம் கிடைக்கும். கோப்பு தேவையில்லை.",
    "Your business name": "உங்கள் வணிகப் பெயர்", "What kind of business is it?": "இது எந்த வகை வணிகம்?",
    "What do you want most?": "நீங்கள் அதிகம் விரும்புவது என்ன?", "Your area or town": "உங்கள் பகுதி அல்லது ஊர்",
    "What problem are you facing? (optional)": "என்ன சிக்கலை எதிர்கொள்கிறீர்கள்? (விருப்பம்)",
    "For example: few customers, a competitor nearby, people say prices are high": "எ.கா.: வாடிக்கையாளர்கள் குறைவு, அருகில் போட்டியாளர், விலை அதிகம் என்கிறார்கள்",
    "Write in English or Tamil. We read it to add advice for your problem.": "ஆங்கிலம் அல்லது தமிழில் எழுதலாம். உங்கள் சிக்கலுக்கான ஆலோசனையைச் சேர்க்க அதைப் படிக்கிறோம்.",
    "Show my growth plan": "என் வளர்ச்சித் திட்டத்தைக் காட்டு",
    "Start with these three things this week": "இந்த வாரம் இந்த மூன்றையும் தொடங்குங்கள்",
    "Your 4-week plan": "உங்கள் 4 வார திட்டம்", "A message you can send on WhatsApp": "WhatsApp-இல் அனுப்பக்கூடிய செய்தி",
    "Track these every week": "இவற்றை வாரந்தோறும் கண்காணியுங்கள்",
    "The file is empty.": "கோப்பு காலியாக உள்ளது.",
    "Upload your file": "உங்கள் கோப்பைப் பதிவேற்றுங்கள்",
    "Upload any .csv or .xlsx file about anything. Sales files get customer and product analysis. Every other file gets a general report.": "எதைப் பற்றிய .csv அல்லது .xlsx கோப்பையும் பதிவேற்றலாம். விற்பனை கோப்புகளுக்கு வாடிக்கையாளர், பொருள் பகுப்பாய்வு கிடைக்கும். மற்ற கோப்புகளுக்கு பொதுவான அறிக்கை கிடைக்கும்.",
    "This is not a typical sales file, so here is a general report instead.": "இது வழக்கமான விற்பனை கோப்பு அல்ல, எனவே பொதுவான அறிக்கை காட்டப்படுகிறது.",
    "The file could not be read. Save it again as CSV or XLSX.": "கோப்பைப் படிக்க முடியவில்லை. CSV அல்லது XLSX ஆக மீண்டும் சேமியுங்கள்.",
})


def _num(s):
    return s


PATTERNS = [
    (re.compile(r"([\d,]+) sales rows analysed \((.+) to (.+)\)"),
     lambda m: f"{m[1]} விற்பனை வரிசைகள் பகுப்பாய்வு செய்யப்பட்டன ({m[2]} முதல் {m[3]} வரை)"),
    (re.compile(r"Your file is large, so only the first ([\d,]+) rows were used to keep the site fast\."),
     lambda m: f"உங்கள் கோப்பு பெரியது, எனவே தளம் வேகமாக இருக்க முதல் {m[1]} வரிசைகள் மட்டுமே பயன்படுத்தப்பட்டன."),
    (re.compile(r"CSV is faster than Excel\. Only the first ([\d,]+) rows are used, so the analysis stays quick\."),
     lambda m: f"CSV கோப்பு Excel-ஐ விட வேகமானது. பகுப்பாய்வு வேகமாக இருக்க முதல் {m[1]} வரிசைகள் மட்டுமே பயன்படுத்தப்படும்."),
    (re.compile(r"(\d+) customer groups found\. Start with the group tagged for your goal\."),
     lambda m: f"{m[1]} வாடிக்கையாளர் குழுக்கள் கிடைத்தன. உங்கள் இலக்குக்கான குறியுள்ள குழுவிலிருந்து தொடங்குங்கள்."),
    (re.compile(r"This segment has ([\d,]+) customers \(([\d.]+)% of the base\)\. They last bought about (\d+) days ago, place around ([\d.]+) orders and spend about ([\d,]+) on average\."),
     lambda m: f"இந்தக் குழுவில் {m[1]} வாடிக்கையாளர்கள் ({m[2]}%) உள்ளனர். அவர்கள் சுமார் {m[3]} நாட்களுக்கு முன் கடைசியாக வாங்கினர்; சராசரியாக {m[4]} ஆர்டர்கள் செய்து சுமார் {m[5]} செலவிடுகின்றனர்."),
    (re.compile(r"([\d.]+)% of sales"), lambda m: f"விற்பனையில் {m[1]}%"),
    (re.compile(r"Expected units in (.+)"), lambda m: f"{m[1]} மாதத்தில் எதிர்பார்க்கும் அலகுகள்"),
    (re.compile(r"Sales in the last 30 days are ([\d.]+)x the usual rate\. Check stock and reorder early\."),
     lambda m: f"கடந்த 30 நாட்களில் விற்பனை வழக்கத்தை விட {m[1]} மடங்கு. இருப்பைச் சரிபார்த்து முன்கூட்டியே ஆர்டர் செய்யுங்கள்."),
    (re.compile(r"Reorder now: stock covers less than (\d+) days of sales"),
     lambda m: f"இப்போதே ஆர்டர் செய்யுங்கள்: இருப்பு {m[1]} நாட்களுக்கும் குறைவான விற்பனைக்கே போதும்"),
    (re.compile(r"Could not analyse this file: (.*)"),
     lambda m: f"இந்தக் கோப்பை பகுப்பாய்வு செய்ய முடியவில்லை: {m[1]}"),
]


def tr(text, lang="ta"):
    """Translate one string (used for chart labels and messages)."""
    if lang != "ta":
        return text
    return _lookup(" ".join(text.split())) or text


def _lookup(s):
    if s in TA:
        return TA[s]
    for rx, fn in PATTERNS:
        m = rx.fullmatch(s)
        if m:
            return fn(m)
    for sep in ("; ", ", "):
        if sep in s:
            parts = s.split(sep)
            out = [TA.get(p) for p in parts]
            if all(out):
                return sep.join(out)
    return None


_TEXT = re.compile(r">([^<>]+)<")
_PLACEHOLDER = re.compile(r'placeholder="([^"]*)"')
_SKIP = re.compile(r"(<script.*?</script>|<style.*?</style>)", re.S | re.I)


def _swap_text(m):
    raw = m.group(1)
    if not raw.strip():
        return m.group(0)
    new = _lookup(" ".join(_html.unescape(raw).split()))
    if new is None:
        return m.group(0)
    lead = raw[: len(raw) - len(raw.lstrip())]
    trail = raw[len(raw.rstrip()):]
    return ">" + lead + _html.escape(new, quote=False) + trail + "<"


def _swap_placeholder(m):
    new = _lookup(_html.unescape(m.group(1)))
    return m.group(0) if new is None else 'placeholder="' + _html.escape(new) + '"'


def translate_html(page):
    parts = _SKIP.split(page)
    for i, part in enumerate(parts):
        if i % 2 == 0:
            part = _TEXT.sub(_swap_text, part)
            parts[i] = _PLACEHOLDER.sub(_swap_placeholder, part)
    return "".join(parts)
