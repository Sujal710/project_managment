//C:\Users\Sujal\Downloads\Project Management Assistant Functional Features Overview\app.js
const API_BASE_URL = window.location.origin;

const outputElement = document.getElementById('output');
const memberListElement = document.getElementById('member-list');
const projectListElement = document.getElementById('project-list');

function logResponse(data) {
    outputElement.textContent = JSON.stringify(data, null, 2);
}

async function apiCall(url, method = 'GET', body = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
    };
    if (body) {
        options.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(url, options);
        const data = await response.json();
        logResponse(data);
        if (!response.ok) {
            throw new Error(data.detail || `HTTP error! status: ${response.status}`);
        }
        return data;
    } catch (error) {
        console.error('API Call Error:', error);
        outputElement.textContent = `Error: ${error.message}\n\nCheck console for details.`;
        return null;
    }
}

// --- Member Functions ---

async function createMember() {
    const name = document.getElementById('member-name').value;
    const email = document.getElementById('member-email').value;
    const role = document.getElementById('member-role').value;
    const availability = parseInt(document.getElementById('member-availability').value);

    if (!name || !email || !role || isNaN(availability)) {
        alert("Please fill all member fields correctly.");
        return;
    }

    const memberData = {
        name: name,
        email: email,
        role: role,
        skills: [],
        experience_years: 0,
        availability_percent: availability
    };

    const newMember = await apiCall(`${API_BASE_URL}/members/`, 'POST', memberData);
    if (newMember) {
        fetchMembers();
    }
}

async function fetchMembers() {
    const members = await apiCall(`${API_BASE_URL}/members/`);
    memberListElement.innerHTML = '';
    if (members && Array.isArray(members)) {
        members.forEach(member => {
            const li = document.createElement('li');
            li.textContent = `${member.name} (${member.role}) - ID: ${member.id}`;
            memberListElement.appendChild(li);
        });
    }
}

// --- Project Functions ---

async function createProject() {
    const name = document.getElementById('project-name').value;
    const description = document.getElementById('project-description').value;
    const memberId = document.getElementById('project-member-id').value;

    if (!name || !memberId) {
        alert("Please fill Project Name and Team Member ID.");
        return;
    }

    const projectData = {
        name: name,
        description: description,
        status: "Not Started",
        milestones: [],
        team_members: [memberId]
    };

    const newProject = await apiCall(`${API_BASE_URL}/projects/`, 'POST', projectData);
    if (newProject) {
        fetchProjects();
    }
}

async function fetchProjects() {
    const projects = await apiCall(`${API_BASE_URL}/projects/`);
    projectListElement.innerHTML = '';
    if (projects && Array.isArray(projects)) {
        projects.forEach(project => {
            const li = document.createElement('li');
            li.textContent = `${project.name} (${project.status}) - ID: ${project.id}`;
            projectListElement.appendChild(li);
        });
    }
}

// --- Task Functions ---

async function createTask() {
    const projectId = document.getElementById('task-project-id').value;
    const name = document.getElementById('task-name').value;
    const estimatedHours = parseFloat(document.getElementById('task-estimated-hours').value);
    const assignedMemberId = document.getElementById('task-assigned-member-id').value;

    if (!projectId || !name || isNaN(estimatedHours) || !assignedMemberId) {
        alert("Please fill all task fields correctly.");
        return;
    }

    const taskData = {
        project_id: projectId,
        name: name,
        priority: "Medium",
        estimated_duration_hours: estimatedHours,
        assigned_to: [assignedMemberId]
    };

    await apiCall(`${API_BASE_URL}/tasks/`, 'POST', taskData);
}

// Initial fetch on load
window.onload = () => {
    fetchMembers();
    fetchProjects();
};
