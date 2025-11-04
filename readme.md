# Project Management Assistant

A comprehensive project management system built with FastAPI and MongoDB, featuring team member management, project tracking, task assignment, time logging, and workload analytics.

## Features

- **User Authentication**: Secure JWT-based authentication with registration and login
- **Team Member Management**: Add, edit, and manage team members with skills and availability tracking
- **Project Management**: Create and track projects with milestones and deadlines
- **Task Management**: Assign tasks with priorities, estimated hours, and dependencies
- **Time Tracking**: Log work hours and compare against estimates
- **Workload Analytics**: Monitor team workload and resource utilization
- **Real-time Dashboard**: Interactive web interface with Bootstrap 5

## Tech Stack

- **Backend**: FastAPI, Python 3.8+
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: JWT tokens with bcrypt password hashing
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Validation**: Pydantic models

## Prerequisites

- Python 3.8 or higher
- MongoDB 4.4 or higher (local or cloud instance)
- pip package manager

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Project-Management-Assistant
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure MongoDB**
   
   Update the MongoDB connection string in `main.py`:
   ```python
   MONGO_URI = "mongodb://localhost:27017"  # For local MongoDB
   # OR
   MONGO_URI = "mongodb+srv://username:password@cluster.mongodb.net"  # For MongoDB Atlas
   ```

5. **Configure Secret Key**
   
   Update the JWT secret key in `app/routers/auth.py`:
   ```python
   SECRET_KEY = "your-secret-key-change-this-in-production"
   ```

## Running the Application

1. **Start the FastAPI server**
   ```bash
   uvicorn main:app --reload
   ```

2. **Access the application**
   - Frontend: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Alternative API Documentation: http://localhost:8000/redoc

## Project Structure

```
Project-Management-Assistant/
├── app/
│   ├── routers/
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── members.py       # Team member management
│   │   ├── projects.py      # Project management
│   │   ├── tasks.py         # Task management
│   │   ├── time_logs.py     # Time logging
│   │   └── assignment.py    # Workload analytics
│   ├── models.py            # Pydantic models
│   └── database.py          # Database operations
├── main.py                  # FastAPI application entry point
├── index.html              # Frontend interface
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user info

### Members
- `POST /members/` - Create team member
- `GET /members/` - List all members
- `GET /members/{member_id}` - Get member by ID
- `PUT /members/{member_id}` - Update member
- `DELETE /members/{member_id}` - Delete member

### Projects
- `POST /projects/` - Create project
- `GET /projects/` - List all projects
- `GET /projects/{project_id}` - Get project by ID
- `PUT /projects/{project_id}` - Update project
- `DELETE /projects/{project_id}` - Delete project

### Tasks
- `POST /tasks/` - Create task
- `GET /tasks/` - List all tasks
- `GET /tasks/{task_id}` - Get task by ID
- `PUT /tasks/{task_id}` - Update task
- `DELETE /tasks/{task_id}` - Delete task
- `GET /tasks/{task_id}/time-summary` - Get time tracking summary

### Time Logs
- `POST /time_logs/` - Create time log
- `GET /time_logs/` - List all time logs
- `GET /time_logs/{log_id}` - Get time log by ID
- `PUT /time_logs/{log_id}` - Update time log
- `DELETE /time_logs/{log_id}` - Delete time log

### Analytics
- `GET /assignment/workload/{member_id}` - Get member workload

## Usage Guide

### First Time Setup

1. **Register an Account**
   - Open the application in your browser
   - Click "Don't have an account? Register"
   - Fill in your details and submit

2. **Add Team Members**
   - Navigate to "Team Members"
   - Click "+ Add Member"
   - Enter member details including skills and availability

3. **Create a Project**
   - Navigate to "Projects"
   - Click "+ Add Project"
   - Set project name, description, status, and deadline

4. **Create Tasks**
   - Navigate to "Tasks"
   - Click "+ Add Task"
   - Assign to a project and team member
   - Set priority, estimated hours, and status

5. **Log Work Time**
   - Navigate to "Time Logs"
   - Click "+ Log Time"
   - Select task, member, and hours worked

6. **Monitor Workload**
   - Navigate to "Workload"
   - View team utilization and active task counts

## Features in Detail

### Time Tracking
- Real-time comparison of estimated vs. actual hours
- Visual progress bars with color-coded status:
  - Green: Under budget
  - Yellow: Near budget limit (90%+)
  - Red: Over budget
- Automatic calculations per task

### Workload Management
- Team member availability tracking
- Active task counts
- Total estimated hours per member
- Utilization percentage calculation

### Task Priorities
- High (Red border)
- Medium (Yellow border)
- Low (Green border)

### Task Statuses
- To Do
- In Progress
- Done

## Security Considerations

⚠️ **Important Security Notes:**

1. Change the `SECRET_KEY` in `app/routers/auth.py` before production
2. Use environment variables for sensitive configuration
3. Enable HTTPS in production
4. Configure CORS properly for your domain
5. Use strong passwords (minimum 6 characters enforced)
6. JWT tokens expire after 24 hours

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Style
```bash
# Install formatting tools
pip install black flake8

# Format code
black .

# Check code style
flake8
```

## Troubleshooting

### MongoDB Connection Issues
- Verify MongoDB is running: `mongosh` or `mongo`
- Check connection string format
- Ensure network access for MongoDB Atlas

### CORS Errors
- Update allowed origins in `main.py`
- Check that frontend URL matches CORS settings

### Authentication Issues
- Clear browser localStorage
- Check JWT token expiration
- Verify SECRET_KEY consistency

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the API documentation at `/docs`

## Roadmap

- [ ] Email notifications
- [ ] Task dependencies visualization
- [ ] Gantt chart view
- [ ] Export reports (PDF/Excel)
- [ ] Mobile app
- [ ] Real-time collaboration
- [ ] File attachments
- [ ] Comments and discussions