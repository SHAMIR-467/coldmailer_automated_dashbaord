from app.main import app


def test_routes_registered():
    paths = {route.path for route in app.routes}
    assert "/api/jobs" in paths
    assert "/api/dashboard/stats" in paths
    assert "/api/jobs/{job_id}/cities" in paths
    assert "/api/settings/test-ollama" in paths


def test_health_route_shape():
    route = next(route for route in app.routes if route.path == "/health")
    assert "GET" in route.methods
