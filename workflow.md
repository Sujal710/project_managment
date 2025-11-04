# Project Management Assistant - Detailed Workflows

## 1. Authentication Workflow

```
User Registration Flow:
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ 1. Submit registration form
       │    (username, email, password, full_name)
       ▼
┌─────────────────────┐
│  Auth Router        │
│  /auth/register     │
└──────┬──────────────┘
       │ 2. Validate input (Pydantic)
       │ 3. Check if username/email exists
       ▼
┌─────────────────────┐
│  Password Hashing   │
│  (bcrypt)           │
└──────┬──────────────┘
       │ 4. Hash password with salt
       ▼
┌─────────────────────┐
│  MongoDB            │
│  Users Collection   │
└──────┬──────────────┘
       │ 5. Store user document
       ▼
┌─────────────────────┐
│  JWT Token Gen      │
└──────┬──────────────┘
       │ 6. Create access token (24h expiry)
       ▼
┌─────────────────────┐
│  Response           │
│  {token, user_info} │
└─────────────────────┘

User Login Flow:
Browser → Auth Router → Verify Password → Generate JWT → Return Token
```

## 2. Team Member Management Workflow

```
Create Member:
┌─────────────┐
│   Browser   │ → Click "Add Member"
└──────┬──────┘
       │ Fill form: name, email, role, skills, 
       │            experience, availability
       ▼
┌─────────────────────┐
│  Members Router     │
│  POST /members/     │
└──────┬──────────────┘
       │ Validate with MemberBase model
       │ - Name (required, min 1 char)
       │ - Email (valid email format)
       │ - Role (required)
       │ - Skills (list of strings)
       │ - Experience (≥0 years)
       │ - Availability (0-100%)
       ▼
┌─────────────────────┐
│  Database Handler   │
└──────┬──────────────┘
       │ Convert PyObjectId
       │ Create timestamps
       ▼
┌─────────────────────┐
│  MongoDB            │
│  members collection │
└──────┬──────────────┘
       │ Insert document
       │ Return new member with _id
       ▼
┌─────────────────────┐
│  Response (201)     │
│  Member object      │
└─────────────────────┘
```

## 3. Project Management Workflow

```
Create Project:
Browser → Submit Project Form
    ↓
Projects Router (POST /projects/)
    ↓
Validate ProjectBase:
    - name (required)
    - description (optional)
    - status (default: "Not Started")
    - milestones (list)
    - deadline (optional datetime)
    - team_member_ids (list of ObjectIds)
    ↓
Database Handler
    ↓
MongoDB projects collection
    ↓
Response with created project

Update Project Status:
Load Project → Edit Modal → Update Status → PUT /projects/{id}
    ↓
Update timestamps
    ↓
Return updated project
```

## 4. Task Management Workflow

```
Create Task Flow:
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ 1. Select "Add Task"
       │ 2. Choose Project (dropdown)
       │ 3. Fill task details
       ▼
┌─────────────────────────────┐
│  Tasks Router               │
│  POST /tasks/               │
└──────┬──────────────────────┘
       │ Validate TaskBase:
       │ - project_id (required, valid ObjectId)
       │ - name (required)
       │ - description (optional)
       │ - status (default: "To Do")
       │ - priority (Low/Medium/High)
       │ - estimated_duration_hours (>0)
       │ - assigned_to_ids (list of member IDs)
       │ - dependency_ids (list of task IDs)
       │ - due_date (optional)
       ▼
┌─────────────────────────────┐
│  Database Handler           │
└──────┬──────────────────────┘
       │ Convert string IDs to ObjectId
       │ Create timestamps
       ▼
┌─────────────────────────────┐
│  MongoDB tasks collection   │
└──────┬──────────────────────┘
       │ Store task document
       ▼
┌─────────────────────────────┐
│  Frontend Update            │
│  Reload tasks list          │
└─────────────────────────────┘

Task Time Summary Flow:
GET /tasks/{task_id}/time-summary
    ↓
Validate task_id (ObjectId format)
    ↓
Fetch task from tasks collection
    ↓
Aggregate time logs for this task:
    - Sum hours_spent
    - Count number of logs
    ↓
Calculate:
    - total_hours_spent
    - difference = total - estimated
    - percentage_used = (total/estimated) * 100
    - status: over_budget | under_budget | on_budget
    ↓
Return summary object
```

## 5. Time Logging Workflow

```
Log Work Time:
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ 1. Click "Log Time"
       │ 2. Select Task (dropdown)
       │ 3. Select Member (dropdown)
       │ 4. Enter hours worked
       │ 5. Add notes (optional)
       ▼
┌──────────────────────────┐
│  Time Logs Router        │
│  POST /time_logs/        │
└──────┬───────────────────┘
       │ Validate TimeLogBase:
       │ - task_id (required, valid ObjectId)
       │ - member_id (required, valid ObjectId)
       │ - hours_spent (>0)
       │ - date_logged (default: now)
       │ - notes (optional)
       ▼
┌──────────────────────────┐
│  Database Handler        │
└──────┬───────────────────┘
       │ Convert IDs to ObjectId
       │ Set created_at timestamp
       ▼
┌──────────────────────────┐
│  MongoDB                 │
│  time_logs collection    │
└──────┬───────────────────┘
       │ Insert log entry
       ▼
┌──────────────────────────┐
│  Trigger Updates         │
└──────┬───────────────────┘
       │ Reload time logs
       │ Recalculate task time summaries
       │ Update workload analytics
       ▼
┌──────────────────────────┐
│  Frontend Refresh        │
│  Show updated data       │
└──────────────────────────┘
```

