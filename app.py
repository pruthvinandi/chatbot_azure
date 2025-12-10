from flask import Flask, render_template, request, jsonify
from openai import AzureOpenAI
import requests
import time

app = Flask(__name__)

# =============================
# === Azure ChatGPT Configuration ===
# =============================
CHAT_API_KEY = "1lkB8jubZ9GiYdVHiLXgPGBU3sFuKLLH8upi6mynvO9IUku8kZEjJQQJ99BJACYeBjFXJ3w3AAABACOGkn4D"
CHAT_ENDPOINT = "https://miniprojectmodel.openai.azure.com/"
CHAT_API_VERSION = "2023-05-15"
CHAT_DEPLOYMENT = "gpt-5-mini"

chat_client = AzureOpenAI(
    api_key=CHAT_API_KEY,
    azure_endpoint=CHAT_ENDPOINT,
    api_version=CHAT_API_VERSION
)

# =============================
# === Azure DALL·E Configuration ===
# =============================
DALLE_API_KEY = "3pb09WBabS6Ip0FmJOO1FF5pBkUdUWqPEYibH27wkmaqdbuyjF9HJQQJ99BJACfhMk5XJ3w3AAAAACOGlF3f"
DALLE_ENDPOINT = "https://pruth-mgqkvj16-swedencentral.cognitiveservices.azure.com/openai/deployments/dall-e-3/images/generations?api-version=2024-02-01"

# =============================
# === Azure Sora Video Configuration ===
# =============================
VIDEO_API_KEY = "3tqBs255GCQR9RinAAZL96fVj5DKE2vLaRXSpd7JikrT30qRuRSgJQQJ99BIACHYHv6XJ3w3AAAAACOGeYX8"
VIDEO_ENDPOINT = "https://pruth-mf5c0cr3-eastus2.cognitiveservices.azure.com"
VIDEO_API_VERSION = "preview"

# =============================
# === HOME ROUTE ===
# =============================
@app.route('/')
def home():
    return render_template("index.html")  # Serve index.html

# =============================
# === CHAT ROUTES ===
# =============================
@app.route('/chat')
def chat_page():
    return render_template("chat.html")  # Serve chat.html

@app.route('/chatbot', methods=['POST'])
def chatbot_response():
    user_message = request.json.get('message', '')
    try:
        response = chat_client.chat.completions.create(
            model=CHAT_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ]
        )
        reply = response.choices[0].message.content
        return jsonify({"response": reply})
    except Exception as e:
        return jsonify({"error": str(e)})

# =============================
# === IMAGE ROUTES ===
# =============================
@app.route('/dalle')
def dalle_page():
    return render_template("dalle.html")  # Serve dalle.html

@app.route('/generate-image', methods=['POST'])
def generate_image():
    prompt = request.json.get("prompt")
    headers = {"api-key": DALLE_API_KEY, "Content-Type": "application/json"}
    payload = {"prompt": prompt, "n": 1, "size": "1024x1024"}

    try:
        resp = requests.post(DALLE_ENDPOINT, headers=headers, json=payload)
        resp.raise_for_status()
        j = resp.json()
        image_url = j["data"][0]["url"]
        return jsonify({"image_url": image_url})
    except Exception as e:
        return jsonify({"error": str(e)})

# =============================
# === VIDEO ROUTES ===
# =============================
@app.route('/video')
def video_page():
    return render_template("sora_video.html")  # Serve sora_video.html

@app.route('/generate-video', methods=['POST'])
def generate_video():
    prompt = request.json.get("prompt")
    headers = {"api-key": VIDEO_API_KEY, "Content-Type": "application/json"}
    job_url = f"{VIDEO_ENDPOINT}/openai/v1/video/generations/jobs?api-version={VIDEO_API_VERSION}"
    body = {"model": "sora", "prompt": prompt, "width": 480, "height": 480, "n_seconds": 5, "n_variants": 1}

    try:
        create_resp = requests.post(job_url, headers=headers, json=body)
        create_resp.raise_for_status()
        job_id = create_resp.json().get("id")

        # Poll for status
        status_url = f"{VIDEO_ENDPOINT}/openai/v1/video/generations/jobs/{job_id}?api-version={VIDEO_API_VERSION}"
        for _ in range(30):
            time.sleep(2)
            status_resp = requests.get(status_url, headers=headers)
            status = status_resp.json().get("status")
            if status in ("succeeded", "failed", "cancelled"):
                break

        if status == "succeeded":
            gen_id = status_resp.json().get("generations")[0].get("id")
            return jsonify({"video_url": f"/video-content/{gen_id}"})
        else:
            return jsonify({"error": f"Video generation failed or pending. Status: {status}"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/video-content/<gen_id>')
def video_content(gen_id):
    headers = {"api-key": VIDEO_API_KEY}
    video_url = f"{VIDEO_ENDPOINT}/openai/v1/video/generations/{gen_id}/content/video?api-version={VIDEO_API_VERSION}"
    try:
        resp = requests.get(video_url, headers=headers, stream=True)
        resp.raise_for_status()
        return app.response_class(resp.iter_content(chunk_size=8192), content_type="video/mp4")
    except Exception as e:
        return jsonify({"error": str(e)})

# =============================
# === MAIN ===
# =============================
if __name__ == '__main__':
    app.run(debug=True)
