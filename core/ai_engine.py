"""
AI NLP Engine for Bandez - Enquiry Classification, Chatbot, Pricing Estimator
Uses NLTK and rule-based pattern matching.
"""
import re
import math

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer

    # Download required NLTK data
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet', quiet=True)
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab', quiet=True)

    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


# ========================
# ENQUIRY CLASSIFICATION
# ========================

CATEGORY_KEYWORDS = {
    'booking_request': {
        'keywords': ['book', 'confirm', 'reserve', 'hire', 'schedule', 'booking', 'reserved', 'want to book',
                     'planning to book', 'need to book', 'would like to book', 'fix a date', 'finalize'],
        'weight': 3.0
    },
    'price_enquiry': {
        'keywords': ['price', 'cost', 'rate', 'fees', 'fee', 'how much', 'budget', 'quote', 'total amount',
                     'charges', 'amount', 'payment', 'pricing', 'expensive', 'affordable', 'charge'],
        'weight': 2.5
    },
    'availability_enquiry': {
        'keywords': ['available', 'availability', 'free on', 'check date', 'open on', 'are you free',
                     'free', 'slot', 'date available', 'booking date', 'when can', 'schedule open'],
        'weight': 2.5
    },
    'general_information': {
        'keywords': ['tell me about', 'what do you offer', 'info', 'details', 'services', 'genre', 'band members',
                     'information', 'about', 'music', 'style', 'performer', 'perform', 'kind of', 'type of'],
        'weight': 1.5
    },
    'complaint': {
        'keywords': ['complaint', 'problem', 'issue', 'refund', 'not satisfied', 'cancel', 'disappointed',
                     'unhappy', 'bad', 'terrible', 'horrible', 'worst', 'upset', 'angry', 'poor service',
                     'dissatisfied', 'not happy', 'fraud', 'cheated'],
        'weight': 4.0
    }
}


def preprocess_text(text):
    """Tokenize, lowercase, remove stopwords, lemmatize"""
    text = text.lower()
    # Remove punctuation except spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = text.split()

    if NLTK_AVAILABLE:
        try:
            stop_words = set(stopwords.words('english'))
            lemmatizer = WordNetLemmatizer()
            tokens = [lemmatizer.lemmatize(t) for t in tokens if t not in stop_words and len(t) > 2]
        except Exception:
            pass

    return tokens


def classify_enquiry(message):
    """
    NLP pipeline: tokenize → stopword removal → lemmatize → keyword match → confidence score
    Returns (category, confidence)
    """
    tokens = preprocess_text(message)
    text_lower = message.lower()

    scores = {}
    for category, config in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in config['keywords']:
            # Multi-word keyword phrases
            if ' ' in keyword:
                if keyword in text_lower:
                    score += config['weight'] * 2
            else:
                if keyword in tokens:
                    score += config['weight']

        scores[category] = score

    if not any(scores.values()):
        return 'general_information', 0.3

    best_category = max(scores, key=scores.get)
    total_score = sum(scores.values())
    confidence = scores[best_category] / total_score if total_score > 0 else 0

    # Minimum confidence threshold
    if confidence < 0.4:
        return 'general_information', confidence

    return best_category, round(confidence, 2)


