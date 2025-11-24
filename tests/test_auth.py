def test_login_logout(client, seed_data):
    # Login
    response = client.post("/auth/login", data={
        "email": "student@example.com",
        "password": "password"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Log out" in response.data  # ログイン後はログアウトボタンがあるはず

    # Logout
    response = client.get("/auth/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"Log In" in response.data

def test_login_invalid(client, seed_data):
    response = client.post("/auth/login", data={
        "email": "student@example.com",
        "password": "wrongpassword"
    }, follow_redirects=True)
    assert "メールまたはパスワードが違います" in response.data.decode("utf-8")
