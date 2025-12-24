# RideON - Complete Ride Booking Platform

A comprehensive Django-based ride booking application with advanced features including trip management, payment processing, user preferences, and administrative controls.

![RideON](https://img.shields.io/badge/Django-5.2.4-green.svg)
![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)

## 🚀 Key Features

### 🎯 **Smart Booking System**
- Single trip restriction (one active trip at a time)
- Multiple vehicle types: Auto, Bike, Car, Luxury
- Real-time fare calculation with promocode support
- Trip status tracking with countdown timers

### 💳 **Multi-Payment Gateway**
- Digital wallet system with transaction history
- Cash, card, and UPI payment options
- Secure payment processing
- Balance validation and error handling

### 🍪 **Advanced Cookie System**
- User preference storage and management
- Recent locations and favorite routes
- Smart form pre-filling
- Personalized user experience

### 👨‍💼 **Admin Dashboard**
- Comprehensive trip management
- Real-time trip status controls
- User and driver management
- Analytics and reporting

### 📱 **Modern UI/UX**
- Responsive mobile-first design
- Purple gradient theme with animations
- FontAwesome icons throughout
- Interactive countdown timers

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+ (recommended 3.13)
- pip package manager
- Virtual environment (recommended)

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/darsh815/RideON.git
   cd RideON
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup database:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create admin user:**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run development server:**
   ```bash
   python manage.py runserver
   ```

7. **Access the application:**
   Open http://127.0.0.1:8000/ in your browser

## 📊 Project Structure

```
rideon/
├── rideon/                 # Main project directory
│   ├── settings.py        # Django settings
│   ├── urls.py           # Main URL routing
│   └── wsgi.py           # WSGI configuration
├── core/                  # Core application
│   ├── models.py         # Database models
│   ├── views.py          # Business logic
│   ├── urls.py           # App URLs
│   ├── cookie_utils.py   # Cookie management
│   ├── documentation.py  # Documentation generator
│   └── migrations/       # Database migrations
├── accounts/              # User management
│   ├── models.py         # User profiles
│   ├── views.py          # Authentication logic
│   └── urls.py           # Auth URLs
├── templates/             # HTML templates
│   ├── core/             # Core templates
│   └── accounts/         # Auth templates
├── static/                # Static files
│   └── css/              # Stylesheets
└── requirements.txt       # Dependencies
```

## 🎮 Usage Guide

### For End Users

1. **Registration & Login:**
   - Create account or login
   - Complete profile setup

2. **Booking a Ride:**
   - Select vehicle type
   - Enter pickup and destination
   - Apply promocodes if available
   - Confirm booking and payment

3. **Managing Trips:**
   - View active trips in booking history
   - Track trip status with countdown
   - Complete payment after trip ends

4. **User Preferences:**
   - Access preferences from any page
   - Set preferred vehicle and payment methods
   - Manage recent locations and favorites

### For Administrators

1. **Admin Dashboard:**
   - Login with admin credentials
   - Access `/admin_dashboard/` for trip management

2. **Trip Management:**
   - Start/end trips manually
   - Monitor ongoing trips
   - Handle customer issues

3. **User Management:**
   - Grant/revoke admin privileges
   - Manage user profiles and wallets

## 🔧 Configuration

### Database Settings
```python
# For PostgreSQL (production)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'rideon_db',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Security Settings
```python
# Production security
SECURE_SSL_REDIRECT = True
SECURE_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## 📝 API Endpoints

- `POST /apply_promocode/` - Apply discount codes
- `GET /trip_details/<id>/` - Get trip details
- `POST /complete_trip/<id>/` - Complete trip
- `GET /preferences/` - User preferences management
- `POST /download_documentation/` - Download documentation

## 🍪 Cookie System

The application uses an advanced cookie system for enhanced user experience:

- **rideon_preferences:** User settings and preferences
- **rideon_recent_locations:** Recent pickup/destination locations
- **rideon_favorite_routes:** Saved favorite routes
- **rideon_booking_prefs:** Booking-specific preferences

## 📚 Documentation

Access comprehensive documentation at `/documentation/` including:
- Complete feature guide
- Installation instructions
- API reference
- Troubleshooting guide
- Download as Word document

## 🚨 Troubleshooting

### Common Issues

1. **Migration Errors:**
   ```bash
   python manage.py migrate --fake-initial
   ```

2. **Static Files Not Loading:**
   ```bash
   python manage.py collectstatic
   ```

3. **Admin Access Issues:**
   ```bash
   python manage.py createsuperuser
   ```

4. **Cookie Problems:**
   - Clear browser cache
   - Check JavaScript is enabled
   - Verify cookie settings

## 🔄 Development

### Running Tests
```bash
python manage.py test
```

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings for functions

### Contributing
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## 📋 Dependencies

- Django 5.2.4
- python-docx (for documentation)
- Additional packages in requirements.txt

## 🔒 Security Features

- CSRF protection on all forms
- Secure cookie handling
- Input validation and sanitization
- SQL injection prevention
- XSS protection

## 📈 Performance

- Optimized database queries
- Efficient session management
- Responsive design for fast loading
- Cookie-based preferences (no DB queries)

## 🌟 Future Enhancements

- Real-time GPS tracking
- Mobile app development
- AI-powered route optimization
- Multi-language support
- Payment gateway integrations

## 📞 Support

For issues and support:
- Check documentation at `/documentation/`
- Review troubleshooting guide
- Create GitHub issue
- Contact development team

## 📄 License

This project is proprietary. All rights reserved.

## 🤝 Contributors

- **Development Team** - Initial work and ongoing maintenance
- **Community Contributors** - Bug reports and feature suggestions

---

**Built with ❤️ using Django**

*RideON - Your Complete Ride Booking Solution*