def get_auto_response(category, enquiry=None):
    """Generate category-specific auto-response"""
    band_name = enquiry.band.band_name if enquiry else 'the band'
    event_type = enquiry.get_event_type_display() if enquiry else 'your event'
    event_date = enquiry.event_date if enquiry else 'your requested date'
    ref = enquiry.reference_number if enquiry else 'N/A'

    responses = {
        'booking_request': f"""Thank you for your booking request for {band_name}!

Your Enquiry Reference: {ref}

We have received your request for a {event_type} on {event_date}. Our band manager will review your enquiry and confirm availability within 24 hours.

You will receive a confirmation email once the booking is accepted.

Warm regards,
{band_name} via Bandez""",

        'price_enquiry': f"""Thank you for your pricing enquiry for {band_name}!

Your Enquiry Reference: {ref}

Please check our Service Packages section on the band profile for detailed pricing information. Pricing depends on the event type, duration, location, and selected package.

Use our AI Pricing Estimator on the profile page for an instant estimate. Our manager will provide a personalized quote within 24 hours.

Warm regards,
{band_name} via Bandez""",

        'availability_enquiry': f"""Thank you for checking {band_name}'s availability!

Your Enquiry Reference: {ref}

We have received your availability enquiry for {event_date}. Our team will confirm availability within 24 hours.

You can also check the live availability calendar on our profile page for real-time information.

Warm regards,
{band_name} via Bandez""",

        'general_information': f"""Thank you for your enquiry about {band_name}!

Your Enquiry Reference: {ref}

We have received your message and our band manager will provide detailed information within 24 hours.

In the meantime, feel free to browse our profile page to learn more about our music genres, event experience, and service packages.

Warm regards,
{band_name} via Bandez""",

        'complaint': f"""We sincerely apologize for your experience and take all feedback very seriously.

Your Enquiry Reference: {ref}

Your concern has been escalated to both the Band Manager and the Bandez Admin team. We will investigate and respond within 12 hours.

We are committed to making this right for you.

Sincerely,
The Bandez Support Team"""
    }
    return responses.get(category, responses['general_information'])


# ========================
# AI PRICING ESTIMATOR
# ========================

EVENT_TYPE_MULTIPLIERS = {
    'wedding': 1.3,
    'corporate': 1.2,
    'private': 1.1,
    'college': 1.0,
    'school': 0.9,
}

LOCATION_TIER_ADJUSTMENTS = {
    'metro': 0.15,
    'tier1': 0.10,
    'tier2': 0.0,
    'rural': -0.10,
}


def estimate_price(package=None, event_type='college', duration=3,
                   audience=100, location_tier='tier2', is_weekend=False, is_holiday=False,
                   base_min=15000, base_max=30000):
    """
    AI Pricing Estimator — rule-based weighted algorithm
    Returns (estimated_min, estimated_max)
    """
    if package:
        base_min = package.min_price
        base_max = package.max_price

    # Event type multiplier
    et_mult = EVENT_TYPE_MULTIPLIERS.get(event_type, 1.0)

    # Duration multiplier (base is 3 hours)
    duration_mult = duration / 3.0

    # Audience size factor
    audience_factor = 1.0
    if audience > 500:
        audience_factor = 1.25
    elif audience > 200:
        audience_factor = 1.15
    elif audience > 100:
        audience_factor = 1.05

    # Location tier adjustment
    loc_adj = 1 + LOCATION_TIER_ADJUSTMENTS.get(location_tier, 0)

    # Day type
    day_mult = 1.0
    if is_holiday:
        day_mult = 1.20
    elif is_weekend:
        day_mult = 1.10

    total_mult = et_mult * duration_mult * audience_factor * loc_adj * day_mult

    estimated_min = int(base_min * total_mult)
    estimated_max = int(base_max * total_mult)

    return estimated_min, estimated_max


# ========================
# CHATBOT NLP ENGINE
# ========================

CHATBOT_INTENTS = {
    'availability': ['available', 'free on', 'check date', 'available on', 'open on', 'free for'],
    'pricing': ['price', 'cost', 'rate', 'how much', 'fees', 'charge', 'quote'],
    'packages': ['packages', 'package', 'plan', 'offer', 'service', 'what do you have'],
    'booking_process': ['how to book', 'process', 'steps', 'how do i book', 'procedure', 'book a band'],
    'event_type': ['wedding', 'corporate', 'college', 'school', 'private', 'events', 'bands for'],
    'rating': ['rating', 'review', 'stars', 'rated', 'reviews', 'score'],
    'navigation': ['where', 'how to find', 'where is', 'how can i see', 'photos', 'gallery'],
    'greeting': ['hello', 'hi', 'hey', 'good morning', 'good evening', 'start', 'help'],
}


