"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

# Create test client
client = TestClient(app)


class TestActivities:
    """Tests for the activities endpoints"""

    def test_get_activities(self):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert "Basketball Team" in activities
        assert "Track and Field" in activities
        assert "Art Club" in activities

    def test_get_activities_structure(self):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_details in activities.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_basketball_team(self):
        """Test specific activity details"""
        response = client.get("/activities")
        activities = response.json()
        basketball = activities["Basketball Team"]
        
        assert basketball["max_participants"] == 15
        assert "alex@mergington.edu" in basketball["participants"]
        assert "james@mergington.edu" in basketball["participants"]


class TestSignup:
    """Tests for signup functionality"""

    def test_signup_new_student(self):
        """Test signing up a new student for an activity"""
        response = client.post(
            "/activities/Drama%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        result = response.json()
        assert "Signed up" in result["message"]
        
        # Verify the student was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "newstudent@mergington.edu" in activities["Drama Club"]["participants"]

    def test_signup_nonexistent_activity(self):
        """Test signing up for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_duplicate(self):
        """Test signing up when already registered"""
        email = "alex@mergington.edu"
        response = client.post(
            f"/activities/Basketball%20Team/signup?email={email}"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()


class TestUnregister:
    """Tests for unregister functionality"""

    def test_unregister_existing_student(self):
        """Test unregistering an existing student"""
        # First, sign up a student
        email = "unregister_test@mergington.edu"
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        # Then unregister them
        response = client.delete(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
        # Verify they were removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity(self):
        """Test unregistering from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_not_registered(self):
        """Test unregistering when not actually registered"""
        response = client.delete(
            "/activities/Programming%20Class/signup?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()


class TestRoot:
    """Tests for the root endpoint"""

    def test_root_redirect(self):
        """Test that root path redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_signup_and_unregister_workflow(self):
        """Test a complete signup and unregister workflow"""
        email = "workflow_test@mergington.edu"
        activity = "Science%20Olympiad"
        
        # Get initial state
        initial_response = client.get("/activities")
        initial_participants = len(initial_response.json()["Science Olympiad"]["participants"])
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify signup
        after_signup = client.get("/activities")
        after_signup_participants = len(after_signup.json()["Science Olympiad"]["participants"])
        assert after_signup_participants == initial_participants + 1
        assert email in after_signup.json()["Science Olympiad"]["participants"]
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/signup?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify unregister
        final_response = client.get("/activities")
        final_participants = len(final_response.json()["Science Olympiad"]["participants"])
        assert final_participants == initial_participants
        assert email not in final_response.json()["Science Olympiad"]["participants"]
