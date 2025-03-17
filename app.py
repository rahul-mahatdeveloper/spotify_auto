





from flask import Flask, request, jsonify
import requests
import time
from dotenv import load_dotenv
import os

app = Flask(__name__)

# Load environment variables
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_URL = "https://api.spotify.com/v1/search"

# 🔑 Cache for Spotify Token
token_cache = {
    "access_token": None,
    "expires_at": 0
}

# 🔑 **Spotify Token Generator with Caching**
def get_spotify_token():
    if token_cache["access_token"] and time.time() < token_cache["expires_at"]:
        return token_cache["access_token"]
    
    auth_response = requests.post(SPOTIFY_AUTH_URL, {
        "grant_type": "client_credentials",
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    })
    
    if auth_response.status_code != 200:
        return None
    
    auth_data = auth_response.json()
    
    if "access_token" not in auth_data:
        return None
    
    token_cache["access_token"] = auth_data["access_token"]
    token_cache["expires_at"] = time.time() + auth_data.get("expires_in", 3600)
    return token_cache["access_token"]

# 🎶 **Spotify Search Function (Internal Use)**
def fetch_spotify_tracks(query):
    """Spotify API se search result fetch karega."""
    if not query:
        return {"error": "Query parameter is required"}

    token = get_spotify_token()
    if not token:
        return {"error": "Failed to get Spotify token"}
    
    headers = {"Authorization": f"Bearer {token}"}
    search_url = f"{SPOTIFY_API_URL}?q={query}&type=track&limit=5"

    response = requests.get(search_url, headers=headers)
    if response.status_code != 200:
        return {"error": "Failed to fetch data from Spotify"}
    
    data = response.json()
    tracks = data.get("tracks", {}).get("items", [])
    filtered_tracks = [
        {
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "spotify_url": track["external_urls"]["spotify"]
        }
        for track in tracks
    ]

    return {"results": filtered_tracks}

# 📡 **Spotify Search API Endpoint**
@app.route("/spotify/search", methods=["GET"])
def search_spotify():
    query = request.args.get("query")
    response_data = fetch_spotify_tracks(query)
    return jsonify(response_data)

# 📡 **MCP Endpoint for AI Assistants**
@app.route("/mcp", methods=["POST"])
def mcp_endpoint():
    data = request.get_json(silent=True)  # ✅ Fix: get_json() ka use kiya hai
    if not data or "query" not in data:
        return jsonify({"error": "Query is required in request body"}), 400
    
    query = data["query"]
    spotify_response = fetch_spotify_tracks(query)
    
    if "error" in spotify_response:
        return jsonify({"status": "error", "message": spotify_response["error"]}), 500

    return jsonify({
        "status": "success",
        "message": f"Top songs for '{query}'",
        "results": spotify_response["results"]
    })

# 🚀 **Run Flask Server**
if __name__ == "__main__":
    app.run(debug=True, port=5000)