def detect_intent(message):
    """Detect chatbot intent from message"""
    text = message.lower()
    tokens = preprocess_text(message)

    for intent, keywords in CHATBOT_INTENTS.items():
        for keyword in keywords:
            if keyword in text or keyword in tokens:
                return intent
    return 'fallback'


def extract_band_name(message):
    """Try to extract band name from message using simple pattern"""
    # Look for patterns like "Is X available" or "what is the rating of X"
    patterns = [
        r'(?:is|about|for|of|does|do)\s+([A-Z][a-zA-Z\s&]+?)(?:\s+available|\'s|\s+have|\s+offer|\?|$)',
        r'([A-Z][a-zA-Z\s&]+?)\s+(?:band|bands)',
    ]
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            return match.group(1).strip()
    return None


def extract_date(message):
    """Simple date extraction from message"""
    patterns = [
        r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',
        r'\b(\d{4}-\d{2}-\d{2})\b',
        r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})\b',
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def generate_chatbot_response(message, user=None):
    """Main chatbot response generator"""
    from bands.models import BandProfile

    intent = detect_intent(message)
    band_name = extract_band_name(message)
    date_str = extract_date(message)

    band = None
    if band_name:
        try:
            band = BandProfile.objects.filter(
                band_name__icontains=band_name, is_active=True
            ).first()
        except Exception:
            band = None

    if intent == 'greeting':
        return "👋 Hello! Welcome to **Bandez**! I'm your AI assistant. I can help you with:\n\n• 📅 Checking band availability\n• 💰 Getting pricing information\n• 📦 Viewing service packages\n• ⭐ Band ratings and reviews\n• 🎵 Finding bands for your event\n• 📖 Step-by-step booking guide\n\nHow can I help you today?", 'greeting'

    elif intent == 'availability':
        if band and date_str:
            from bands.models import BandAvailability
            from bookings.models import Booking
            from django.utils import timezone
            try:
                from datetime import datetime
                check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                avail = BandAvailability.objects.filter(band=band, date=check_date).first()
                booked = Booking.objects.filter(band=band, event_date=check_date, status='confirmed').exists()
                if booked or (avail and avail.status in ['booked', 'blocked']):
                    return f"❌ **{band.band_name}** is **not available** on {date_str}. Please check their calendar for available dates or try the enquiry form for alternative date suggestions.", 'availability'
                else:
                    return f"✅ **{band.band_name}** is **available** on {date_str}! Click 'Send Enquiry' on their profile to book them.", 'availability'
            except Exception:
                return f"I found **{band.band_name}**! Please check their profile page for the live availability calendar to verify date availability.", 'availability'
        elif band:
            return f"Please visit **{band.band_name}'s** profile page to see the live availability calendar. Would you like me to help with anything else?", 'availability'
        else:
            return "To check availability, please visit the band's profile page and use the availability calendar! You can also use the enquiry form to check a specific date.", 'availability'

    elif intent == 'pricing':
        if band:
            packages = band.packages.filter(is_active=True)
            if packages.exists():
                pkg_list = '\n'.join([f"• **{p.name}**: ₹{p.min_price:,} – ₹{p.max_price:,} (for {p.duration_hours} hrs)" for p in packages])
                return f"💰 **{band.band_name}** Service Packages:\n\n{pkg_list}\n\nUse the **AI Pricing Estimator** on their profile for a personalized estimate based on your event details!", 'pricing'
            else:
                return f"**{band.band_name}** hasn't added specific package pricing yet. Please send an enquiry for a custom quote.", 'pricing'
        else:
            return "💰 Pricing varies by band, event type, duration, and location. Visit any band's profile to use the **AI Pricing Estimator** widget! Generally, prices range from ₹10,000 to ₹1,50,000+ depending on the band and event.", 'pricing'

    elif intent == 'packages':
        if band:
            packages = band.packages.filter(is_active=True)
            if packages.exists():
                pkg_list = '\n'.join([f"• **{p.name}**: {p.description[:80]}..." for p in packages])
                return f"📦 **{band.band_name}** offers these packages:\n\n{pkg_list}\n\nVisit their profile for full details!", 'packages'
            else:
                return f"**{band.band_name}** hasn't listed packages yet. Contact them via the enquiry form!", 'packages'
        else:
            return "Most bands on Bandez offer **Basic**, **Standard**, and **Premium** packages. Visit any band's profile to see their specific packages and pricing!", 'packages'

    elif intent == 'booking_process':
        return """📋 **How to Book a Band on Bandez:**

1. 🔍 **Explore** — Browse bands on the Explore page using filters
2. 👀 **View Profile** — Click any band card to see full details
3. 📅 **Check Availability** — Use the calendar or pick a date in the enquiry form
4. 💰 **Get Estimate** — Use the AI Pricing Estimator
5. 📝 **Send Enquiry** — Fill the enquiry form with your event details
6. ✉️ **Confirmation** — You'll get an email with your reference number
7. ✅ **Booking Confirmed** — The band manager will accept/reject within 24 hours
8. 🎵 **Enjoy Your Event!** — Then rate the band afterwards

Need any help with a specific step?""", 'booking_process'

    elif intent == 'event_type':
        from bands.models import BandProfile
        event_keywords = {'wedding': 'wedding', 'corporate': 'corporate', 'college': 'college', 'school': 'school', 'private': 'private'}
        detected_event = None
        msg_lower = message.lower()
        for key, val in event_keywords.items():
            if key in msg_lower:
                detected_event = val
                break

        if detected_event:
            bands = BandProfile.objects.filter(is_active=True, is_approved=True)
            matching = [b for b in bands if detected_event in (b.event_types or [])][:4]
            if matching:
                band_list = '\n'.join([f"• **{b.band_name}** — {b.base_location} | ⭐ {b.average_rating}" for b in matching])
                return f"🎵 **Bands for {detected_event.title()} Events:**\n\n{band_list}\n\nVisit the Explore page to see all available bands with filters!", 'event_type'
        return "🎵 Bandez has bands for **Weddings**, **Corporate Events**, **College Programs**, **School Events**, and **Private Functions**! Use the Explore page tabs to filter by event type.", 'event_type'

    elif intent == 'rating':
        if band:
            return f"⭐ **{band.band_name}** has an average rating of **{band.average_rating}★** based on {band.total_reviews} reviews. Visit their profile to read all reviews!", 'rating'
        else:
            return "You can see band ratings on their profile pages and on the Explore page. Use the **Min Rating** filter to find top-rated bands!", 'rating'

    elif intent == 'navigation':
        return """🧭 **Navigation Guide:**

• 📸 **Gallery** → Band Profile → scroll down to Gallery section
• 📅 **Availability** → Band Profile → Availability Calendar section  
• 📦 **Packages** → Band Profile → Service Packages section
• ⭐ **Reviews** → Band Profile → Reviews section
• 🔍 **Search Bands** → Explore page (top navigation)
• 📋 **My Enquiries** → Customer Dashboard
• 💬 **Chatbot** → Click the chat bubble (bottom-right corner)

Is there anything specific you're looking for?""", 'navigation'

    else:
        return "🤔 I'm not sure I understood that. Here's what I can help with:\n\n• **Check availability** of a band on a date\n• **Pricing** and package information\n• **How to book** a band\n• **Find bands** for your event type\n• **Band ratings** and reviews\n\nOr visit the [Explore page](/bands/explore/) to browse all bands! For further assistance, please [send an enquiry](/enquiries/) or email us at **support@bandez.com**.", 'fallback'
