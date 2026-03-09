# 🎵 Bandez — Band Booking Platform

> A full-featured Django web application for discovering, enquiring, and booking bands for events. Built with an AI-powered chatbot, NLP enquiry classification, Stripe payment integration, and a complete band management system.

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Tech Stack](#-tech-stack)
3. [Project Structure](#-project-structure)
4. [Installation & Setup](#-installation--setup)
5. [Configuration](#-configuration)
6. [Django Apps & Features](#-django-apps--features)
   - [Accounts App](#1-accounts-app)
   - [Bands App](#2-bands-app)
   - [Enquiries App](#3-enquiries-app)
   - [Bookings App](#4-bookings-app)
   - [Reviews App](#5-reviews-app)
   - [Chatbot App](#6-chatbot-app)
   - [Core App](#7-core-app)
7. [Database Models](#-database-models)
8. [URL Routes Reference](#-url-routes-reference)
9. [AI Engine (NLP)](#-ai-engine-nlp)
10. [Payment Integration (Stripe)](#-payment-integration-stripe)
11. [Admin Panel](#-admin-panel)
12. [Security Features](#-security-features)
13. [Running the Project](#-running-the-project)

---

## 🌐 Project Overview

**Bandez** is a platform that connects customers looking to hire bands for events (weddings, corporate events, college fests, etc.) with professional band managers. The platform supports:

- Customer and Band Manager registration with role-based access
- Band profile creation with photos, gallery, service packages, and availability calendar
- Enquiry submission with AI-powered auto-categorisation and auto-reply
- Booking management with Stripe online payment (full, advance, or offline)
- Customer ratings and reviews after completed bookings
- An AI chatbot assistant for navigating the platform
- A custom admin dashboard for platform management

---

## 🛠 Tech Stack

| Component      | Technology                          |
|---------------|--------------------------------------|
| Backend        | Django 4.x (Python)                 |
| Database       | SQLite (dev) / PostgreSQL (prod)    |
| Frontend       | Bootstrap 5, Crispy Forms           |
| Payments       | Stripe (Checkout Sessions)          |
| AI / NLP       | NLTK (tokenization, lemmatization)  |
| Email          | Django email (Console / SMTP)       |
| Media Storage  | Local filesystem (`/media/`)        |
| Static Files   | `/static/` directory                |

---

## 🗂 Project Structure

```
final project/
├── bandez/               # Django project settings & root URLs
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/             # User registration, auth, profile
├── bands/                # Band profiles, packages, gallery, availability
├── enquiries/            # Enquiry submission, messaging, manager review
├── bookings/             # Booking management, Stripe payments
├── reviews/              # Customer ratings & reviews
├── chatbot/              # AI chatbot (NLP-based)
├── core/                 # Home, dashboards, admin panel
├── templates/            # All HTML templates organised per app
├── static/               # CSS, JS, images
├── media/                # User-uploaded files (band photos, gallery)
├── manage.py
└── db.sqlite3
```

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.10+
- pip
- Git

### Step-by-Step Setup

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd "final project"

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 3. Install dependencies
pip install django
pip install pillow            # Image handling
pip install django-crispy-forms crispy-bootstrap5
pip install stripe            # Stripe payments
pip install nltk              # AI / NLP engine

# 4. Run database migrations
python manage.py migrate

# 5. Create a superuser (admin)
python manage.py createsuperuser

# 6. Collect static files (optional for development)
python manage.py collectstatic

# 7. Start the development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

---

## 🔧 Configuration

All settings are in `bandez/settings.py`.

### Key Settings

```python
# Timezone
TIME_ZONE = 'Asia/Kolkata'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Session expiry (30 minutes of inactivity)
SESSION_COOKIE_AGE = 1800

# Account lockout after failed logins
MAX_LOGIN_ATTEMPTS = 5    # lock after 5 failures
LOCKOUT_DURATION = 15     # locked for 15 minutes

# Gallery limits
MAX_GALLERY_IMAGES = 20
MAX_IMAGE_SIZE_MB = 5

# Stripe (set via .env file - never hardcode!)
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', '')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
```

### Email Configuration

Currently uses the **console backend** (emails print to terminal). To enable real email delivery:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

---

## 📦 Django Apps & Features

---

### 1. Accounts App

**Location:** `accounts/`

Handles all authentication, registration, and user management.

#### Features
- **Three user roles:** `customer`, `band_manager`, `admin`
- **Email-based login** (not username)
- **Email verification** via unique token link (24-hour validity)
- **OTP-based password reset** (6-digit code, 30-minute validity)
- **Account lockout** after 5 failed login attempts (15-minute lockout)
- **Session timeout** middleware (30 minutes of inactivity auto-logs out)
- **Profile update** and **account deletion**

#### Models

| Model | Description |
|-------|-------------|
| `User` | Custom user extending `AbstractUser`. Has `role`, `phone`, `email` (unique), `is_email_verified`, `failed_login_attempts`, `lockout_until` |
| `EmailVerificationToken` | One-time token for verifying a new account's email |
| `PasswordResetOTP` | 6-digit OTP for resetting forgotten passwords |

#### Key Views

| View | URL | Description |
|------|-----|-------------|
| `register_customer` | `/accounts/register/customer/` | Customer registration form |
| `register_band_manager` | `/accounts/register/band-manager/` | Band manager registration |
| `user_login` | `/accounts/login/` | Login with lockout protection |
| `user_logout` | `/accounts/logout/` | Logout and redirect to home |
| `password_reset_request` | `/accounts/password-reset/` | Enter email to receive OTP |
| `verify_otp` | `/accounts/verify-otp/` | Enter 6-digit OTP |
| `set_new_password` | `/accounts/set-new-password/` | Set a new password after OTP |
| `profile_view` | `/accounts/profile/` | View and update profile |
| `delete_account` | `/accounts/delete-account/` | Permanently delete account |

#### Middleware

`accounts/middleware.py` — `SessionTimeoutMiddleware`:
- Checks the time of the last request
- If more than 30 minutes have passed, logs out the user and sets a session message
- Applied globally via `MIDDLEWARE` in settings

#### Login Flow (with lockout)

```
User enters email + password
        ↓
User.is_locked_out() checked
        ↓ (not locked)
django authenticate()
        ↓ Success → login() → redirect by role
        ↓ Fail → increment failed_login_attempts
              → if >= 5: set lockout_until = now + 15min
```

---

### 2. Bands App

**Location:** `bands/`

Manages band profiles, service packages, photo galleries, and availability calendars.

#### Features
- Band managers can create and edit their band profile
- Upload a profile photo (thumbnail)
- Add up to 20 gallery images with captions and reordering
- Create service packages with min/max pricing and durations
- Manage availability calendar (per-date status: available / blocked / booked / pending)
- **Explore page** with search and filters for customers

#### Models

| Model | Description |
|-------|-------------|
| `BandProfile` | Core band info: name, description, genres (JSON), event types (JSON), location, contact, ratings, photo |
| `ServicePackage` | A named package for a band with min/max price and duration |
| `GalleryImage` | A photo for the band's gallery with ordering |
| `BandAvailability` | Per-date availability status for a band |

#### Genre Options
`carnatic`, `bollywood`, `jazz`, `rock`, `pop`, `folk`, `classical`, `western`, `fusion`, `devotional`, `instrumental`, `electronic`

#### Event Type Options
`wedding`, `college`, `school`, `corporate`, `private`

#### Location Tier Options
`metro`, `tier1`, `tier2`, `rural`

#### Availability Statuses
| Status | Meaning |
|--------|---------|
| `available` | Band is free on that date |
| `blocked` | Manager has manually blocked the date |
| `booked` | Confirmed booking exists |
| `pending` | Enquiry received but not yet confirmed |

#### Key Views

| View | URL | Description |
|------|-----|-------------|
| `explore` | `/bands/explore/` | Browse all bands with genre/event type/rating filters |
| `band_profile_detail` | `/bands/<pk>/` | Full public profile page |
| `manager_dashboard` | `/bands/dashboard/` | Band manager's main dashboard |
| `create_band_profile` | `/bands/create/` | Create a new band profile |
| `edit_band_profile` | `/bands/edit/` | Edit existing band profile |
| `manage_packages` | `/bands/packages/` | List, add, edit packages |
| `manage_gallery` | `/bands/gallery/` | Manage gallery images |
| `upload_gallery_image` | `/bands/gallery/upload/` | Upload a new gallery photo |
| `delete_gallery_image` | `/bands/gallery/<pk>/delete/` | Delete a gallery image |
| `manage_availability` | `/bands/availability/` | Edit per-date availability |
| `check_availability_ajax` | `/bands/check-availability/` | AJAX check for a specific date |

#### Band Rating Calculation

```python
# BandProfile.update_rating()
ratings = Rating.objects.filter(band=self)
total = sum(r.stars for r in ratings)
self.average_rating = round(total / ratings.count(), 1)
self.total_reviews = ratings.count()
self.save()
```
Called automatically when a rating is saved or deleted.

---

### 3. Enquiries App

**Location:** `enquiries/`

Handles the full flow from a customer submitting an enquiry to a manager accepting or rejecting it.

#### Features
- Customers submit enquiries from a band's profile page
- Auto-generated reference number (`BNZ` + 8 digits e.g. `BNZ12345678`)
- AI auto-categorisation of the enquiry message using NLP
- Automatic personalised reply sent to the customer
- In-app messaging thread between customer and manager
- Manager can accept or reject enquiries
- Accepted enquiry → creates a Booking

#### Enquiry Categories (AI-classified)
| Category | Description |
|----------|-------------|
| `booking_request` | Customer wants to book a specific date |
| `price_enquiry` | Customer asking about pricing/fees |
| `availability_enquiry` | Customer checking if a date is free |
| `general_information` | General questions about the band |
| `complaint` | Customer issue or complaint (high priority) |

#### Enquiry Statuses
`pending` → `reviewed` → `accepted` / `rejected` → `completed` / `cancelled`

#### Models

| Model | Description |
|-------|-------------|
| `Enquiry` | Full enquiry record: customer, band, package, event details, message, AI category, status |
| `EnquiryMessage` | Individual message in the enquiry thread (by customer or manager), supports image attachments |

#### Key Views

| View | URL | Description |
|------|-----|-------------|
| `submit_enquiry` | `/enquiries/send/<band_id>/` | Submit a new enquiry to a band |
| `my_enquiries` | `/enquiries/my-enquiries/` | Customer's enquiry list |
| `enquiry_detail` | `/enquiries/<pk>/` | Full enquiry thread and details |
| `cancel_enquiry` | `/enquiries/<pk>/cancel/` | Customer cancels an enquiry |
| `send_enquiry_message` | `/enquiries/<pk>/message/` | Send a message in the thread |
| `manager_enquiry_list` | `/enquiries/manage/` | Manager views all received enquiries |
| `accept_enquiry` | `/enquiries/manage/<pk>/accept/` | Manager accepts → creates Booking |
| `reject_enquiry` | `/enquiries/manage/<pk>/reject/` | Manager rejects enquiry |
| `pricing_estimator_ajax` | `/enquiries/pricing-estimate/` | AI price estimate (AJAX) |

#### AI Auto-Response Flow

```
Customer submits enquiry
       ↓
classify_enquiry(message) → (category, confidence)
       ↓
get_auto_response(category, enquiry) → personalised email text
       ↓
Auto-reply sent to customer + enquiry marked auto_reply_sent=True
```

---

### 4. Bookings App

**Location:** `bookings/`

Manages confirmed bookings and Stripe online payments.

#### Features
- Booking created automatically when a manager accepts an enquiry
- Manager sets the agreed amount and payment type before accepting
- Supports three payment modes: Full, Advance (partial), Offline (pay later)
- Stripe Checkout integration for online payments
- Customer can cancel a pending booking
- Manager can mark a booking as completed
- Manager can mark an advance-paid booking as fully paid (offline confirmation)
- Reminder and rating prompt tracking flags

#### Booking Statuses
| Status | Description |
|--------|-------------|
| `pending_payment` | Booking created, waiting for payment |
| `confirmed` | Payment received / offline confirmed |
| `completed` | Event is done |
| `cancelled` | Booking was cancelled |

#### Payment Types
| Type | Description |
|------|-------------|
| `full` | Customer pays the full agreed amount online |
| `advance` | Customer pays a partial advance online |
| `offline` | No online payment; manager marks as paid manually |

#### Models

| Field | Description |
|-------|-------------|
| `enquiry` | One-to-one link to the originating Enquiry |
| `customer` / `band` / `package` | Related party FKs |
| `event_date`, `event_type`, `event_location` | Event details |
| `agreed_amount` | Final agreed fee |
| `payment_type` | `full` / `advance` / `offline` |
| `advance_amount` | Amount for advance payment |
| `status` | Booking lifecycle status |
| `payment_status` | `pending` / `paid` / `failed` |
| `stripe_checkout_session_id` | Stripe session for reconciliation |

#### Key Views

| View | URL | Description |
|------|-----|-------------|
| `my_bookings` | `/bookings/my-bookings/` | Customer's booking list |
| `booking_detail` | `/bookings/<pk>/` | Booking detail with payment option |
| `cancel_booking` | `/bookings/<pk>/cancel/` | Customer cancels a booking |
| `manager_bookings` | `/bookings/manage/` | Manager's received bookings list |
| `mark_completed` | `/bookings/manage/<pk>/complete/` | Manager marks booking as done |
| `mark_fully_paid` | `/bookings/manage/<pk>/paid/` | Manager marks advance booking as fully paid |
| `create_checkout_session` | `/bookings/<pk>/checkout/` | Initiates Stripe Checkout |
| `payment_success` | `/bookings/payment-success/` | Stripe redirects here on success |
| `payment_cancel` | `/bookings/payment-cancel/` | Stripe redirects here on cancel |
| `stripe_webhook` | `/bookings/webhook/stripe/` | Stripe webhook for payment events |

#### Stripe Checkout Flow

```
Customer clicks "Pay Now"
       ↓
create_checkout_session() → stripe.checkout.Session.create()
       ↓ Stripe-hosted payment page
       ↓ Success → payment_success view updates booking status → confirmed
       ↓ Cancel  → payment_cancel view
       ↓ Webhook → stripe_webhook view (server-side confirmation)
```

---

### 5. Reviews App

**Location:** `reviews/`

Allows customers to rate and review bands after a completed booking.

#### Features
- Only customers with a **completed** booking can leave a review
- One review per booking (enforced via `OneToOneField`)
- Star rating from 1–5 with text review
- Reviews auto-update the band's `average_rating` and `total_reviews`
- Admin can approve/hide reviews

#### Models

| Model | Fields |
|-------|--------|
| `Rating` | `customer`, `band`, `booking` (OneToOne), `stars` (1–5), `review` text, `event_type`, `is_approved` |

#### Rating Auto-Update

Any time a `Rating` is saved or deleted, `band.update_rating()` is called automatically via the model's `save()` and `delete()` overrides, recalculating the average from scratch.

---

### 6. Chatbot App

**Location:** `chatbot/`

An AI-powered chatbot assistant embedded on the platform.

#### Features
- Persistent chat widget available site-wide (bottom-right corner)
- Detects user intent using NLTK-powered NLP
- Can answer questions about: availability, pricing, packages, booking process, event types, ratings, navigation
- Can look up live band data (availability, packages, ratings) from the database
- Falls back gracefully when NLTK is not available

#### Intent Types

| Intent | Trigger Keywords | Response |
|--------|-----------------|----------|
| `greeting` | hello, hi, hey, help | Welcome message with capabilities |
| `availability` | available, free on, check date | Checks live band availability |
| `pricing` | price, cost, rate, how much | Lists band packages with prices |
| `packages` | package, plan, service | Lists available packages |
| `booking_process` | how to book, steps, procedure | 8-step booking guide |
| `event_type` | wedding, college, corporate... | Lists bands for that event type |
| `rating` | rating, review, stars | Shows band's rating |
| `navigation` | where, gallery, how to find | Navigation guide |
| `fallback` | (anything else) | Help options + Explore link |

#### AI NLP Pipeline

```
User message
     ↓
preprocess_text()     ← lowercase, strip punctuation
     ↓
tokenize + stopword removal + WordNet lemmatization (NLTK)
     ↓
detect_intent()       ← keyword matching
extract_band_name()   ← regex pattern on message
extract_date()        ← regex date patterns
     ↓
generate_chatbot_response()   ← looks up DB if needed
     ↓
JSON response to frontend
```

---

### 7. Core App

**Location:** `core/`

Handles the homepage, role-based dashboards, and the admin control panel.

#### Features
- Public homepage with search/filter for bands
- **Customer Dashboard**: summary of enquiries, bookings, recent activity
- **Band Manager Dashboard**: upcoming bookings, pending enquiries, profile status
- **Custom Admin Panel** (separate from Django `/admin/`): manage users, bands, enquiries, reviews

#### Key Views

| View | URL | Description |
|------|-----|-------------|
| `home` | `/` | Homepage with band search |
| `customer_dashboard` | `/dashboard/` | Customer's personal dashboard |
| `about` | `/about/` | About Bandez page |
| `contact` | `/contact/` | Contact page |
| `admin_dashboard` | `/admin-panel/` | Admin overview |
| `admin_users` | `/admin-panel/users/` | List and manage all users |
| `admin_toggle_user` | `/admin-panel/users/<pk>/toggle/` | Activate/deactivate a user |
| `admin_bands` | `/admin-panel/bands/` | List and manage all bands |
| `admin_approve_band` | `/admin-panel/bands/<pk>/approve/` | Approve a band profile |
| `admin_toggle_band` | `/admin-panel/bands/<pk>/toggle/` | Activate/deactivate a band |
| `admin_enquiries` | `/admin-panel/enquiries/` | View all platform enquiries |
| `admin_reviews` | `/admin-panel/reviews/` | Moderate reviews |

---

## 🗄 Database Models

```
accounts_user
    ↕ (FK)
bands_bandprofile ──→ bands_servicepackage
                  ──→ bands_galleryimage
                  ──→ bands_bandavailability
                  ──→ enquiries_enquiry ──→ enquiries_enquirymessage
                                        ──→ bookings_booking ──→ reviews_rating
```

### Complete Model Reference

| App | Model | Key Fields |
|-----|-------|-----------|
| accounts | `User` | `role`, `email` (unique), `is_email_verified`, `failed_login_attempts`, `lockout_until` |
| accounts | `EmailVerificationToken` | `user` (OneToOne), `token`, `created_at` |
| accounts | `PasswordResetOTP` | `user`, `otp` (6 chars), `is_used` |
| bands | `BandProfile` | `manager` (OneToOne User), `band_name`, `genres` (JSON), `event_types` (JSON), `location_tier`, `average_rating`, `total_reviews`, `is_approved` |
| bands | `ServicePackage` | `band`, `name`, `min_price`, `max_price`, `duration_hours` |
| bands | `GalleryImage` | `band`, `image`, `caption`, `order` |
| bands | `BandAvailability` | `band`, `date`, `status` (available/blocked/booked/pending) |
| enquiries | `Enquiry` | `customer`, `band`, `reference_number` (unique), `event_type`, `event_date`, `ai_category`, `ai_confidence`, `status`, `manager_note` |
| enquiries | `EnquiryMessage` | `enquiry`, `sender`, `message`, `attachment` |
| bookings | `Booking` | `enquiry` (OneToOne), `agreed_amount`, `payment_type`, `advance_amount`, `status`, `payment_status`, `stripe_checkout_session_id` |
| reviews | `Rating` | `customer`, `band`, `booking` (OneToOne), `stars` (1–5), `review`, `is_approved` |

---

## 🔗 URL Routes Reference

| App | Prefix | Example URL |
|-----|--------|-------------|
| core | `` | `/`, `/dashboard/`, `/admin-panel/` |
| accounts | `/accounts/` | `/accounts/login/`, `/accounts/register/customer/` |
| bands | `/bands/` | `/bands/explore/`, `/bands/3/`, `/bands/dashboard/` |
| enquiries | `/enquiries/` | `/enquiries/send/3/`, `/enquiries/my-enquiries/` |
| bookings | `/bookings/` | `/bookings/my-bookings/`, `/bookings/5/checkout/` |
| reviews | `/reviews/` | `/reviews/` |
| chatbot | `/chatbot/` | `/chatbot/` |

---

## 🤖 AI Engine (NLP)

**Location:** `core/ai_engine.py`

Three distinct AI components:

### 1. Enquiry Classifier
```python
category, confidence = classify_enquiry(message)
# Returns one of: booking_request, price_enquiry,
#                 availability_enquiry, general_information, complaint
```
- Uses weighted keyword matching after NLTK preprocessing
- Minimum confidence threshold: 0.4 (falls back to `general_information`)
- Complaint category has highest weight (4.0) — escalated urgently

### 2. AI Pricing Estimator
```python
min_price, max_price = estimate_price(
    package=pkg,
    event_type='wedding',
    duration=4,
    audience=200,
    location_tier='metro',
    is_weekend=True,
    is_holiday=False
)
```
**Multiplier Factors:**
| Factor | Details |
|--------|---------|
| Event Type | Wedding ×1.3, Corporate ×1.2, Private ×1.1, College ×1.0, School ×0.9 |
| Duration | Proportional to hours (base = 3 hrs) |
| Audience | >500 → +25%, >200 → +15%, >100 → +5% |
| Location | Metro +15%, Tier-1 +10%, Tier-2 ±0%, Rural −10% |
| Weekend | +10% |
| Holiday | +20% |

### 3. Chatbot Response Engine
```python
response_text, intent = generate_chatbot_response(message, user=request.user)
```
- Detects intent → extracts band name → extracts date → queries DB → returns response
- Falls back gracefully if NLTK is unavailable

---

## 💳 Payment Integration (Stripe)

Stripe test mode is configured. The platform uses **Stripe Checkout** (hosted payment page).

### Setup for Local Webhook Testing

1. Download `stripe.exe` (already in project root)
2. run the dev server: `python manage.py runserver`
3. In a separate terminal: `stripe listen --forward-to localhost:8000/bookings/webhook/stripe/`
4. Copy the webhook secret shown and update `STRIPE_WEBHOOK_SECRET` in `settings.py`

### Payment Flow

```
1. Manager accepts enquiry → sets agreed_amount + payment_type
2. Booking created (status: pending_payment)
3. Customer visits booking detail → clicks "Pay Now"
4. create_checkout_session() → Stripe Checkout session
5a. Success → payment_success view → booking.status = 'confirmed'
5b. Webhook → stripe_webhook → double-confirms payment
6. Offline payments → Manager clicks "Mark as Fully Paid"
```

### Test Card Numbers (Stripe)
| Card | Number | Use |
|------|--------|-----|
| Success | `4242 4242 4242 4242` | Successful payment |
| Decline | `4000 0000 0000 0002` | Card declined |
| 3D Secure | `4000 0025 0000 3155` | Auth required |

Use any future expiry date, any 3-digit CVC.

---

## 🛡 Admin Panel

Bandez has **two admin interfaces:**

### 1. Django Built-in Admin (`/admin/`)
Access with a superuser account. Full model-level access.

```bash
python manage.py createsuperuser
```

### 2. Custom Admin Panel (`/admin-panel/`)
Only accessible to users with `role='admin'` or `is_staff=True`.

Features:
- View all registered users (toggle active/inactive)
- View all band profiles (approve / toggle active)
- View all enquiries platform-wide
- Moderate customer reviews

---

## 🔐 Security Features

| Feature | Implementation |
|---------|---------------|
| Email-based login | `USERNAME_FIELD = 'email'` on custom User model |
| Account lockout | After 5 failed logins → locked 15 minutes |
| Session timeout | 30 minutes of inactivity → auto-logout |
| Email verification | UUID token link, 24-hour validity |
| OTP password reset | 6-digit OTP, 30-minute validity, single-use |
| CSRF protection | Django CSRF middleware (enabled globally) |
| Role-based access | `@login_required` + role checks in every view |
| Stripe webhook signature | `stripe.Webhook.construct_event()` with secret |

---

## 🚀 Running the Project

```bash
# Activate virtual environment
venv\Scripts\activate

# Apply any new migrations
python manage.py migrate

# Start the development server
python manage.py runserver

# (Optional) Start Stripe webhook listener in a second terminal
.\stripe.exe listen --forward-to localhost:8000/bookings/webhook/stripe/
```

**Default login redirect by role:**
- `customer` → `/dashboard/`
- `band_manager` → `/bands/dashboard/`
- `admin` / staff → `/admin-panel/`

---

## 📝 Notes for Developers

- **Templates** are in `templates/<app_name>/` (e.g., `templates/bands/profile_detail.html`)
- **Media files** (uploads) go to `media/band_profiles/`, `media/band_gallery/`, `media/message_attachments/`
- **Static files** (CSS/JS) are in `static/`
- Django template tags must always be on **a single line** (do not let your editor wrap them)
- The `DEBUG = True` setting allows serving media files locally — change for production
- Replace the `SECRET_KEY` in `settings.py` before any production deployment

---

*Built with ❤️ using Django • Bandez © 2025*
