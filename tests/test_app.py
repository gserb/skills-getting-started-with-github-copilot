from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_root_redirect():
    """Test that root endpoint redirects to static/index.html"""
    response = client.get("/")
    assert response.status_code == 307  # Temporary redirect
    assert response.headers["location"] == "/static/index.html"

def test_get_activities():
    """Test getting the list of activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    assert isinstance(activities, dict)
    assert len(activities) > 0
    
    # Test structure of an activity
    activity = list(activities.values())[0]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity
    assert isinstance(activity["participants"], list)

def test_signup_new_participant():
    """Test signing up a new participant for an activity"""
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    
    # First ensure the student isn't already registered
    response = client.get("/activities")
    initial_participants = response.json()[activity_name]["participants"]
    if email in initial_participants:
        # Use the unregister endpoint to remove them first
        client.delete(f"/activities/{activity_name}/unregister?email={email}")
    
    # Now try to register them
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    
    # Verify they were added
    response = client.get("/activities")
    updated_participants = response.json()[activity_name]["participants"]
    assert email in updated_participants

def test_signup_duplicate_participant():
    """Test that signing up a participant twice fails"""
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # Using an email we know exists
    
    # Try to sign up
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()

def test_signup_nonexistent_activity():
    """Test signing up for an activity that doesn't exist"""
    response = client.post("/activities/NonexistentClub/signup?email=test@mergington.edu")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_unregister_participant():
    """Test unregistering a participant from an activity"""
    activity_name = "Chess Club"
    email = "temporarystudent@mergington.edu"
    
    # First register a temporary student
    client.post(f"/activities/{activity_name}/signup?email={email}")
    
    # Now unregister them
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    
    # Verify they were removed
    response = client.get("/activities")
    current_participants = response.json()[activity_name]["participants"]
    assert email not in current_participants

def test_unregister_not_registered():
    """Test unregistering a participant who isn't registered"""
    activity_name = "Chess Club"
    email = "notregistered@mergington.edu"
    
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"].lower()

def test_unregister_nonexistent_activity():
    """Test unregistering from an activity that doesn't exist"""
    response = client.delete("/activities/NonexistentClub/unregister?email=test@mergington.edu")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_activity_capacity():
    """Test that activities track their participant counts correctly"""
    response = client.get("/activities")
    activities = response.json()
    
    for name, activity in activities.items():
        assert len(activity["participants"]) <= activity["max_participants"]
        spots_left = activity["max_participants"] - len(activity["participants"])
        assert spots_left >= 0