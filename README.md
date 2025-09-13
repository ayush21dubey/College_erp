# Student ERP System

A modern web application for managing student attendance data with automated scraping from the SRM CEM campus portal.

## Features

- 🔐 **Secure Authentication**: Login with roll number and password
- 📊 **Real-time Data Scraping**: Automatically fetches attendance data from the campus portal
- 📈 **Analytics Dashboard**: Comprehensive analytics and visualizations
- 🌙 **Dark Mode Support**: Beautiful dark/light theme toggle
- 📱 **Responsive Design**: Works perfectly on desktop and mobile devices
- 🔄 **Auto-refresh**: Data automatically refreshes every 5 minutes
- 💾 **SQLite Database**: Local data storage with proper schema

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd erpSRMCEM
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Chrome WebDriver**
   - Download ChromeDriver from [here](https://chromedriver.chromium.org/)
   - Place `chromedriver.exe` in the project root directory
   - Or use the provided `chromedriver.exe` in the repository

4. **Initialize the database**
   ```bash
   python connectdb.py
   ```

## Usage

1. **Start the application**
   ```bash
   python htmlRender.py
   ```

2. **Access the application**
   - Open your browser and go to `http://localhost:5000`
   - Login with your SRM CEM roll number and password

3. **Features available after login:**
   - View attendance records for all subjects
   - Access analytics dashboard with charts and statistics
   - Refresh data manually or wait for auto-refresh
   - Switch between light and dark themes

## Project Structure

```
erpSRMCEM/
├── htmlRender.py          # Main Flask application
├── connectdb.py           # Database operations
├── scrapp.py              # Web scraping functionality
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── Templates/            # HTML templates
│   ├── login.html        # Login page
│   ├── attendance.html   # Attendance dashboard
│   ├── dashboard.html    # Analytics dashboard
│   └── error.html        # Error pages
├── chromedriver.exe      # Chrome WebDriver
└── student_erp.db        # SQLite database (created automatically)
```

## Database Schema

The application uses SQLite with the following tables:

- **students**: Stores student information and login credentials
- **attendance_records**: Stores detailed attendance data for each subject
- **login_logs**: Tracks login history and sessions

## API Endpoints

- `GET /` - Login page
- `POST /login_handler` - Handle login form submission
- `GET /attendance` - Attendance dashboard
- `GET /dashboard` - Analytics dashboard
- `GET /scraping_status` - Get scraping status (JSON)
- `POST /refresh_data` - Refresh attendance data
- `GET /logout` - Logout user
- `GET /api/attendance_data` - Get attendance data (JSON)

## Security Features

- Password hashing using Werkzeug's security functions
- Session management for user authentication
- Input validation and sanitization
- SQL injection prevention with parameterized queries

## Browser Compatibility

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Troubleshooting

1. **ChromeDriver issues**: Make sure ChromeDriver is in the project root and matches your Chrome version
2. **Scraping fails**: Check your internet connection and campus portal availability
3. **Database errors**: Delete `student_erp.db` and restart the application to recreate the database

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support or questions, please open an issue in the repository.