## 6. Workload Analytics Workflow

```
Calculate Member Workload:
┌─────────────────────────────┐
│  Assignment Router          │
│  GET /assignment/workload/  │
│      {member_id}            │
└──────┬──────────────────────┘
       │ 1. Validate member_id
       ▼
┌─────────────────────────────┐
│  Fetch Member Data          │
└──────┬──────────────────────┘
       │ Get availability_percent
       ▼
┌─────────────────────────────┐
│  MongoDB Aggregation        │
│  Pipeline                   │
└──────┬──────────────────────┘
       │ Match: assigned_to_ids = member_id
       │        AND status ≠ "Done"
       │ Group: Sum estimated_duration_hours
       │        Count active tasks
       ▼
┌─────────────────────────────┐
│  Calculate Metrics          │
└──────┬──────────────────────┘
       │ total_hours = sum of all active tasks
       │ active_tasks_count = count
       │ utilization = (total_hours / weekly_capacity) * 100
       │ weekly_capacity = (availability_percent/100) * 40
       ▼
┌─────────────────────────────┐
│  Return Workload Object     │
└──────┬──────────────────────┘
       │ {
       │   member_id,
       │   member_name,
       │   availability_percent,
       │   active_tasks_count,
       │   total_estimated_hours_assigned
       │ }
       ▼
┌─────────────────────────────┐
│  Frontend Display           │
│  - Progress bars            │
│  - Utilization percentage   │
│  - Color coding             │
└─────────────────────────────┘
```

## 7. Data Relationships

```
┌─────────┐
│  User   │
└─────────┘

┌──────────┐       ┌──────────┐       ┌──────────┐
│  Member  │───┐   │ Project  │───┐   │   Task   │
└──────────┘   │   └──────────┘   │   └──────────┘
               │                   │         │
               │                   │         │
               └───────┬───────────┘         │
                       │                     │
                       │   ┌─────────────────┘
                       │   │
                       ▼   ▼
                  ┌────────────┐
                  │  TimeLog   │
                  └────────────┘

Relationships:
- Member can be assigned to multiple Tasks
- Task belongs to one Project
- Task can be assigned to multiple Members
- TimeLog references one Task and one Member
- Project can have multiple team_member_ids
- Task can have multiple dependency_ids (other tasks)
```

## 8. Frontend State Management Flow

```
Application State:
┌─────────────────────────────────┐
│  Global Variables               │
├─────────────────────────────────┤
│  - authToken (JWT)              │
│  - currentUser (user object)    │
│  - members[] (array)            │
│  - projects[] (array)           │
│  - tasks[] (array)              │
│  - timeLogs[] (array)           │
│  - taskTimeSummaries{} (object) │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  API Call Flow                  │
├─────────────────────────────────┤
│  1. apiCall(endpoint, method,   │
│     body, authToken)            │
│  2. Check response status       │
│  3. Handle 401 → logout         │
│  4. Parse JSON                  │
│  5. Normalize documents         │
│     (_id → id)                  │
│  6. Update global state         │
│  7. Re-render UI                │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  UI Update Triggers             │
├─────────────────────────────────┤
│  - renderMembers()              │
│  - renderProjects()             │
│  - renderTasks()                │
│  - renderTimeLogs()             │
│  - renderWorkload()             │
└─────────────────────────────────┘
```

## 9. Error Handling Flow

```
Request Error Handling:
API Call → Try-Catch Block
    ↓
Catch Error Types:
    - 401 Unauthorized → Logout user
    - 404 Not Found → Show "Not found" alert
    - 400 Bad Request → Show validation error
    - 500 Server Error → Show "Server error" alert
    ↓
Display Error Message
    ↓
Keep UI in consistent state

Validation Flow:
Frontend Validation:
    - Required fields
    - Email format
    - Number ranges
    - Date formats
    ↓
Submit to Backend
    ↓
Pydantic Model Validation:
    - Type checking
    - Field validators
    - Business rules
    ↓
Database Constraints:
    - Unique emails/usernames
    - Valid ObjectIds
    - Reference integrity
    ↓
Return Appropriate Error
```

## 10. Complete User Journey

```
1. User Arrives → Authentication Required
2. Register/Login → Receive JWT Token
3. Token Stored in localStorage
4. Access Main App → Token Validated on Every Request
5. Add Team Members → Create member profiles
6. Create Projects → Define project scope
7. Create Tasks → Assign to projects and members
8. Log Work Time → Track actual hours
9. View Analytics → Monitor progress and workload
10. Update Task Status → Mark as complete
11. View Reports → Time tracking summaries
12. Logout → Clear token and return to login
```