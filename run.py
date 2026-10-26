import uvicorn
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:8500")

if __name__ == "__main__":
    print("=" * 65)
    print("🚀 SEO Command Center - Multi-Site Management & Autopilot Engine")
    print("🌐 Dashboard URL: http://127.0.0.1:8500")
    print("=" * 65)
    
    # Auto-open browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    uvicorn.run("app.main:app", host="127.0.0.1", port=8500, reload=True)
